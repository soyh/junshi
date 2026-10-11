from pathlib import Path
import pytest
from app.config.settings import get_settings
from app.core.database import get_connection
from app.services.llm import LLMAnalysisError
from app.services.llm_provider_config import LLMProviderConfigService
from app.services.vision_llm_provider import LLMVisionProviderService
from app.services.qwen_provider import QwenProvider
from tests.test_179_vision_model_routing import _enable_llm_encryption, _profile


def test_unconfigured_account_never_inherits_server_or_other_user_key(client, monkeypatch):
    _enable_llm_encryption(monkeypatch)
    monkeypatch.setenv('DASHSCOPE_API_KEY', 'server-secret')
    get_settings.cache_clear()
    _profile(client, name='Owner', model='test', api_key='owner-secret', activate=True)
    with get_connection() as conn:
        owner = LLMProviderConfigService().build_provider(conn, get_settings().local_user_id)
        assert owner.api_key == 'owner-secret'
        for service in (LLMProviderConfigService(), LLMVisionProviderService()):
            provider = service.build_provider(conn, 'other-account')
            assert provider.api_key is None
            with pytest.raises(LLMAnalysisError, match='not configured'):
                provider.test_connection()
    assert QwenProvider().api_key is None
    get_settings.cache_clear()


def seed(client, monkeypatch, tmp_path):
    monkeypatch.setenv('MEDIA_STORAGE_DIRECTORY', str(tmp_path / 'media'))
    get_settings.cache_clear()
    person = client.post('/api/v1/persons', json={'name': 'Delete me'}).json()
    conversation = client.post('/api/v1/conversations', json={'person_id': person['id']}).json()
    result = client.post(f"/api/v1/conversations/{conversation['id']}/media", files={'file': ('test.png', b'fake-test-image', 'image/png')})
    assert result.status_code == 201, result.text
    with get_connection() as conn:
        path = Path(conn.execute('SELECT storage_path FROM media_attachments WHERE id=?', (result.json()['id'],)).fetchone()[0])
        conn.execute('INSERT INTO action_plan_snapshots(id,user_id,person_id,recommendation_id,recommendation_json,action_plan_json,evidence_json) VALUES(?,?,?,?,?,?,?)', ('snap', person['user_id'], person['id'], 'rec', '{}', '{}', '{}'))
        conn.execute('INSERT INTO person_memories(person_id,user_id,updated_at) VALUES(?,?,CURRENT_TIMESTAMP)', (person['id'],person['user_id']))
    return person, conversation, path


def test_person_delete_removes_snapshots_memory_conversations_and_media(client, monkeypatch, tmp_path):
    person, conversation, path = seed(client,monkeypatch,tmp_path)
    other = client.post('/api/v1/persons', json={'name':'Keep me'}).json()
    assert client.delete('/api/v1/persons/'+person['id'], headers={'X-User-ID':'other-account'}).status_code == 404
    assert path.exists()
    assert client.delete('/api/v1/persons/'+person['id']).status_code == 204
    assert not path.exists()
    with get_connection() as conn:
        for table in ('conversations','media_attachments','person_memories','action_plan_snapshots'):
            assert conn.execute(f'SELECT COUNT(*) FROM {table} WHERE person_id=?',(person['id'],)).fetchone()[0] == 0
        assert not conn.execute('PRAGMA foreign_key_check').fetchall()
    assert client.get('/api/v1/persons/'+other['id']).status_code == 200


def test_failed_blob_cleanup_is_reported_and_owner_can_retry(client, monkeypatch, tmp_path):
    person, _, path = seed(client,monkeypatch,tmp_path)
    original = Path.unlink
    def fail(self, *args, **kwargs):
        if self == path: raise PermissionError('test lock')
        return original(self,*args,**kwargs)
    monkeypatch.setattr(Path,'unlink',fail)
    assert client.delete('/api/v1/persons/'+person['id']).status_code == 503
    assert path.exists()
    monkeypatch.setattr(Path,'unlink',original)
    assert client.delete('/api/v1/persons/'+person['id'],headers={'X-User-ID':'other-account'}).status_code == 404
    assert client.delete('/api/v1/persons/'+person['id']).status_code == 204
    assert not path.exists()


def test_person_delete_refuses_outside_storage_path(client, monkeypatch, tmp_path):
    person, _, path = seed(client,monkeypatch,tmp_path)
    outside = tmp_path / 'outside.txt'
    outside.write_text('must survive')
    with get_connection() as conn:
        conn.execute('UPDATE media_attachments SET storage_path=? WHERE person_id=?', (str(outside), person['id']))
    assert client.delete('/api/v1/persons/'+person['id']).status_code == 503
    assert client.get('/api/v1/persons/'+person['id']).status_code == 200
    assert outside.read_text() == 'must survive'
    assert path.exists()
