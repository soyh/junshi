from app.services.reference_status import check_topics
from tests.test_197_reference_skills_context import _upload, _conversation, OTHER_USER_ID


def test_status_distinguishes_missing_disabled_ambiguous_and_empty():
    def row(id, name, enabled=True, content='', guide=False):
        return dict(id=id,name=name,original_filename=name,effective_enabled=enabled,
                    enabled_by_default=enabled,is_guide=guide,content=content)
    items=[row('g','指南.md',content='- 正常：`ok.md`\n- 停用：`off.md`\n- 缺失：`missing.md`\n- 歧义：`dup.md`\n- 未关联主题',guide=True),
           row('a','ok.md'),row('b','off.md',False),row('d1','dup.md'),row('d2','dup.md')]
    result=check_topics(items)
    assert [r['file_status'] for r in result['rows']]==['available','disabled','missing','ambiguous','unbound']
    assert result['effective_links']==1
    items[0]['effective_enabled']=False
    assert not any(r['effective'] for r in check_topics(items)['rows'])


def test_status_respects_owner_and_conversation_override(client):
    guide=_upload(client,'指南.md','- 接话：`聊天.md`\n- 不存在：`private.md`'.encode())
    doc=_upload(client,'聊天.md',b'body')
    foreign=_upload(client,'private.md',b'PRIVATE',headers={'X-User-ID':OTHER_USER_ID})
    assert client.patch('/api/v1/references/'+guide['id'],json={'is_guide':True}).status_code==200
    global_status=client.get('/api/v1/references/catalog').json()['retrieval']['topic_status']
    assert global_status['rows'][0]['effective']
    assert global_status['rows'][1]['file_status']=='missing'
    assert foreign['id'] not in str(global_status)
    convo=_conversation(client)
    assert client.put(f"/api/v1/conversations/{convo['id']}/references/{doc['id']}",json={'enabled':False}).status_code==200
    status=client.get(f"/api/v1/conversations/{convo['id']}/references/context").json()['retrieval']['topic_status']
    assert status['rows'][0]['file_status']=='disabled'
    assert status['rows'][0]['matches'][0]['override_enabled'] is False
    assert not status['rows'][0]['effective']
