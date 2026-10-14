"""TLS-only verification mail transport. Credentials and codes are never logged."""
import re
import smtplib
import ssl
from dataclasses import dataclass, field
from email.message import EmailMessage


def normalize_email(value: str) -> str:
    value = value.strip()
    if len(value) > 254 or not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}", value):
        raise ValueError('请填写有效的邮箱地址')
    return value.lower()


@dataclass(frozen=True)
class MailSettings:
    host: str
    port: int
    username: str
    password: str = field(repr=False)
    sender: str
    implicit_tls: bool = True


class VerificationMailer:
    def __init__(self, settings: MailSettings):
        self.settings = settings

    def send(self, recipient: str, code: str):
        recipient = normalize_email(recipient)
        if not re.fullmatch(r'[0-9]{6}', code):
            raise ValueError('Invalid verification code')
        cfg = self.settings
        if not cfg.host or not cfg.username or not cfg.password:
            raise ValueError('邮件服务尚未配置')
        message = EmailMessage()
        message['From'] = normalize_email(cfg.sender)
        message['To'] = recipient
        message['Subject'] = 'AI 恋爱军师 · 邮箱验证码'
        message.set_content(f'你的验证码为：{code}\n有效期 10 分钟。请勿向他人提供验证码。\n如非本人操作，请忽略此邮件。')
        context = ssl.create_default_context()
        try:
            if cfg.implicit_tls:
                transport = smtplib.SMTP_SSL(cfg.host, cfg.port, timeout=15, context=context)
            else:
                transport = smtplib.SMTP(cfg.host, cfg.port, timeout=15)
            with transport as smtp:
                if not cfg.implicit_tls:
                    smtp.ehlo()
                    smtp.starttls(context=context)
                    smtp.ehlo()
                smtp.login(cfg.username, cfg.password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException):
            raise ValueError('验证码邮件发送失败，请稍后重试') from None
