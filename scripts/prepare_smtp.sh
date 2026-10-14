#!/usr/bin/env bash
# Preparation only: does not edit production .env, restart services or migrate DB.
set -Eeuo pipefail
umask 077
test "$(id -u)" -eq 0 || { echo '请使用 sudo bash 执行'; exit 1; }
cd /opt/ai-love-strategist
echo '===== 当前生产版本和健康 ====='
git rev-parse HEAD
git status --short --untracked-files=no
curl --noproxy '*' --fail --silent --show-error --max-time 15 http://127.0.0.1:18080/health/ready
echo
RUN=$(mktemp -d /var/tmp/test228-smtp.XXXXXXXX)
chmod 700 "$RUN"
export TEST228_SMTP_RUN="$RUN"
read -r -p 'SMTP 主机：' TEST228_SMTP_HOST </dev/tty
read -r -p 'SMTP 端口（465 或 587）：' TEST228_SMTP_PORT </dev/tty
case "$TEST228_SMTP_PORT" in 465|587) ;; *) echo '端口须为 465 或 587'; exit 1;; esac
read -r -p 'SMTP 登录账号：' TEST228_SMTP_USERNAME </dev/tty
read -r -s -p 'SMTP 授权码 / 密码（输入不显示）：' TEST228_SMTP_PASSWORD </dev/tty
printf '\n' >/dev/tty
read -r -p '发信邮箱地址：' TEST228_SMTP_SENDER </dev/tty
read -r -p '接收测试邮件的你自己的邮箱地址：' TEST228_SMTP_RECIPIENT </dev/tty
export TEST228_SMTP_HOST TEST228_SMTP_PORT TEST228_SMTP_USERNAME TEST228_SMTP_PASSWORD TEST228_SMTP_SENDER TEST228_SMTP_RECIPIENT
.venv/bin/python <<'PY'
import os,sys,json,secrets,smtplib,ssl
from pathlib import Path
from email.message import EmailMessage
host=os.environ['TEST228_SMTP_HOST'];port=int(os.environ['TEST228_SMTP_PORT'])
user=os.environ['TEST228_SMTP_USERNAME'];password=os.environ['TEST228_SMTP_PASSWORD']
sender=os.environ['TEST228_SMTP_SENDER'];recipient=os.environ['TEST228_SMTP_RECIPIENT']
if not all((host,user,password,sender,recipient)) or any('\r' in x or '\n' in x for x in (host,user,sender,recipient)):
    raise SystemExit('配置不完整或格式不正确')
msg=EmailMessage();msg['From']=sender;msg['To']=recipient;msg['Subject']='AI 恋爱军师 SMTP 配置测试'
msg.set_content('这是你在服务器主动发起的 SMTP 测试邮件。收到此邮件表示发信链路可用；账号升级尚未上线。')
try:
    context=ssl.create_default_context()
    smtp=smtplib.SMTP_SSL(host,port,timeout=15,context=context) if port==465 else smtplib.SMTP(host,port,timeout=15)
    with smtp:
        if port==587:smtp.ehlo();smtp.starttls(context=context);smtp.ehlo()
        smtp.login(user,password);smtp.send_message(msg)
except (OSError,smtplib.SMTPException):
    raise SystemExit('SMTP 测试失败，请核对服务商设置、端口和授权码；未修改生产配置。')
config=dict(SMTP_HOST=host,SMTP_PORT=str(port),SMTP_USERNAME=user,SMTP_PASSWORD=password,SMTP_SENDER=sender,
            SMTP_IMPLICIT_TLS='true' if port==465 else 'false',EMAIL_VERIFICATION_SECRET=secrets.token_hex(32),EMAIL_REGISTRATION_REQUIRED='true')
path=Path(os.environ['TEST228_SMTP_RUN'])/'smtp.env'
path.write_text('\n'.join(k+'='+json.dumps(v,ensure_ascii=False) for k,v in config.items())+'\n',encoding='utf-8')
path.chmod(0o600)
print('SMTP 服务接受测试邮件：PASS（还需检查收件箱或垃圾箱）')
print('私有配置文件：'+str(path))
print('未修改生产 .env，未执行数据库迁移或服务重启。')
PY
unset TEST228_SMTP_PASSWORD
echo 'TEST-228 SMTP PREPARATION: PASS'
