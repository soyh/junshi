#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
APP=/opt/ai-love-strategist
BASE=a7842b28510ae7495174e727f962622cbc0b3d90
SHA=f4ecbfd2315bfe50890891756076a40f3f524a42
BUNDLE_HASH=6064cac128689b8f9dcf7a81218fdc0ec724ff04fdb88647e77758bca90c7bc4
BUNDLE=${1:-/home/ubuntu/test228.bundle}
MAIL_CONFIG=${2:?请提供 SMTP 准备生成的私有配置文件路径}
test "$(id -u)" -eq 0
test -f "$BUNDLE"
test -f "$MAIL_CONFIG"
test -x "$APP/.venv/bin/python"
RUN=$(mktemp -d /var/tmp/test228-isolated.XXXXXXXX)
chmod 700 "$RUN"
exec > >(tee "$RUN/acceptance.log") 2>&1
trap 'rc=$?; echo "验收失败，退出码：$rc；日志：$RUN/acceptance.log"; exit "$rc"' ERR
echo '===== TEST-228 / 01 生产基线 ====='
test "$(git -C "$APP" rev-parse HEAD)" = "$BASE"
test -z "$(git -C "$APP" status --porcelain --untracked-files=no)"
systemctl is-active --quiet ai-love-strategist.service
for unit in ai-love-strategist.service ai-love-strategist-backup.timer ai-love-strategist-watchdog.timer; do
  systemctl show "$unit" -p ActiveState -p UnitFileState -p MainPID >> "$RUN/services.before"
done
curl --noproxy '*' -fsS --max-time 15 http://127.0.0.1:18080/health/ready > "$RUN/health.before.json"
echo '===== TEST-228 / 02 离线候选版本 ====='
cp -- "$BUNDLE" "$RUN/test228.bundle"
printf '%s  %s\n' "$BUNDLE_HASH" "$RUN/test228.bundle" | sha256sum -c -
git clone --quiet "$RUN/test228.bundle" "$RUN/repo"
test "$(git -C "$RUN/repo" rev-parse HEAD)" = "$SHA"
test -z "$(git -C "$RUN/repo" status --porcelain --untracked-files=no)"
for file in backend/requirements.txt backend/app/config/launcher.py; do
  if git -C "$APP" cat-file -e "$BASE:$file" 2>/dev/null; then
    git -C "$APP" show "$BASE:$file" > "$RUN/original"
    cmp "$RUN/original" "$RUN/repo/$file"
  fi
