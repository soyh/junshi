#!/usr/bin/env bash
set -euo pipefail
cd "C:/Users/12274/Documents/deepseek-harness/default-workspace/junshi-repo"
tar -czf /tmp/app251.tgz -C backend app migrations
scp -o BatchMode=yes -i "C:/Users/12274/.ssh/junshi_ed25519" /tmp/app251.tgz ubuntu@101.34.253.116:/tmp/app251.tgz
ssh -o BatchMode=yes -i "C:/Users/12274/.ssh/junshi_ed25519" ubuntu@101.34.253.116 'sudo bash -s' <<'EOF'
set -euo pipefail
cd /opt/ai-love-strategist/backend
tar -xzf /tmp/app251.tgz
/opt/ai-love-strategist/.venv/bin/python -c "from app.core.migrations import run_migrations; run_migrations()"
systemctl restart ai-love-strategist
sleep 4
systemctl is-active ai-love-strategist
curl -s -o /dev/null -w 'profile=%{http_code}\n' http://127.0.0.1:18080/api/v1/settings/profile
curl -s http://127.0.0.1:18080/app | grep -c '军师判断' || true
EOF
