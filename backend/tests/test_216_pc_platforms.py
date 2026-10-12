import hashlib
import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.config.settings import get_settings
from app.core.database import get_connection
from app.services.account_portability import export_account, import_account, seal, unseal

PASSWORD = 'synthetic-test-password-216'


def seed(client):
    person = client.post('/api/v1/persons', json={'name': 'Synthetic person'}).json()
    conversation = client.post('/api/v1/conversations', json={'person_id': person['id']}).json()
    return person, conversation


def test_multiple_platforms_same_person_and_isolation(client):
    person, conversation = seed(client)
    path = f'/api/v1/persons/{person["id"]}/platform-accounts'
    accounts = [client.post(path, json={'platform': p, 'account_handle': 'synthetic-id'}).json() for p in ('wechat', 'douyin')]
    assert len(client.get(path).json()) == 2
    assert client.get(path, headers={'X-User-ID': 'foreign'}).status_code == 404
    assert client.post(path, json={'platform': 'wechat', 'account_handle': 'synthetic-id'}).status_code == 409
    other, foreign_conversation = seed(client)
    source = f'/api/v1/conversations/{conversation["id"]}/platform-source'
    assert client.put(source, json={'account_id': accounts[0]['id']}).status_code == 200
    assert client.put(f'/api/v1/conversations/{foreign_conversation["id"]}/platform-source', json={'account_id': accounts[0]['id']}).status_code == 404
    assert client.delete(path + '/' + accounts[0]['id']).status_code == 409
    assert client.delete('/api/v1/persons/' + person['id']).status_code == 204
    with get_connection() as conn:
        assert conn.execute('SELECT COUNT(*) FROM conversation_platform_sources').fetchone()[0] == 0
        assert not conn.execute('PRAGMA foreign_key_check').fetchall()


def test_pc_messages_retry_is_idempotent_and_copy_has_no_write(client):
    person, conversation = seed(client)
    payload = {'operation_id': str(uuid4()), 'conversation_id': conversation['id'], 'sender_type': 'person',
               'content': 'synthetic latest message', 'sent_at': '2026-10-11T10:00:00+08:00'}
    first = client.post('/api/v1/pc/messages', json=payload)
    assert first.status_code == 200, first.text
    assert client.post('/api/v1/pc/messages', json=payload).json()['id'] == first.json()['id']
    assert client.post('/api/v1/pc/messages', json={**payload, 'content': 'changed'}).status_code == 409
    assert client.post('/api/v1/pc/messages', json=payload, headers={'X-User-ID': 'foreign'}).status_code == 404
    with get_connection() as conn:
        assert conn.execute('SELECT COUNT(*) FROM messages').fetchone()[0] == 1


def test_pc_media_retry_and_complete_encrypted_roundtrip(client, monkeypatch, tmp_path):
    monkeypatch.setenv('MEDIA_STORAGE_DIRECTORY', str(tmp_path / 'media'))
    get_settings.cache_clear()
    person, conversation = seed(client)
    account = client.post(f'/api/v1/persons/{person["id"]}/platform-accounts', json={'platform': 'wechat', 'account_handle': 'synthetic'}).json()
    client.put(f'/api/v1/conversations/{conversation["id"]}/platform-source', json={'account_id': account['id']})
    operation = str(uuid4())
    content = b'synthetic-media-for-storage-test'
    def upload():
        return client.post(f'/api/v1/pc/conversations/{conversation["id"]}/media', data={'operation_id': operation, 'sent_at': '2026-10-11T10:00:00+08:00'}, files={'file': ('test.png', content, 'image/png')})
    first = upload()
    assert first.status_code == 200, first.text
    assert upload().json()['id'] == first.json()['id']
    user = person['user_id']
    raw = export_account(user, PASSWORD)
    assert b'synthetic-media' not in raw and b'api_key' not in raw
    payload = unseal(raw, PASSWORD)
    assert 'user_credentials' not in payload['tables'] and 'user_llm_provider_profiles' not in payload['tables']
    with pytest.raises(ValueError): unseal(raw, 'wrong-password-216')
    with pytest.raises(ValueError, match='已有业务'): import_account(user, raw, PASSWORD)
    # Simulate a fresh target installation by removing source business rows first.
    assert client.delete('/api/v1/persons/' + person['id']).status_code == 204
    client.get('/api/v1/persons', headers={'X-User-ID': 'target'})
    assert import_account('target', raw, PASSWORD)['imported']
    with get_connection() as conn:
        row = conn.execute('SELECT * FROM media_attachments').fetchone()
        assert row['user_id'] == 'target'
        assert Path(row['storage_path']).read_bytes() == content
        assert conn.execute('SELECT user_id FROM conversation_platform_sources').fetchone()[0] == 'target'
        assert not conn.execute('PRAGMA foreign_key_check').fetchall()
    with pytest.raises(ValueError): import_account('target', raw, PASSWORD)


