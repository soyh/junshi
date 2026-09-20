#!/usr/bin/env bash
set -euo pipefail

REPOSITORY="https://github.com/soyh/junshi.git"
SOURCE_HEAD=""
PROJECT="/opt/ai-love-strategist"
BUNDLE=""
ENV_FILE=""
APPLY=0
INSTALL_PACKAGES=1
SERVICE="ai-love-strategist.service"
BACKUP_TIMER="ai-love-strategist-backup.timer"
WATCHDOG_TIMER="ai-love-strategist-watchdog.timer"

fail() {
    echo "REPLACEMENT_RECOVERY=FAILED"
    echo "reason=$1"
    exit 1
}

usage() {
    cat <<'EOF'
Usage:
  bootstrap-replacement-server.sh \
    --source-head <git-sha> \
    --bundle <encrypted-recovery-bundle> \
    [--repository <git-url>] \
    [--project <path>] \
    [--env-file <production-env-file>] \
    [--apply] \
    [--no-install-packages]

Without --apply the script bootstraps only code + Python dependencies and stages
an encrypted recovery bundle. It never installs a production .env or restores DB.

--apply requires --env-file and is intended only for a replacement server that
has no active ai-love-strategist.service.
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --repository)
            REPOSITORY=${2:?missing repository}
            shift 2
            ;;
        --source-head)
            SOURCE_HEAD=${2:?missing source head}
            shift 2
            ;;
        --project)
            PROJECT=${2:?missing project}
            shift 2
            ;;
        --bundle)
            BUNDLE=${2:?missing bundle}
            shift 2
            ;;
        --env-file)
            ENV_FILE=${2:?missing env file}
            shift 2
            ;;
        --apply)
            APPLY=1
            shift
            ;;
        --no-install-packages)
            INSTALL_PACKAGES=0
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            fail "unknown-argument:$1"
            ;;
    esac
done

[ "$(id -u)" -eq 0 ] || fail "root-required"
[ -n "$SOURCE_HEAD" ] || fail "source-head-required"
[ -f "$BUNDLE" ] || fail "bundle-missing"

if [ "$APPLY" -eq 1 ] && [ ! -f "$ENV_FILE" ]; then
    fail "production-env-required-for-apply"
fi

if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet "$SERVICE"; then
    fail "target-has-active-production-runtime"
fi

port8899_pid() {
    if ! command -v ss >/dev/null 2>&1; then
        printf '0\n'
        return
    fi
    ss -ltnp 2>/dev/null \
        | sed -n '/:8899 / s/.*pid=\([0-9][0-9]*\).*/\1/p' \
        | head -n1
}

select_python() {
    local candidate
    for candidate in python3.13 python3.12 python3.11 python3; do
        if ! command -v "$candidate" >/dev/null 2>&1; then
            continue
        fi
        if "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
        then
            command -v "$candidate"
            return 0
        fi
    done
    return 1
}

install_system_packages() {
    if [ "$INSTALL_PACKAGES" -ne 1 ]; then
        return 1
    fi

    if command -v dnf >/dev/null 2>&1; then
        dnf install -y git iproute >/dev/null
        if ! dnf install -y python3.11 python3.11-pip >/dev/null 2>&1; then
            dnf install -y python3 python3-pip >/dev/null
        fi
        return 0
    fi

    if command -v apt-get >/dev/null 2>&1; then
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -y >/dev/null
        apt-get install -y git iproute2 python3 python3-venv python3-pip >/dev/null
        return 0
    fi

    return 1
}

PYBASE=$(select_python || true)
if ! command -v git >/dev/null 2>&1 || [ -z "$PYBASE" ] || ! command -v ss >/dev/null 2>&1; then
    install_system_packages || fail "required-system-packages-missing"
    PYBASE=$(select_python || true)
fi

command -v git >/dev/null 2>&1 || fail "git-missing"
command -v systemctl >/dev/null 2>&1 || fail "systemd-missing"
command -v ss >/dev/null 2>&1 || fail "ss-missing"
[ -n "$PYBASE" ] || fail "python-3.11-or-newer-required"

PORT8899_BEFORE=$(port8899_pid)
PORT8899_BEFORE=${PORT8899_BEFORE:-0}

PARENT=$(dirname "$PROJECT")
install -d -m 0755 "$PARENT"

if [ -e "$PROJECT" ] && [ ! -d "$PROJECT/.git" ]; then
    if [ -n "$(find "$PROJECT" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null || true)" ]; then
        fail "project-path-exists-but-is-not-a-git-checkout"
    fi
fi

if [ ! -d "$PROJECT/.git" ]; then
    rm -rf "$PROJECT"
    git clone "$REPOSITORY" "$PROJECT" >/dev/null
fi

cd "$PROJECT"

if [ -n "$(git status --porcelain)" ]; then
    fail "project-checkout-dirty"
fi

git remote set-url origin "$REPOSITORY"
git fetch --tags --prune origin >/dev/null
if ! git cat-file -e "${SOURCE_HEAD}^{commit}" 2>/dev/null; then
    git fetch origin "$SOURCE_HEAD" >/dev/null 2>&1 || fail "source-head-not-fetchable"
