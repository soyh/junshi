#!/usr/bin/env bash
# Deploy Build 257 backend: app/ + migrations/, then migrate and restart.
set -euo pipefail
cd "C:/Users/12274/Documents/deepseek-harness/default-workspace/junshi-repo"
KEY="C:/Users/12274/.ssh/id_ed25519"
HOST="ubuntu@101.34.253.116"

tar -czf /tmp/app257.tgz -C backend app migrations
ls -l /tmp/app257.tgz
scp -i "$KEY" -o BatchMode=yes /tmp/app257.tgz "$HOST:/tmp/app257.tgz"

ssh -i "$KEY" -o BatchMode=yes "$HOST" "sudo bash -lc 'cd /opt/ai-love-strategist/backend && tar -xzf /tmp/app257.tgz && /opt/ai-love-strategist/.venv/bin/python -c \"from app.core.migrations import run_migrations; run_migrations()\" && systemctl restart ai-love-strategist && sleep 4 && systemctl is-active ai-love-strategist'"

ssh -i "$KEY" -o BatchMode=yes "$HOST" "sudo bash -lc 'cd /opt/ai-love-strategist && .venv/bin/python -c \"
import sqlite3
conn = sqlite3.connect(\\\"data/app.sqlite3\\\")
cols = [r[1] for r in conn.execute(\\\"PRAGMA table_info(user_profiles)\\\")]
print(\\\"user_profiles.wechat_id\\\", \\\"wechat_id\\\" in cols)
print(\\\"user_profiles.contact_handoff_enabled\\\", \\\"contact_handoff_enabled\\\" in cols)
print(\\\"persons.wechat_id\\\", \\\"wechat_id\\\" in [r[1] for r in conn.execute(\\\"PRAGMA table_info(persons)\\\")])
\"'"

ssh -i "$KEY" -o BatchMode=yes "$HOST" "curl -s -o /dev/null -w 'profile=%{http_code}\n' http://127.0.0.1:18080/api/v1/settings/profile; curl -s -o /dev/null -w 'resolve=%{http_code}\n' -X POST -H 'content-type: application/json' -d '{\"platform\":\"xhs\",\"account_handle\":\"probe\"}' http://127.0.0.1:18080/api/v1/persons/resolve-channel"
