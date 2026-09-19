#!/usr/bin/env bash
set -euo pipefail

PROJECT=/opt/ai-love-strategist
PY="$PROJECT/.venv/bin/python"
UNIT_DIR=/etc/systemd/system
SERVICE=ai-love-strategist-offsite-backup.service
TIMER=ai-love-strategist-offsite-backup.timer

if [ "$(id -u)" -ne 0 ]; then
    echo "offsite installer requires root"
    exit 1
fi

cd "$PROJECT"

if [ ! -x "$PY" ]; then
    echo "project virtualenv python is missing"
    exit 1
fi

# Fail closed before installing/enabling anything. This validates that a verified
# local managed backup exists, the encryption key is valid, the destination is
# mounted and writable as a directory, and it is on storage distinct from the
# local managed backup.
"$PY" -m app.offsite_backup --check --json

install -m 0644 "$PROJECT/deploy/systemd/$SERVICE" "$UNIT_DIR/$SERVICE"
install -m 0644 "$PROJECT/deploy/systemd/$TIMER" "$UNIT_DIR/$TIMER"

systemctl daemon-reload
systemd-analyze verify "$UNIT_DIR/$SERVICE" "$UNIT_DIR/$TIMER"

# Enabling this timer must not restart or otherwise mutate the application
# runtime. It schedules only the independent offsite backup oneshot.
systemctl enable "$TIMER"

echo "offsite backup units installed"
echo "timer enabled but not started automatically"
echo "start explicitly with: systemctl start $TIMER"
