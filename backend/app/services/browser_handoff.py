"""One-use browser login grants, never usable as API bearer sessions."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.services.auth_session import AuthSessionService


def digest(ticket):
    return hashlib.sha256(ticket.encode('ascii')).hexdigest()


class InvalidHandoff(ValueError):
    pass


def issue(conn, token, now=None):
    now = now or datetime.now(timezone.utc)
    conn.execute('BEGIN IMMEDIATE')
    session = AuthSessionService().get_active_session(conn, token, now=now)
    if session is None:
        raise InvalidHandoff('请重新登录客户端。')
    expiry = min(now + timedelta(seconds=60), datetime.fromisoformat(session.expires_at))
    ticket = secrets.token_urlsafe(32)
    conn.execute('DELETE FROM browser_handoffs WHERE expires_at <= ? OR session_id = ?',
                 (now.isoformat(), session.id))
    conn.execute('INSERT INTO browser_handoffs VALUES (?, ?, ?)',
                 (digest(ticket), session.id, expiry.isoformat()))
    return {'ticket': ticket, 'expires_at': expiry.isoformat()}


def redeem(conn, ticket, now=None):
    now = now or datetime.now(timezone.utc)
    conn.execute('BEGIN IMMEDIATE')
    row = conn.execute('''SELECT h.expires_at AS ticket_expiry, s.*
        FROM browser_handoffs h JOIN auth_sessions s ON s.id = h.session_id
        WHERE h.ticket_hash = ?''', (digest(ticket),)).fetchone()
    if (row is None or row['revoked_at'] is not None
            or datetime.fromisoformat(row['ticket_expiry']) <= now
            or datetime.fromisoformat(row['expires_at']) <= now):
        raise InvalidHandoff('登录衔接已失效，请回到客户端重新点击打开主页面。')
    conn.execute('DELETE FROM browser_handoffs WHERE ticket_hash = ?', (digest(ticket),))
    return AuthSessionService().create(conn, row['user_id'], now=now)