def test_archive_cannot_reference_other_users_rows_or_leave_partial_data(client, monkeypatch, tmp_path):
    monkeypatch.setenv('MEDIA_STORAGE_DIRECTORY', str(tmp_path / 'media')); get_settings.cache_clear()
    person, conversation = seed(client)
    payload = unseal(export_account(person['user_id'], PASSWORD), PASSWORD)
    payload['tables']['conversations'][0]['person_id'] = 'external-person'
    client.get('/api/v1/persons', headers={'X-User-ID': 'target'})
    with pytest.raises(ValueError, match='关联'): import_account('target', seal(payload, PASSWORD), PASSWORD)
    with get_connection() as conn:
        assert not conn.execute('SELECT 1 FROM persons WHERE user_id="target"').fetchone()
    assert client.get('/api/v1/persons/' + person['id']).status_code == 200


def test_portability_routes_require_auth_and_password(client):
    assert client.post('/api/v1/account-transfer/export', json={'password': PASSWORD}, headers={'Authorization': 'Bearer invalid'}).status_code == 401
    assert client.post('/api/v1/account-transfer/export', json={'password': 'short'}).status_code == 422


def test_new_migration_is_idempotent_and_retains_old_rows(client):
    person, conversation = seed(client)
    sql = (Path(__file__).parents[1] / 'migrations/021_platform_accounts.sql').read_text(encoding='utf8')
    with get_connection() as conn:
        before = [tuple(r) for r in conn.execute('SELECT * FROM persons')]
        conn.executescript(sql); conn.executescript(sql)
        assert before == [tuple(r) for r in conn.execute('SELECT * FROM persons')]


def test_upgrade_from_twenty_preserves_all_existing_tables(client):
    from app.core.migrations import run_migrations
    seed(client)
    with get_connection() as conn:
        for table in ('pc_ingest_receipts', 'conversation_platform_sources', 'person_platform_accounts'):
            conn.execute(f'DROP TABLE {table}')
        conn.execute("DELETE FROM schema_migrations WHERE version = '021'")
        tables = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'schema_migrations' ORDER BY name").fetchall()
        before = {name: (sql, [tuple(row) for row in conn.execute(f'SELECT * FROM "{name}" ORDER BY rowid')]) for name, sql in tables}
    run_migrations()
    run_migrations()
    with get_connection() as conn:
        for name, (sql, rows) in before.items():
            assert conn.execute('SELECT sql FROM sqlite_master WHERE name=?', (name,)).fetchone()[0] == sql
            assert [tuple(row) for row in conn.execute(f'SELECT * FROM "{name}" ORDER BY rowid')] == rows
        from pathlib import Path
        expected = {p.name.split('_', 1)[0] for p in (Path(__file__).parents[1] / 'migrations').glob('*.sql')}
        assert '021' in expected
        assert {row[0] for row in conn.execute('SELECT version FROM schema_migrations')} == expected
        assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert not conn.execute('PRAGMA foreign_key_check').fetchall()
