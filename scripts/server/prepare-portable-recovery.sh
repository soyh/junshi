#!/usr/bin/env bash
set -euo pipefail

PROJECT=${PROJECT:-/opt/ai-love-strategist}
PY="$PROJECT/.venv/bin/python"
ENV_FILE="$PROJECT/.env"
EXPORT_DIR="$PROJECT/data/recovery_exports"
SERVICE=ai-love-strategist.service
BACKUP_TIMER=ai-love-strategist-backup.timer
WATCHDOG_TIMER=ai-love-strategist-watchdog.timer

if [ "$(id -u)" -ne 0 ]; then
    echo "TEST150_SERVER_PREP=FAILED"
    echo "reason=root-required"
    exit 1
fi

cd "$PROJECT"

if [ ! -x "$PY" ]; then
    echo "TEST150_SERVER_PREP=FAILED"
    echo "reason=venv-python-missing"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "TEST150_SERVER_PREP=FAILED"
    echo "reason=production-env-missing"
    exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
    echo "TEST150_SERVER_PREP=FAILED"
    echo "reason=repository-dirty"
    exit 1
fi

HEAD=$(git rev-parse HEAD)
PID_BEFORE=$(systemctl show "$SERVICE" --property=MainPID --value)
PORT8899_BEFORE=$(ss -ltnp 2>/dev/null | sed -n '/:8899 / s/.*pid=\([0-9][0-9]*\).*/\1/p' | head -n1 || true)

if [ -z "$PID_BEFORE" ] || [ "$PID_BEFORE" = "0" ]; then
    echo "TEST150_SERVER_PREP=FAILED"
    echo "reason=runtime-not-active"
    exit 1
fi

"$PY" -m app.probe live --json >/dev/null
"$PY" -m app.probe ready --json >/dev/null
"$PY" -m app.preflight --json >/dev/null

# Create one normal managed backup before changing the running code/config.
"$PY" -m app.backup >/dev/null

install -d -m 0700 "$EXPORT_DIR"

# Update only TEST-150 portable-recovery keys. The encryption key is generated
# inside Python and is never printed to stdout/stderr or stored in Git.
PROJECT_PATH="$PROJECT" "$PY" - <<'PY'
from __future__ import annotations

import base64
import os
import tempfile
from pathlib import Path

project = Path(os.environ["PROJECT_PATH"]).resolve()
env_path = project / ".env"
original = env_path.read_text(encoding="utf-8")
lines = original.splitlines()

values: dict[str, str] = {}
for line in lines:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    values[key.strip()] = value.strip()

if not values.get("PORTABLE_BACKUP_ENCRYPTION_KEY"):
    values["PORTABLE_BACKUP_ENCRYPTION_KEY"] = base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")

values["PORTABLE_BACKUP_DIRECTORY"] = str(project / "data" / "recovery_exports")
values["PORTABLE_BACKUP_KEEP"] = "7"

managed = {
    "PORTABLE_BACKUP_DIRECTORY",
    "PORTABLE_BACKUP_ENCRYPTION_KEY",
    "PORTABLE_BACKUP_KEEP",
}

output: list[str] = []
seen: set[str] = set()
for line in lines:
    if "=" in line and not line.lstrip().startswith("#"):
        key = line.split("=", 1)[0].strip()
        if key in managed:
            if key not in seen:
                output.append(f"{key}={values[key]}")
                seen.add(key)
            continue
    output.append(line)

if output and output[-1] != "":
    output.append("")
for key in ("PORTABLE_BACKUP_DIRECTORY", "PORTABLE_BACKUP_ENCRYPTION_KEY", "PORTABLE_BACKUP_KEEP"):
    if key not in seen:
        output.append(f"{key}={values[key]}")

payload = "\n".join(output).rstrip("\n") + "\n"
stat = env_path.stat()
fd, tmp_name = tempfile.mkstemp(prefix=".env.test150.", dir=project)
try:
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as target:
        target.write(payload)
        target.flush()
        os.fsync(target.fileno())
    os.chmod(tmp_name, 0o600)
    try:
        os.chown(tmp_name, stat.st_uid, stat.st_gid)
    except PermissionError:
        pass
    os.replace(tmp_name, env_path)
    directory_fd = os.open(project, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
finally:
    try:
        os.unlink(tmp_name)
    except FileNotFoundError:
        pass
PY

chmod 0600 "$ENV_FILE"

# Configuration must be usable before restarting the production runtime.
"$PY" -m app.portable_backup --check --json >/dev/null

# Focused portable-recovery regression on the real server.
"$PY" -m pytest -q backend/tests/test_portable_local_disaster_recovery.py >/dev/null

# Deliberate restart deploys the checked-out TEST-150 code. TEST-149's startup
# readiness gate makes restart fail if the app never reaches /ready.
systemctl restart "$SERVICE"

"$PY" -m app.probe live --json >/dev/null
"$PY" -m app.probe ready --json >/dev/null
"$PY" -m app.preflight --json >/dev/null

PREPARE_JSON=$("$PY" -m app.portable_backup --prepare --json)
BUNDLE=$(printf '%s' "$PREPARE_JSON" | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["bundle"])')
BUNDLE_SHA=$(printf '%s' "$PREPARE_JSON" | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["bundle_sha256"])')
"$PY" -m app.portable_backup --verify "$BUNDLE" --json >/dev/null

PID_AFTER=$(systemctl show "$SERVICE" --property=MainPID --value)
PORT8899_AFTER=$(ss -ltnp 2>/dev/null | sed -n '/:8899 / s/.*pid=\([0-9][0-9]*\).*/\1/p' | head -n1 || true)

if [ -z "$PID_AFTER" ] || [ "$PID_AFTER" = "0" ]; then
    echo "TEST150_SERVER_PREP=FAILED"
    echo "reason=runtime-missing-after-restart"
    exit 1
fi

if [ "$PORT8899_BEFORE" != "$PORT8899_AFTER" ]; then
    echo "TEST150_SERVER_PREP=FAILED"
    echo "reason=reserved-port-8899-owner-changed"
    exit 1
fi

if [ "$(systemctl is-active "$BACKUP_TIMER")" != "active" ]; then
    echo "TEST150_SERVER_PREP=FAILED"
    echo "reason=backup-timer-inactive"
    exit 1
fi

if [ "$(systemctl is-active "$WATCHDOG_TIMER")" != "active" ]; then
    echo "TEST150_SERVER_PREP=FAILED"
    echo "reason=watchdog-timer-inactive"
    exit 1
fi

if [ "$(stat -c '%a' "$ENV_FILE")" != "600" ]; then
    echo "TEST150_SERVER_PREP=FAILED"
    echo "reason=env-mode-regressed"
    exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
    echo "TEST150_SERVER_PREP=FAILED"
    echo "reason=repository-dirty-after-prep"
    exit 1
fi

echo "TEST150_SERVER_PREP=PASSED"
echo "SOURCE_HEAD=$HEAD"
echo "RUNTIME_PID=$PID_BEFORE->$PID_AFTER"
echo "BUNDLE_SHA256=$BUNDLE_SHA"
echo "PORT8899_PID=${PORT8899_AFTER:-0}"
echo "DATABASE_RESTORE_EXECUTED=NO"
