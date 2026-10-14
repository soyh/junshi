#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
APP=/opt/ai-love-strategist
BASE=a7842b28510ae7495174e727f962622cbc0b3d90
SHA=f4ecbfd2315bfe50890891756076a40f3f524a42
BUNDLE_HASH=6064cac128689b8f9dcf7a81218fdc0ec724ff04fdb88647e77758bca90c7bc4
BUNDLE=${1:-/home/ubuntu/test228.bundle}
MAIL_CONFIG=${2:?需要 SMTP 私有配置路径}
ACCEPTANCE=${3:?需要已通过验收的隔离目录}
test "$(id -u)" -eq 0
test -f "$BUNDLE" && test -f "$MAIL_CONFIG"
test -x "$APP/.venv/bin/python"
RUN=$(mktemp -d "$APP/data/test228-deploy.XXXXXXXX")
chmod 700 "$RUN"
exec > >(tee "$RUN/deploy.log") 2>&1
export TEST228_APP="$APP" TEST228_RUN="$RUN" TEST228_MAIL_CONFIG="$MAIL_CONFIG"
STOPPED=0; BACKED_UP=0; START_ATTEMPTED=0; COMMITTED=0
DB="$APP/data/app.sqlite3"
restore_timers() {
  for unit in ai-love-strategist-backup.timer ai-love-strategist-watchdog.timer; do
    if grep -qx "$unit" "$RUN/active-timers"; then systemctl start "$unit"; fi
  done
}
cat > "$RUN/fingerprint.py" <<'PY'
import sqlite3,sys,hashlib
from pathlib import Path
with sqlite3.connect(Path(sys.argv[1]).resolve().as_uri()+'?mode=ro',uri=True) as db:
    values=[]
    for name,sql in db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        quoted='"'+name.replace('"','""')+'"'
        rows=sorted(repr(tuple(row)) for row in db.execute('SELECT * FROM '+quoted))
        values.append((name,sql,rows))
    print(hashlib.sha256(repr(values).encode()).hexdigest())
PY
fail() {
  rc=$?; trap - ERR; set +e
  echo "===== 上线失败处理；退出码：$rc ====="
  systemctl status ai-love-strategist.service --no-pager > "$RUN/service-status.log" 2>&1
  journalctl -u ai-love-strategist.service -n 100 --no-pager > "$RUN/service-last.log" 2>&1
  if [ "$STOPPED" = 1 ] && [ "$COMMITTED" = 0 ]; then
    systemctl stop ai-love-strategist.service
    safe=1
    if [ "$START_ATTEMPTED" = 1 ]; then
      safe=0
      "$APP/.venv/bin/python" "$RUN/fingerprint.py" "$DB" > "$RUN/current.fingerprint"
      if cmp -s "$RUN/post.fingerprint" "$RUN/current.fingerprint"; then safe=1; fi
    fi
    if [ "$safe" = 1 ]; then
      rollback_ok=1
      cd "$APP"
      if [ "$BACKED_UP" = 1 ]; then
        "$APP/.venv/bin/python" -m app.restore --backup "$RUN/baseline.sqlite3" --destination "$DB" --offline-confirmed || rollback_ok=0
      fi
      git checkout --detach "$BASE" || rollback_ok=0
      cp -p "$RUN/root.env" "$APP/.env" || rollback_ok=0
      cp -p "$RUN/backend.env" "$APP/backend/.env" || rollback_ok=0
      if [ "$rollback_ok" = 1 ] && systemctl start ai-love-strategist.service; then
        restore_timers
        echo 'TEST-219 自动回退：PASS'
      else
        echo '自动回退未完成：请保留日志，服务可能处于停止状态。'
      fi
    else
      echo '启动后发现数据变更，未用备份覆盖新数据；保留 TEST-228 代码和数据库，服务保持停止。'
    fi
  elif [ "$STOPPED" = 0 ] || [ "$COMMITTED" = 1 ]; then
    if [ -f "$RUN/active-timers" ]; then restore_timers; fi
  fi
  echo "部署目录：$RUN"
  echo "部署日志：$RUN/deploy.log"
  echo "服务日志：$RUN/service-last.log"
  exit "$rc"
}
trap fail ERR
echo '===== TEST-228 / 01 当前生产与隔离记录 ====='
test "$(git -C "$APP" rev-parse HEAD)" = "$BASE"
test -z "$(git -C "$APP" status --porcelain --untracked-files=no)"
systemctl is-active --quiet ai-love-strategist.service
grep -Fxq 'TEST-228 ISOLATED ACCEPTANCE: PASS' "$ACCEPTANCE/acceptance.log"
grep -Fxq "候选 SHA：$SHA" "$ACCEPTANCE/acceptance.log"
grep -Eq '1317 passed' "$ACCEPTANCE/acceptance.log"
"$APP/.venv/bin/python" - "$ACCEPTANCE/migration-result.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]));assert r['status']=='PASS' and r['migration']=='022 -> 023' and r['idempotent']
PY
curl --noproxy '*' -fsS --max-time 15 http://127.0.0.1:18080/health/ready > "$RUN/health.before.json"
curl --noproxy '*' --resolve 101.34.253.116:443:127.0.0.1 -fsS --max-time 15 https://101.34.253.116/app > "$RUN/page.before.html"
"$APP/.venv/bin/python" - "$RUN/health.before.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]));assert r['status']=='ready' and r['migrations']['applied_count']==22 and r['migrations']['expected_count']==22
PY
echo '===== TEST-228 / 02 固定代码与配置 ====='
cp -- "$BUNDLE" "$RUN/test228.bundle"
printf '%s  %s\n' "$BUNDLE_HASH" "$RUN/test228.bundle" | sha256sum -c -
git -C "$APP" fetch "$RUN/test228.bundle" refs/heads/test-228-email-account-management
test "$(git -C "$APP" rev-parse FETCH_HEAD)" = "$SHA"
git -C "$APP" merge-base --is-ancestor "$BASE" "$SHA"
test -z "$(git -C "$APP" diff --name-only "$BASE" "$SHA" -- backend/requirements.txt deploy/systemd backend/migrations/0{01,02,03,04,05,06,07,08,09,10,11,12,13,14,15,16,17,18,19,20,21,22}_\*)"
while IFS= read -r file; do
  if [ -e "$APP/$file" ] && ! git -C "$APP" ls-files --error-unmatch "$file" >/dev/null 2>&1; then
    echo '新增文件与本地文件冲突，停止部署。'; false
  fi
