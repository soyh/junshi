#!/usr/bin/env bash
set -euo pipefail

PROJECT=/opt/ai-love-strategist
UNIT_SOURCE="$PROJECT/deploy/systemd"
UNIT_TARGET=/etc/systemd/system

if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "BLOCKED: install.sh must run as root" >&2
    exit 1
fi

required=(
    "$UNIT_SOURCE/ai-love-strategist.service"
    "$UNIT_SOURCE/ai-love-strategist-backup.service"
    "$UNIT_SOURCE/ai-love-strategist-backup.timer"
    "$PROJECT/.env"
    "$PROJECT/data/app.sqlite3"
)

for path in "${required[@]}"; do
    if [ ! -e "$path" ]; then
        echo "BLOCKED: required path missing: $path" >&2
        exit 1
    fi
done

install -m 0644 "$UNIT_SOURCE/ai-love-strategist.service" \
    "$UNIT_TARGET/ai-love-strategist.service"
install -m 0644 "$UNIT_SOURCE/ai-love-strategist-backup.service" \
    "$UNIT_TARGET/ai-love-strategist-backup.service"
install -m 0644 "$UNIT_SOURCE/ai-love-strategist-backup.timer" \
    "$UNIT_TARGET/ai-love-strategist-backup.timer"

chmod 0600 "$PROJECT/.env" "$PROJECT/data/app.sqlite3"

if [ -d "$PROJECT/data/backups" ]; then
    find "$PROJECT/data/backups" -maxdepth 1 -type f \
        \( -name '*.sqlite3' -o -name '*.manifest.json' \) \
        -exec chmod 0600 {} +
fi

systemctl daemon-reload
systemctl enable ai-love-strategist.service
systemctl enable ai-love-strategist-backup.timer

echo "systemd units installed and enabled"
echo "runtime service and backup timer were NOT started or restarted"
echo "activate them only after TEST-148 validation"
