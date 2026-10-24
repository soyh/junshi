#!/usr/bin/env bash
# Deploy backend build 258 (WeChat aliases + chat intent) and publish the PC zip.
set -euo pipefail

KEY=/c/Users/12274/.ssh/id_ed25519
HOST=ubuntu@101.34.253.116
ROOT=/c/Users/12274/Documents/deepseek-harness/default-workspace/junshi-repo

cd "$ROOT/backend"
tar -czf /tmp/app258.tgz app migrations

scp -i "$KEY" -o BatchMode=yes /tmp/app258.tgz "$HOST:/tmp/app258.tgz"

ssh -i "$KEY" -o BatchMode=yes "$HOST" 'sudo bash -lc "
set -e
cd /opt/ai-love-strategist/backend
tar -xzf /tmp/app258.tgz
/opt/ai-love-strategist/.venv/bin/python -c \"from app.core.migrations import run_migrations; run_migrations()\"
systemctl restart ai-love-strategist
sleep 3
systemctl is-active ai-love-strategist
curl -s -o /dev/null -w \"profile=%{http_code}\n\" http://127.0.0.1:18080/api/v1/settings/profile
/opt/ai-love-strategist/.venv/bin/python - <<PY
import sqlite3
c = sqlite3.connect(\"/opt/ai-love-strategist/data/app.sqlite3\")
print([r[1] for r in c.execute(\"PRAGMA table_info(user_profiles)\")][-6:])
print([r[1] for r in c.execute(\"PRAGMA table_info(relationships)\")])
PY
"'

ssh -i "$KEY" -o BatchMode=yes "$HOST" 'sudo mv /tmp/junshi258.zip /var/www/junshi-downloads/JunshiPC-258-Windows-x64.zip && sudo chmod 644 /var/www/junshi-downloads/JunshiPC-258-Windows-x64.zip && ls -l /var/www/junshi-downloads/JunshiPC-258-Windows-x64.zip'