done < <(git -C "$APP" diff --diff-filter=A --name-only "$BASE" "$SHA")
cp -p "$APP/.env" "$RUN/root.env"
cp -p "$APP/backend/.env" "$RUN/backend.env"
cp "$MAIL_CONFIG" "$RUN/smtp.env"
chmod 600 "$RUN/smtp.env"
cd "$APP"
ACTUAL_DB=$("$APP/.venv/bin/python" -c 'from app.config.settings import get_settings; from pathlib import Path; print(Path(get_settings().database_path).resolve())')
test "$ACTUAL_DB" = "$DB"
read -r -p '输入你现有的软件登录账号（不是 SMTP 邮箱）：' ADMIN_USERNAME </dev/tty
export TEST228_ADMIN_USERNAME="$ADMIN_USERNAME"
"$APP/.venv/bin/python" <<'PY'
import os,sqlite3,stat
from pathlib import Path
from dotenv import dotenv_values
from app.config.settings import get_settings
with sqlite3.connect(Path(get_settings().database_path).resolve().as_uri()+'?mode=ro',uri=True) as c:
    assert c.execute('SELECT 1 FROM user_credentials WHERE username=?',(os.environ['TEST228_ADMIN_USERNAME'].strip().lower(),)).fetchone(),'软件账号不存在'
path=Path(os.environ['TEST228_MAIL_CONFIG']);info=path.stat()
assert info.st_uid==0 and not stat.S_IMODE(info.st_mode)&0o077,'SMTP 原文件权限不正确'
cfg=dotenv_values(Path(os.environ['TEST228_RUN'])/'smtp.env')
assert all(cfg.get(k) for k in ('SMTP_HOST','SMTP_PORT','SMTP_USERNAME','SMTP_PASSWORD','SMTP_SENDER','SMTP_IMPLICIT_TLS','EMAIL_VERIFICATION_SECRET'))
assert len(cfg['EMAIL_VERIFICATION_SECRET'])>=32
print('软件账号及 SMTP 配置检查：PASS')
PY
: > "$RUN/active-timers"
for unit in ai-love-strategist-backup.timer ai-love-strategist-watchdog.timer; do
  if systemctl is-active --quiet "$unit"; then echo "$unit" >> "$RUN/active-timers"; fi
