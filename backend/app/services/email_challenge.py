"""Caller must commit failed verification attempts as well as successful results."""
import hashlib
import hmac
import secrets
import time
import uuid
from app.services.account_mail import normalize_email


class EmailChallengeError(ValueError):
    pass


class EmailChallengeService:
    def __init__(self, secret: str, mailer, clock=time.time):
        if len(secret) < 32:
            raise ValueError('验证码签名密钥必须至少 32 个字符')
        self.secret, self.mailer, self.clock = secret.encode(), mailer, clock

    def digest(self, value):
        return hmac.new(self.secret, value.encode(), hashlib.sha256).hexdigest()

    def send(self, conn, email, purpose, requester, user_id=None):
        email = normalize_email(email)
        if purpose not in ('register','bind','reset','delete'):
            raise EmailChallengeError('验证码用途不正确')
        now = int(self.clock())
        requester_hash = self.digest(requester)
        # Serialize rate checks with inserts, including requests from other workers.
        conn.execute('BEGIN IMMEDIATE')
        recent = conn.execute('SELECT MAX(created_at) FROM email_challenges WHERE email=?', (email,)).fetchone()[0]
        count = conn.execute('SELECT COUNT(*) FROM email_challenges WHERE created_at>? AND email=?', (now-3600,email)).fetchone()[0]
        requester_count = conn.execute('SELECT COUNT(*) FROM email_challenges WHERE created_at>? AND requester_hash=?', (now-3600,requester_hash)).fetchone()[0]
        if (recent is not None and now-recent < 60) or count >= 10 or requester_count >= 60:
            raise EmailChallengeError('验证码发送过于频繁，请稍后重试')
        identifier = str(uuid.uuid4())
        code = f'{secrets.randbelow(1000000):06d}'
        conn.execute('INSERT INTO email_challenges(id,email,purpose,requester_hash,user_id,code_hash,created_at,expires_at,consumed) VALUES(?,?,?,?,?,?,?,?,1)',
                     (identifier,email,purpose,requester_hash,user_id,self.digest(identifier+':'+code),now,now+600))
        # Reserve the rate-limit slot before SMTP, without holding the application
        # database write lock during network I/O. Failed sends remain inactive.
        conn.commit()
        self.mailer.send(email, code)
        conn.execute('BEGIN IMMEDIATE')
        conn.execute('UPDATE email_challenges SET consumed=0 WHERE id=?',(identifier,))
        # Only a delivered new code invalidates earlier codes of the same scope.
        conn.execute('UPDATE email_challenges SET consumed=1 WHERE email=? AND purpose=? AND user_id IS ? AND id<>?', (email,purpose,user_id,identifier))
        return identifier

    def consume(self, conn, identifier, email, purpose, code, user_id=None):
        email = normalize_email(email)
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute('SELECT * FROM email_challenges WHERE id=?', (identifier,)).fetchone()
        if row is None or row['email'] != email or row['purpose'] != purpose or row['user_id'] != user_id:
            return False
        if row['consumed'] or row['attempts'] >= 5 or row['expires_at'] <= int(self.clock()):
            return False
        conn.execute('UPDATE email_challenges SET attempts=attempts+1 WHERE id=?', (identifier,))
        if not hmac.compare_digest(row['code_hash'], self.digest(identifier+':'+code)):
            return False
        conn.execute('UPDATE email_challenges SET consumed=1 WHERE id=?', (identifier,))
        return True
