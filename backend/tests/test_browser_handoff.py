from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from app.core.database import get_connection
from app.services import browser_handoff


def setup_ticket(client):
    token = client.post('/api/v1/auth/register', json={
        'username': 'handoff-user', 'password': 'strong-password-1234'
    }).json()['access_token']
    headers = {'Authorization': 'Bearer ' + token}
    result = client.post('/api/v1/auth/browser-handoff', headers=headers)
    assert result.status_code == 200
    assert result.headers['cache-control'] == 'no-store'
    return token, headers, result.json()['ticket']


def exchange(client, ticket):
    return client.post('/api/v1/auth/browser-handoff/redeem', json={'ticket': ticket})


def test_single_use_and_account_isolation(client):
    token, headers, ticket = setup_ticket(client)
    person = client.post('/api/v1/persons', headers=headers, json={'name': 'Private person'}).json()
    assert client.get('/api/v1/persons', headers={'Authorization': 'Bearer ' + ticket}).status_code == 401
    with get_connection() as conn:
        assert conn.execute('SELECT ticket_hash FROM browser_handoffs').fetchone()[0] != ticket
    result = exchange(client, ticket)
    assert result.status_code == 200
    assert result.headers['cache-control'] == 'no-store'
    browser = result.json()['access_token']
    assert browser != token
    assert client.get('/api/v1/persons', headers={'Authorization': 'Bearer ' + browser}).json()[0]['id'] == person['id']
    assert exchange(client, ticket).status_code == 401
    assert client.get('/api/v1/persons', headers=headers).status_code == 200


def test_revoked_source_cannot_be_exchanged(client):
    _, headers, ticket = setup_ticket(client)
    client.delete('/api/v1/auth/session', headers=headers)
    assert exchange(client, ticket).status_code == 401


def test_expiry_and_replacement(client):
    token, headers, ticket = setup_ticket(client)
    replacement = client.post('/api/v1/auth/browser-handoff', headers=headers).json()['ticket']
    assert exchange(client, ticket).status_code == 401
    with get_connection() as conn:
        conn.execute('UPDATE browser_handoffs SET expires_at = ?',
                     ((datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),))
    assert exchange(client, replacement).status_code == 401


def test_issue_requires_real_session_even_in_development(client):
    assert client.post('/api/v1/auth/browser-handoff').status_code == 401
    assert client.post('/api/v1/auth/browser-handoff', headers={'Authorization': 'Bearer invalid'}).status_code == 401
    assert exchange(client, 'a' * 43).status_code == 401
    assert exchange(client, '\u4e2d' * 43).status_code == 422


def test_concurrent_redemption_only_one_wins(client):
    _, _, ticket = setup_ticket(client)
    def consume(_):
        try:
            with get_connection() as conn:
                browser_handoff.redeem(conn, ticket)
            return True
        except browser_handoff.InvalidHandoff:
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(consume, range(2))) == [False, True]
