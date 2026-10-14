from unittest.mock import MagicMock, patch
import smtplib
import pytest
from app.services.account_mail import MailSettings, VerificationMailer, normalize_email


@pytest.mark.parametrize('value', ['a@example.com\r\nBcc: other@example.com', 'not-mail', 'a@', 'a b@example.com'])
def test_rejects_invalid_and_header_injection(value):
    with pytest.raises(ValueError): normalize_email(value)


def test_starttls_precedes_credentials():
    cfg = MailSettings('smtp.example.com', 587, 'user', 'secret', 'sender@example.com', False)
    smtp = MagicMock()
    with patch('app.services.account_mail.smtplib.SMTP') as factory:
        factory.return_value.__enter__.return_value = smtp
        VerificationMailer(cfg).send('receiver@example.com', '123456')
    assert [c[0] for c in smtp.method_calls] == ['ehlo', 'starttls', 'ehlo', 'login', 'send_message']


def test_transport_error_does_not_expose_credentials():
    cfg = MailSettings('smtp.example.com', 465, 'user', 'secret', 'sender@example.com')
    with patch('app.services.account_mail.smtplib.SMTP_SSL', side_effect=smtplib.SMTPException('secret')):
        with pytest.raises(ValueError, match='验证码邮件发送失败') as error:
            VerificationMailer(cfg).send('receiver@example.com', '123456')
    assert 'secret' not in str(error.value)
