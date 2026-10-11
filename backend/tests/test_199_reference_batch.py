
import pytest

def upload(client, name):
    response = client.post('/api/v1/references', files={'file': (name, b'text', 'text/plain')})
    assert response.status_code == 201
    return response.json()['id']

def conversation(client):
    p = client.post('/api/v1/persons', json={'name': 'batch'}).json()
    return client.post('/api/v1/conversations', json={'person_id': p['id'], 'title': 'batch'}).json()['id']

def batch(client, ids, action, scope='global', conversation_id=None):
    return client.post('/api/v1/references/batch', json=dict(
        reference_ids=ids, action=action, scope=scope, conversation_id=conversation_id))

def test_mixed_batch_global_enable_disable_and_deduplication(client):
    ids = [upload(client, 'doc.md'), upload(client, 'SKILL.md')]
    assert batch(client, ids + ids, 'disable').json() == {'updated_count': 2}
    assert all(not x['enabled_by_default'] for x in client.get('/api/v1/references').json())
    assert batch(client, ids, 'enable').status_code == 200
    assert all(x['enabled_by_default'] for x in client.get('/api/v1/references').json())

def test_batch_conversation_isolation_priority_and_inherit(client):
    ids = [upload(client, 'doc.md'), upload(client, 'SKILL.md')]
    c1, c2 = conversation(client), conversation(client)
    assert client.put(f'/api/v1/conversations/{c1}/references/{ids[0]}',
        json={'enabled': True, 'priority': 7}).status_code == 200
    assert batch(client, ids, 'disable', 'conversation', c1).status_code == 200
    items = client.get('/api/v1/references', params={'conversation_id': c1}).json()
    assert all(not x['effective_enabled'] for x in items)
    assert next(x for x in items if x['id'] == ids[0])['override_priority'] == 7
    assert all(x['effective_enabled'] for x in client.get('/api/v1/references',
        params={'conversation_id': c2}).json())
    assert batch(client, ids, 'inherit', 'conversation', c1).status_code == 200
    assert all(x['override_enabled'] is None for x in client.get('/api/v1/references',
        params={'conversation_id': c1}).json())

@pytest.mark.parametrize('action', ['disable', 'delete'])
def test_batch_rejects_entire_selection_if_any_id_missing_or_foreign(client, action):
    own = upload(client, 'own.md')
    foreign = client.post('/api/v1/references',
        headers={'X-User-ID': '11111111-1111-1111-1111-111111111111'},
        files={'file': ('foreign.md', b'foreign', 'text/plain')}).json()['id']
    for invalid in ['missing', foreign]:
        assert batch(client, [own, invalid], action).status_code == 404
        items = client.get('/api/v1/references').json()
        assert len(items) == 1 and items[0]['id'] == own
        assert items[0]['enabled_by_default'] is True

def test_batch_delete_cascades_overrides_only_for_selected_items(client):
    ids = [upload(client, 'delete.md'), upload(client, 'keep.md')]
    c = conversation(client)
    assert batch(client, ids, 'disable', 'conversation', c).status_code == 200
    assert batch(client, ids[:1], 'delete').json() == {'updated_count': 1}
    remaining = client.get('/api/v1/references', params={'conversation_id': c}).json()
    assert len(remaining) == 1 and remaining[0]['id'] == ids[1]
    assert remaining[0]['override_enabled'] is False

def test_batch_invalid_scope_empty_and_foreign_conversation(client):
    own = upload(client, 'own.md')
    assert batch(client, [], 'disable').status_code == 422
    assert batch(client, [own], 'inherit').status_code == 422
    assert batch(client, [own], 'disable', 'conversation').status_code == 422
    c = conversation(client)
    response = client.post('/api/v1/references/batch',
        headers={'X-User-ID': '11111111-1111-1111-1111-111111111111'},
        json={'reference_ids': [own], 'action': 'disable', 'scope': 'conversation', 'conversation_id': c})
    assert response.status_code == 404
    assert client.get('/api/v1/references').json()[0]['enabled_by_default'] is True
