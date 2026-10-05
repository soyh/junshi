from tests.test_197_reference_skills_context import _conversation, _upload, OTHER_USER_ID


def test_create_and_edit_global_guide_without_any_conversation(client):
    doc = _upload(client, "冲突.md", "道歉与补救".encode())
    created = client.post('/api/v1/references/guide', json={
        'name': '全局主题指南', 'content': '# 导读\n- 冲突与修复：`冲突.md`',
    })
    assert created.status_code == 201
    assert created.headers['cache-control'] == 'no-store'
    guide = created.json()
    catalog = client.get('/api/v1/references/catalog')
    assert catalog.status_code == 200
    assert catalog.json()['conversation_id'] is None
    assert catalog.json()['retrieval']['guide_count'] == 1
    assert catalog.json()['retrieval']['query'] == ''
    assert 'candidates' not in catalog.json()
    entry = next(x for x in catalog.json()['catalog'] if x['reference_id'] == doc['id'])
    assert '冲突与修复' in entry['topics']
    listed = next(x for x in client.get('/api/v1/references').json() if x['id'] == guide['id'])
    assert listed['enabled_by_default'] is True
    assert listed['original_filename'] == '全局主题指南.md'
    assert client.put(f"/api/v1/references/{guide['id']}/content", json={
        'content': '# 新导读\n- 修复：`冲突.md`', 'expected_revision': guide['revision'],
    }).status_code == 200
    assert client.get('/api/v1/references/catalog').json()['retrieval']['guide_count'] == 1


def test_global_catalog_does_not_inherit_conversation_overrides_or_foreign_files(client):
    convo = _conversation(client)
    global_doc = _upload(client, 'global.md', b'GLOBAL')
    local_doc = _upload(client, 'local.md', b'LOCAL', enabled=False)
    _upload(client, 'foreign.md', b'FOREIGN', headers={'X-User-ID': OTHER_USER_ID})
    for doc, enabled in [(global_doc, False), (local_doc, True)]:
        assert client.put(f"/api/v1/conversations/{convo['id']}/references/{doc['id']}",
                          json={'enabled': enabled}).status_code == 200
    global_catalog = client.get('/api/v1/references/catalog').json()
    local_catalog = client.get(f"/api/v1/conversations/{convo['id']}/references/context").json()
    assert [x['reference_id'] for x in global_catalog['catalog']] == [global_doc['id']]
    assert [x['reference_id'] for x in local_catalog['catalog']] == [local_doc['id']]


def test_global_guide_applies_to_new_and_existing_conversations(client):
    old = _conversation(client)
    guide = client.post('/api/v1/references/guide', json={'name': '导读.md', 'content': '# 通用规则'}).json()
    new = _conversation(client)
    for convo in [old, new]:
        items = client.get(f"/api/v1/conversations/{convo['id']}/references/context").json()['items']
        assert guide['id'] in [x['reference_id'] for x in items]


def test_invalid_guide_creation_does_not_create_placeholder(client):
    for payload in [ {'name': '  ', 'content': 'x'}, {'name': '../guide', 'content': 'x'},
                     {'name': 'guide.md', 'content': ' \n'}, {'name': 'guide.md', 'content': '中' * 180000} ]:
        assert client.post('/api/v1/references/guide', json=payload).status_code == 422
    assert client.get('/api/v1/references').json() == []