fi

git checkout --detach "$SOURCE_HEAD" >/dev/null
[ "$(git rev-parse HEAD)" = "$SOURCE_HEAD" ] || fail "source-head-checkout-mismatch"
[ -z "$(git status --porcelain)" ] || fail "project-checkout-dirty-after-checkout"

if [ ! -x "$PROJECT/.venv/bin/python" ]; then
    if ! "$PYBASE" -m venv "$PROJECT/.venv" >/dev/null 2>&1; then
        if command -v apt-get >/dev/null 2>&1 && [ "$INSTALL_PACKAGES" -eq 1 ]; then
            apt-get install -y python3-venv >/dev/null
            "$PYBASE" -m venv "$PROJECT/.venv" >/dev/null 2>&1 || fail "python-venv-create-failed"
        else
            fail "python-venv-create-failed"
        fi
    fi
fi

PY="$PROJECT/.venv/bin/python"
"$PY" -m pip install --disable-pip-version-check -q -r "$PROJECT/backend/requirements.txt"

install -d -m 0700 "$PROJECT/data"
install -d -m 0700 "$PROJECT/data/recovery-incoming"

STAGED_BUNDLE="$PROJECT/data/recovery-incoming/$(basename "$BUNDLE")"
install -m 0600 "$BUNDLE" "$STAGED_BUNDLE"

if [ "$APPLY" -ne 1 ]; then
    PORT8899_AFTER=$(port8899_pid)
    PORT8899_AFTER=${PORT8899_AFTER:-0}
    [ "$PORT8899_BEFORE" = "$PORT8899_AFTER" ] || fail "reserved-port-8899-owner-changed"

    echo "REPLACEMENT_BOOTSTRAP=STAGED"
    echo "SOURCE_HEAD=$SOURCE_HEAD"
    echo "PROJECT=$PROJECT"
    echo "REMOTE_BUNDLE=$STAGED_BUNDLE"
    echo "ENV_TRANSFERRED=NO"
    echo "DATABASE_RESTORE_EXECUTED=NO"
    echo "PORT8899_PID=$PORT8899_AFTER"
    exit 0
fi

install -m 0600 "$ENV_FILE" "$PROJECT/.env"
rm -f "$ENV_FILE"

cd "$PROJECT"

"$PY" -m app.portable_backup --verify "$STAGED_BUNDLE" --json >/dev/null

EXTRACT_DIR="$PROJECT/data/recovery-incoming/extracted"
rm -rf "$EXTRACT_DIR"
install -d -m 0700 "$EXTRACT_DIR"

EXTRACT_JSON=$("$PY" -m app.portable_backup \
    --extract "$STAGED_BUNDLE" \
    --destination-dir "$EXTRACT_DIR" \
    --json)
BACKUP=$(printf '%s' "$EXTRACT_JSON" | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["backup"])')
MANIFEST=$(printf '%s' "$EXTRACT_JSON" | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["manifest"])')

"$PY" -m app.backup --verify-manifest "$MANIFEST" >/dev/null

if systemctl is-active --quiet "$SERVICE"; then
    fail "target-became-active-before-restore"
fi

"$PY" -m app.restore \
    --backup "$BACKUP" \
    --destination "$PROJECT/data/app.sqlite3" \
    --offline-confirmed >/dev/null
chmod 0600 "$PROJECT/.env" "$PROJECT/data/app.sqlite3"

# Create a fresh local managed backup from the restored DB before preflight.
"$PY" -m app.backup >/dev/null
"$PY" -m app.preflight --json >/dev/null

bash "$PROJECT/deploy/systemd/install.sh" >/dev/null
systemctl start "$SERVICE"
"$PY" -m app.probe live --json >/dev/null
"$PY" -m app.probe ready --json >/dev/null
"$PY" -m app.preflight --json >/dev/null
systemctl start "$BACKUP_TIMER"
systemctl start "$WATCHDOG_TIMER"

[ "$(systemctl is-active "$SERVICE")" = "active" ] || fail "runtime-not-active-after-restore"
[ "$(systemctl is-active "$BACKUP_TIMER")" = "active" ] || fail "backup-timer-not-active-after-restore"
[ "$(systemctl is-active "$WATCHDOG_TIMER")" = "active" ] || fail "watchdog-timer-not-active-after-restore"

PORT8899_AFTER=$(port8899_pid)
PORT8899_AFTER=${PORT8899_AFTER:-0}
[ "$PORT8899_BEFORE" = "$PORT8899_AFTER" ] || fail "reserved-port-8899-owner-changed"

PID_AFTER=$(systemctl show "$SERVICE" --property=MainPID --value)
[ -n "$PID_AFTER" ] && [ "$PID_AFTER" != "0" ] || fail "runtime-mainpid-missing"

rm -rf "$EXTRACT_DIR"

echo "REPLACEMENT_RECOVERY=PASSED"
echo "SOURCE_HEAD=$SOURCE_HEAD"
echo "PROJECT=$PROJECT"
echo "RUNTIME_PID=$PID_AFTER"
echo "PORT8899_PID=$PORT8899_AFTER"
echo "DATABASE_RESTORE_EXECUTED=YES"
