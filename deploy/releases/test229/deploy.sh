#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
APP=/opt/ai-love-strategist
BASE=f4ecbfd2315bfe50890891756076a40f3f524a42
SHA=0929710c97c4324c9816b481a7ebfec67700fc8d
BUNDLE_HASH=037ca06e27b817ec69f793e6c3a840bad8e0da7b813aec1c9b6ef2c36c751b5b
BUNDLE=${1:-/home/ubuntu/test229.bundle}
test "$(id -u)" -eq 0
test -f "$BUNDLE"
test -x "$APP/.venv/bin/python"
RUN=$(mktemp -d "$APP/data/test229-deploy.XXXXXXXX")
chmod 700 "$RUN"
exec > >(tee "$RUN/deploy.log") 2>&1
STOPPED=0; COMMITTED=0
DB="$APP/data/app.sqlite3"
export TEST229_RUN="$RUN" TEST229_APP="$APP"
restore_timers() {
  for unit in ai-love-strategist-backup.timer ai-love-strategist-watchdog.timer; do
    if grep -Fxq "$unit" "$RUN/active-timers"; then systemctl start "$unit" || return 1; fi
  done
}
ready() {
  local attempt
  for attempt in {1..30}; do
    if curl --noproxy '*' -fsS --connect-timeout 2 --max-time 3 http://127.0.0.1:18080/health/ready > "$RUN/health.json"; then
      if "$APP/.venv/bin/python" "$RUN/check-health.py" "$RUN/health.json"; then return 0; fi
    fi
    sleep 1
  done
  return 1
}
fail() {
  local rc=${1:-1}
  trap - ERR INT TERM
  set +e
  echo "===== TEST-229 上线未完成；退出码：$rc ====="
  journalctl -u ai-love-strategist.service -n 100 --no-pager > "$RUN/service-last.log" 2>&1
  if [ "$STOPPED" = 1 ] && [ "$COMMITTED" = 0 ]; then
    systemctl stop ai-love-strategist.service
    rollback_ok=1
    git -C "$APP" checkout --detach "$BASE" || rollback_ok=0
    if [ "$rollback_ok" = 1 ] && systemctl start ai-love-strategist.service && ready; then
      if restore_timers; then echo 'TEST-228 代码及健康回退：PASS'; else echo '代码已回退；定时任务恢复失败，请提供日志。'; fi
    else
      echo '自动回退未完成，请提供日志；项目可能保持停止。'
    fi
    echo '数据库未用备份覆盖；配置保持原样。'
  elif [ "$STOPPED" = 1 ]; then
    echo '新版已经完成页面验收，保留新版运行；请提供定时任务错误日志。'
  fi
  echo "部署日志：$RUN/deploy.log"
  echo "服务日志：$RUN/service-last.log"
  exit "$rc"
}
trap 'fail $?' ERR
trap 'fail 130' INT
trap 'fail 143' TERM
cat > "$RUN/check-health.py" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]))
assert r['status']=='ready' and r['database']['ok'] and r['migrations']['ok']
assert r['migrations']['expected_count']==23 and r['migrations']['applied_count']==23
PY
echo '===== TEST-229 / 01 生产基线 ====='
test "$(git -C "$APP" rev-parse HEAD)" = "$BASE"
test -z "$(git -C "$APP" status --porcelain --untracked-files=no)"
systemctl is-active --quiet ai-love-strategist.service
ready
cat "$RUN/health.json"; echo
sha256sum "$APP/.env" "$APP/backend/.env" > "$RUN/config.sha256"
: > "$RUN/active-timers"
for unit in ai-love-strategist-backup.timer ai-love-strategist-watchdog.timer; do
  if systemctl is-active --quiet "$unit"; then echo "$unit" >> "$RUN/active-timers"; fi
done
echo "部署目录：$RUN"
echo '===== TEST-229 / 02 离线候选及变更边界 ====='
cp -- "$BUNDLE" "$RUN/test229.bundle"
printf '%s  %s\n' "$BUNDLE_HASH" "$RUN/test229.bundle" | sha256sum -c -
git -C "$APP" bundle verify "$RUN/test229.bundle"
git -C "$APP" fetch "$RUN/test229.bundle" refs/heads/test-229-account-style-user-picker
test "$(git -C "$APP" rev-parse FETCH_HEAD)" = "$SHA"
git -C "$APP" merge-base --is-ancestor "$BASE" "$SHA"
test -z "$(git -C "$APP" diff --name-only "$BASE" "$SHA" -- backend/migrations backend/requirements.txt deploy/systemd backend/app/config)"
git clone --quiet --branch test-229-account-style-user-picker "$RUN/test229.bundle" "$RUN/repo"
test "$(git -C "$RUN/repo" rev-parse HEAD)" = "$SHA"
while IFS= read -r file; do
  if [ -e "$APP/$file" ] && ! git -C "$APP" ls-files --error-unmatch "$file" >/dev/null 2>&1; then
    echo "新增文件冲突：$file"; false
  fi