done
for file in "$APP"/backend/migrations/*.sql; do
  cmp "$file" "$RUN/repo/backend/migrations/$(basename "$file")"
done
mkdir -p "$RUN/tmp"
export TEST228_RUN="$RUN" TEST228_APP="$APP" TEST228_MAIL_CONFIG="$MAIL_CONFIG"
export TMPDIR="$RUN/tmp"
echo '===== TEST-228 / 03 服务器专项 ====='
cd "$RUN/repo/backend"
APP_ENV=development EMAIL_REGISTRATION_REQUIRED=false "$APP/.venv/bin/python" -m pytest -q \
  tests/test_account_mail.py tests/test_email_challenge.py tests/test_account_identity.py \
  tests/test_email_account_api.py tests/test_account_admin_api.py tests/test_account_deletion.py \
  tests/test_auth_account_login.py
echo '===== TEST-228 / 04 服务器全量 ====='
APP_ENV=development EMAIL_REGISTRATION_REQUIRED=false "$APP/.venv/bin/python" -m pytest -q
echo '===== TEST-228 / 05 只读生产副本与 023 演练 ====='
cd "$APP/backend"
"$APP/.venv/bin/python" <<'PY'
import os,sqlite3,json
from pathlib import Path
from app.config.settings import get_settings
run=Path(os.environ['TEST228_RUN'])
source=Path(get_settings().database_path).resolve()
with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(run/'rehearsal.sqlite3') as dst:
    src.backup(dst)
with sqlite3.connect(run/'rehearsal.sqlite3') as db:
    assert [r[0] for r in db.execute('SELECT version FROM schema_migrations ORDER BY version')]==[f'{i:03}' for i in range(1,23)]
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not db.execute('PRAGMA foreign_key_check').fetchall()
print('生产只读一致性副本、001–022、完整性及外键：PASS')
PY
cd "$RUN/repo/backend"
"$APP/.venv/bin/python" <<'PY'
import os,sqlite3,hashlib,json
from pathlib import Path
run=Path(os.environ['TEST228_RUN']);path=run/'rehearsal.sqlite3'
db=sqlite3.connect(path)
names=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name<>'schema_migrations' ORDER BY name")]
def fingerprint():
    result={}
    for name in names:
        quoted='"'+name.replace('"','""')+'"'
        schema=(db.execute(f'PRAGMA table_info({quoted})').fetchall(),db.execute(f'PRAGMA foreign_key_list({quoted})').fetchall())
        rows=sorted(repr(tuple(r)) for r in db.execute('SELECT * FROM '+quoted))
        result[name]=hashlib.sha256(repr((schema,rows)).encode()).hexdigest()
    return result
before=fingerprint()
sql=(run/'repo/backend/migrations/023_account_identity.sql').read_text(encoding='utf-8')
db.execute('PRAGMA foreign_keys=ON');db.executescript(sql)
assert fingerprint()==before
db.executescript(sql);assert fingerprint()==before
db.execute("INSERT INTO schema_migrations(version) VALUES('023')");db.commit()
assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
assert not db.execute('PRAGMA foreign_key_check').fetchall()
result={'status':'PASS','migration':'022 -> 023','existing_tables_unchanged':len(names),'idempotent':True}
(run/'migration-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
PY
echo '===== TEST-228 / 06 真实 SMTP 与隔离注册闭环 ====='
DATABASE_PATH="$RUN/mail-smoke.sqlite3" LOG_DIR="$RUN/mail-logs" MEDIA_STORAGE_DIRECTORY="$RUN/mail-media" \
  APP_ENV=production APP_DEBUG=false "$APP/.venv/bin/python" <<'PY'
import os,stat,uuid
from pathlib import Path
from dotenv import dotenv_values
config=Path(os.environ['TEST228_MAIL_CONFIG'])
info=config.stat()
assert info.st_uid==0 and not (stat.S_IMODE(info.st_mode)&0o077),'SMTP 配置文件权限不正确'
values=dotenv_values(config)
keys=('SMTP_HOST','SMTP_PORT','SMTP_USERNAME','SMTP_PASSWORD','SMTP_SENDER','SMTP_IMPLICIT_TLS','EMAIL_VERIFICATION_SECRET','EMAIL_REGISTRATION_REQUIRED')
assert all(values.get(k) for k in keys),'SMTP 配置不完整'
os.environ.update({k:values[k] for k in keys})
os.environ['EMAIL_REGISTRATION_REQUIRED']='true'
from app.config.settings import get_settings
get_settings.cache_clear()
from app.main import app
from app.api.routes import account_identity as routes
from app.services.email_challenge import EmailChallengeService
from fastapi.testclient import TestClient
real=routes.challenge_service();captured=[]
class ObservedMailer:
    def send(self,email,code):
        real.mailer.send(email,code)
        captured.append(code)
routes.challenge_service=lambda:EmailChallengeService(values['EMAIL_VERIFICATION_SECRET'],ObservedMailer())
with TestClient(app) as client:
    name='smtp_test_'+uuid.uuid4().hex[:12]
    password=uuid.uuid4().hex
    assert client.post('/api/v1/auth/register',json={'username':name,'password':password}).status_code==400
    email=values['SMTP_SENDER']
    response=client.post('/api/v1/auth/email/code',json={'email':email,'purpose':'register'})
    assert response.status_code==200,'真实 SMTP 验证码发送失败'
    assert len(captured)==1
    registered=client.post('/api/v1/auth/email/register',json={'username':name,'password':password,'email':email,'code':captured[0],'challenge_id':response.json()['challenge_id']})
    assert registered.status_code==201,'隔离邮箱注册失败'
    token=registered.json()['access_token']
    identity=client.get('/api/v1/auth/email/identity',headers={'Authorization':'Bearer '+token})
    assert identity.status_code==200 and identity.json()['email']==email
    assert client.get('/api/v1/admin/accounts',headers={'Authorization':'Bearer '+token}).status_code==403
    captured.clear()
print('真实 SMTP、强制邮箱注册、绑定身份及管理员边界：PASS（仅隔离数据库）')
PY
echo '===== TEST-228 / 07 复核生产 ====='
test "$(git -C "$APP" rev-parse HEAD)" = "$BASE"
test -z "$(git -C "$APP" status --porcelain --untracked-files=no)"
for unit in ai-love-strategist.service ai-love-strategist-backup.timer ai-love-strategist-watchdog.timer; do
  systemctl show "$unit" -p ActiveState -p UnitFileState -p MainPID >> "$RUN/services.after"
done
cmp "$RUN/services.before" "$RUN/services.after"
curl --noproxy '*' -fsS --max-time 15 http://127.0.0.1:18080/health/ready > "$RUN/health.after.json"
"$APP/.venv/bin/python" - "$RUN/health.before.json" "$RUN/health.after.json" <<'PY'
import json,sys
for path in sys.argv[1:]:
    data=json.load(open(path))
    assert data['status']=='ready' and data['migrations']['expected_count']==22 and data['migrations']['applied_count']==22
print('生产代码、服务及 001–022 健康状态：PASS')
PY
echo 'TEST-228 ISOLATED ACCEPTANCE: PASS'
echo "候选 SHA：$SHA"
echo '未切换生产代码、未迁移生产数据库、未重启服务。'
echo '未修改生产配置、Nginx、证书或旧服务器 8899。'
echo "隔离目录：$RUN"
echo "完整日志：$RUN/acceptance.log"
echo '退出码：0'