done
echo '===== TEST-228 / 03 暂停项目与最终备份 ====='
STOPPED=1
systemctl stop ai-love-strategist-backup.timer ai-love-strategist-watchdog.timer
systemctl stop ai-love-strategist-backup.service ai-love-strategist-watchdog.service ai-love-strategist-recovery.service ai-love-strategist.service
if systemctl is-active --quiet ai-love-strategist.service; then echo '停服未完成'; false; fi
"$APP/.venv/bin/python" -m app.backup --destination "$RUN/baseline.sqlite3"
"$APP/.venv/bin/python" -m app.backup --verify-manifest "$RUN/baseline.sqlite3"
BACKED_UP=1
echo '===== TEST-228 / 04 切换候选与 023 迁移 ====='
git checkout --detach "$SHA"
"$APP/.venv/bin/python" -c 'from app.core.migrations import run_migrations; run_migrations()'
"$APP/.venv/bin/python" <<'PY'
import os,sqlite3
from pathlib import Path
run=Path(os.environ['TEST228_RUN']);target=Path(os.environ['TEST228_APP'])/'data/app.sqlite3'
with sqlite3.connect((run/'baseline.sqlite3').as_uri()+'?mode=ro',uri=True) as old,sqlite3.connect(target.as_uri()+'?mode=ro',uri=True) as new:
    tables=[r[0] for r in old.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name<>'schema_migrations'")]
    for name in tables:
        quoted='"'+name.replace('"','""')+'"'
        for pragma in ('table_info','foreign_key_list'):
            assert old.execute(f'PRAGMA {pragma}({quoted})').fetchall()==new.execute(f'PRAGMA {pragma}({quoted})').fetchall()
        assert sorted(repr(tuple(r)) for r in old.execute('SELECT * FROM '+quoted))==sorted(repr(tuple(r)) for r in new.execute('SELECT * FROM '+quoted))
    assert [r[0] for r in new.execute('SELECT version FROM schema_migrations ORDER BY version')]==[f'{i:03}' for i in range(1,24)]
    assert new.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not new.execute('PRAGMA foreign_key_check').fetchall()
print('023 迁移、原有表结构及数据、完整性与外键：PASS')
PY
echo '===== TEST-228 / 05 SMTP 配置与管理员初始化 ====='
"$APP/.venv/bin/python" <<'PY'
import os
from pathlib import Path
from dotenv import dotenv_values,set_key
app=Path(os.environ['TEST228_APP']);cfg=dotenv_values(Path(os.environ['TEST228_RUN'])/'smtp.env')
keys=('SMTP_HOST','SMTP_PORT','SMTP_USERNAME','SMTP_PASSWORD','SMTP_SENDER','SMTP_IMPLICIT_TLS','EMAIL_VERIFICATION_SECRET','EMAIL_REGISTRATION_REQUIRED')
cfg['EMAIL_REGISTRATION_REQUIRED']='true'
for path in (app/'.env',app/'backend/.env'):
    before=dotenv_values(path)
    for key in keys:set_key(str(path),key,cfg[key],quote_mode='always')
    path.chmod(0o600);after=dotenv_values(path)
    assert {k:v for k,v in before.items() if k not in keys}=={k:v for k,v in after.items() if k not in keys}
    assert all(after[k]==cfg[k] for k in keys)
print('SMTP 配置已保存；原有模型密钥和其他配置保持一致：PASS')
PY
"$APP/.venv/bin/python" scripts/account_admin.py --grant-admin="$ADMIN_USERNAME"
"$APP/.venv/bin/python" "$RUN/fingerprint.py" "$DB" > "$RUN/post.fingerprint"
"$APP/.venv/bin/python" -m app.backup --destination "$RUN/post-migration.sqlite3"
"$APP/.venv/bin/python" -m app.preflight --backup-dir "$RUN" --json
echo '===== TEST-228 / 06 启动与上线验收 ====='
START_ATTEMPTED=1
systemctl start ai-love-strategist.service
curl --noproxy '*' -fsS --max-time 15 http://127.0.0.1:18080/health/ready > "$RUN/health.after.json"
curl --noproxy '*' --resolve 101.34.253.116:443:127.0.0.1 -fsS --max-time 15 https://101.34.253.116/app > "$RUN/page.after.html"
curl --noproxy '*' --resolve 101.34.253.116:443:127.0.0.1 -fsS --max-time 15 https://101.34.253.116/api/v1/auth/email/policy > "$RUN/policy.json"
"$APP/.venv/bin/python" - "$RUN" <<'PY'
import json,sys
from pathlib import Path
run=Path(sys.argv[1]);health=json.loads((run/'health.after.json').read_text())
assert health['status']=='ready' and health['migrations']['expected_count']==23 and health['migrations']['applied_count']==23
policy=json.loads((run/'policy.json').read_text());assert policy['email_registration_required'] and policy['mail_available']
page=(run/'page.after.html').read_text()
for marker in ('email-account-center','email-admin-panel','email-admin-delete','email-send-code'):assert marker in page
print('HTTPS 页面、001–023、强制邮箱注册及 SMTP 配置：PASS')
PY
for endpoint in auth/email/identity admin/accounts; do
  status=$(curl --noproxy '*' --resolve 101.34.253.116:443:127.0.0.1 -sS --max-time 15 -o "$RUN/unauthorized.json" -w '%{http_code}' "https://101.34.253.116/api/v1/$endpoint")
  test "$status" = 401
done
COMMITTED=1
restore_timers
echo '===== TEST-228 / 07 最终结果 ====='
echo 'TEST-228 PRODUCTION DEPLOYMENT: PASS'
echo "生产 SHA：$SHA"
echo '数据库迁移：001–023；原有业务数据及结构核对通过。'
echo '邮箱验证注册已启用；管理员权限已授予输入的软件账号。'
echo '原定时任务已恢复；未修改 Nginx、证书或旧服务器 8899。'
echo '访问地址：https://101.34.253.116/app'
echo "停服备份：$RUN/baseline.sqlite3"
echo "部署日志：$RUN/deploy.log"
echo '退出码：0'