done < <(git -C "$APP" diff --diff-filter=A --name-only "$BASE" "$SHA")
mkdir "$RUN/tmp"
export TMPDIR="$RUN/tmp"
echo '===== TEST-229 / 03 服务器隔离专项 ====='
cd "$RUN/repo/backend"
APP_ENV=development EMAIL_REGISTRATION_REQUIRED=false "$APP/.venv/bin/python" -m pytest -q \
  tests/test_account_mail.py tests/test_email_challenge.py tests/test_account_identity.py \
  tests/test_email_account_api.py tests/test_account_admin_api.py tests/test_account_deletion.py tests/test_auth_account_login.py
echo '专项测试：PASS'
echo '===== TEST-229 / 04 服务器隔离全量 ====='
APP_ENV=development EMAIL_REGISTRATION_REQUIRED=false "$APP/.venv/bin/python" -m pytest -q | tee "$RUN/full-suite.log"
grep -Eq '1318 passed' "$RUN/full-suite.log"
echo '全量测试：PASS'
cd "$APP"
test "$(git rev-parse HEAD)" = "$BASE"
ready
sha256sum -c "$RUN/config.sha256"
"$APP/.venv/bin/python" <<'PY'
import os
from pathlib import Path
from app.config.settings import get_settings
s=get_settings()
assert Path(s.database_path).resolve()==Path(os.environ['TEST229_APP'])/'data/app.sqlite3'
assert s.email_registration_required
print('实际数据库路径及邮箱注册配置：PASS')
PY
echo '===== TEST-229 / 05 停服及最终备份 ====='
STOPPED=1
systemctl stop ai-love-strategist-backup.timer ai-love-strategist-watchdog.timer
systemctl stop ai-love-strategist-backup.service ai-love-strategist-watchdog.service ai-love-strategist-recovery.service ai-love-strategist.service
test "$(systemctl show ai-love-strategist.service -p ActiveState --value)" = inactive
"$APP/.venv/bin/python" -m app.backup --destination "$RUN/baseline.sqlite3"
"$APP/.venv/bin/python" -m app.backup --verify-manifest "$RUN/baseline.sqlite3"
"$APP/.venv/bin/python" - "$RUN/baseline.sqlite3" <<'PY'
import sqlite3,sys
from pathlib import Path
with sqlite3.connect(Path(sys.argv[1]).resolve().as_uri()+'?mode=ro',uri=True) as db:
    assert [r[0] for r in db.execute('SELECT version FROM schema_migrations ORDER BY version')]==[f'{n:03}' for n in range(1,24)]
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not db.execute('PRAGMA foreign_key_check').fetchall()
print('停服备份、001–023、完整性及外键：PASS')
PY
echo '===== TEST-229 / 06 切换精确代码并启动 ====='
git checkout --detach "$SHA"
sha256sum -c "$RUN/config.sha256"
"$APP/.venv/bin/python" -m app.preflight --backup-dir "$RUN" --json
systemctl start ai-love-strategist.service
ready
echo '===== TEST-229 / 07 HTTPS 页面及接口验收 ====='
curl --noproxy '*' --resolve 101.34.253.116:443:127.0.0.1 -fsS --max-time 15 https://101.34.253.116/app > "$RUN/page.html"
curl --noproxy '*' --resolve 101.34.253.116:443:127.0.0.1 -fsS --max-time 15 https://101.34.253.116/api/v1/auth/email/policy > "$RUN/policy.json"
"$APP/.venv/bin/python" - "$RUN" <<'PY'
import json,sys
from pathlib import Path
run=Path(sys.argv[1]);page=(run/'page.html').read_text()
for marker in ('email-user-table','email-user-search','email-users-prev','email-users-next','email-footer-link','email-admin-delete'):
    assert marker in page,marker
assert '<input id="email-admin-target"' not in page
policy=json.loads((run/'policy.json').read_text());assert policy['email_registration_required'] and policy['mail_available']
print('统一页面、用户表格、分页搜索及邮箱注册：PASS')
PY
for endpoint in auth/email/identity admin/accounts admin/accounts/directory; do
  status=$(curl --noproxy '*' --resolve 101.34.253.116:443:127.0.0.1 -sS --max-time 15 -o "$RUN/unauthorized.json" -w '%{http_code}' "https://101.34.253.116/api/v1/$endpoint")
  test "$status" = 401
done
echo '未登录接口保护：PASS'
sha256sum -c "$RUN/config.sha256"
COMMITTED=1
restore_timers
systemctl is-active --quiet ai-love-strategist.service
ready
echo '===== TEST-229 / 08 最终结果 ====='
echo 'TEST-229 PRODUCTION DEPLOYMENT: PASS'
echo "生产 SHA：$SHA"
echo '服务器专项及 1318 项全量：PASS'
echo 'HTTPS 页面及用户目录接口保护：PASS'
echo '数据库迁移：001–023，无新增迁移'
echo '原定时任务已恢复；未修改配置、SMTP、管理员权限、Nginx 或证书。'
echo '未连接或操作旧服务器及其 8899 服务。'
echo "停服备份：$RUN/baseline.sqlite3"
echo "完整日志：$RUN/deploy.log"
echo '访问地址：https://101.34.253.116/app'
echo '退出码：0'
