from copy import deepcopy
import pytest

from app.core.database import get_connection
from app.services import person_memory as memory
from app.services.analysis import AnalysisService
from app.services.text_import_parser import parse_text, validate_candidates
from tests.test_197_reference_skills_context import _conversation, LOCAL_USER_ID
from tests.test_strategic_reply import create_relationship


class MemoryProvider:
    def __init__(self):
        self.calls = []

    def summarize_person(self, context):
        self.calls.append(deepcopy(context))
        return {'description':'双方持续聊天，保留此前约定。','facts':['对方喜欢晚间聊天'],
                'constraints':['不要替用户承诺见面'],'unknowns':['尚未确认恋爱关系'],
                'relationship_status':'互动积极','relationship_stage':'熟悉',
                'reason':'对方在本批记录主动发起聊天，更新互动状态；关系仍未确认。',
                'evidence_source_ids':[context['messages'][-1]['id']]}


def setup_history(client, count=3):
    conversation = _conversation(client)
    create_relationship(client,conversation['person_id'])
    rows=[]
    for n in range(count):
        response=client.post('/api/v1/messages',json={'conversation_id':conversation['id'],
            'sender_type':'person','content':f'第{n}条聊天','sent_at':f'2026-09-26T10:{n:02}:00+08:00'})
        assert response.status_code==201
        rows.append(response.json())
    return conversation,rows


def state(client, conversation):
    response=client.get(f"/api/v1/persons/{conversation['person_id']}/memory")
    assert response.status_code==200,response.text
    return response.json()


def test_incremental_memory_compresses_only_covered_history_and_audits(client):
    c,rows=setup_history(client,36);provider=MemoryProvider()
    assert memory.refresh_memory(LOCAL_USER_ID,c['person_id'],provider,max_batches=1)['status']=='partial'
    s=state(client,c)
    assert (s['covered_count'],s['total_count'])==(32,36)
    assert s['events'][0]['reason'] and s['events'][0]['before']['relationship']['status']!=s['events'][0]['after']['relationship']['status']
    with get_connection() as conn:
        context=AnalysisService().get_context(conn,LOCAL_USER_ID,c['id'])
    assert len(context['messages'])==16
    assert context['messages'][-1]['id']==rows[-1]['id']
    assert context['person_memory']['summary']['constraints']==['不要替用户承诺见面']
    assert memory.refresh_memory(LOCAL_USER_ID,c['person_id'],provider)['status']=='current'
    assert len(provider.calls[1]['messages'])==4
    assert provider.calls[1]['previous_summary']['description']
    count=len(provider.calls)
    memory.refresh_memory(LOCAL_USER_ID,c['person_id'],provider)
    assert len(provider.calls)==count
    assert state(client,c)['total_count']==36


def test_edit_invalidates_summary_and_rebuilds_without_old_summary(client):
    c,rows=setup_history(client);provider=MemoryProvider()
    memory.refresh_memory(LOCAL_USER_ID,c['person_id'],provider)
    assert client.patch('/api/v1/messages/'+rows[0]['id'],json={'content':'之前记录有误'}).status_code==200
    assert state(client,c)['stale'] and state(client,c)['summary']=={}
    with get_connection() as conn:
        context=AnalysisService().get_context(conn,LOCAL_USER_ID,c['id'])
    assert 'person_memory' not in context
    memory.refresh_memory(LOCAL_USER_ID,c['person_id'],provider)
    assert provider.calls[-1]['previous_summary']=={}
    assert not state(client,c)['stale']
    for row in rows:
        assert client.delete('/api/v1/messages/'+row['id']).status_code==204
    memory.refresh_memory(LOCAL_USER_ID,c['person_id'],provider)
    assert state(client,c)['summary']=={}
    assert state(client,c)['events'][0]['outcome']=='invalidated'


def test_invalid_provenance_does_not_publish_or_edit_relationship(client):
    c,_=setup_history(client)
    class Invalid(MemoryProvider):
        def summarize_person(self, context):
            proposal=super().summarize_person(context);proposal['evidence_source_ids']=['foreign-message']
            return proposal
    assert memory.refresh_memory(LOCAL_USER_ID,c['person_id'],Invalid())['status']=='failed'
    s=state(client,c)
    assert not s['summary'] and s['covered_count']==0 and s['events'][0]['outcome']=='failed'
    assert 'foreign-message' not in str(s)


def test_concurrent_edit_discards_stale_model_update(client):
    c,rows=setup_history(client)
    class Changing(MemoryProvider):
        def summarize_person(self, context):
            client.patch('/api/v1/messages/'+rows[0]['id'],json={'content':'新修改'})
            return super().summarize_person(context)
    assert memory.refresh_memory(LOCAL_USER_ID,c['person_id'],Changing())['status']=='superseded'
    s=state(client,c)
    assert not s['summary'] and s['events'][0]['outcome']=='discarded'


def test_audit_failure_rolls_back_the_applied_changes(client,monkeypatch):
    c,_=setup_history(client);original=memory.record_event
    def fail(conn,*args,**kwargs):
        if args[3]=='updated':raise RuntimeError('simulated audit storage failure')
        return original(conn,*args,**kwargs)
    monkeypatch.setattr(memory,'record_event',fail)
    assert memory.refresh_memory(LOCAL_USER_ID,c['person_id'],MemoryProvider())['status']=='failed'
    assert state(client,c)['summary']=={}
    with get_connection() as conn:
        status=conn.execute('SELECT status FROM relationships WHERE person_id=?',(c['person_id'],)).fetchone()[0]
    assert status!='互动积极'


def test_memory_endpoints_are_tenant_scoped_and_manual_changes_logged(client):
    c,_=setup_history(client)
    url=f"/api/v1/persons/{c['person_id']}/memory"
    assert client.get(url,headers={'X-User-ID':'foreign-memory-user'}).status_code==404
    assert client.post(url+'/refresh',headers={'X-User-ID':'foreign-memory-user'}).status_code==404
    assert client.patch('/api/v1/persons/'+c['person_id'],json={'notes':'手动补充偏好'}).status_code==200
    event=state(client,c)['events'][0]
    assert event['source']=='user' and event['reason'] and event['after']['notes']=='手动补充偏好'


def test_chinese_batch_examples_parse_to_beijing_without_touching_iso():
    rows=validate_candidates(parse_text('2026年09月26日 10:40:00 | 我 | 早早早\n2026年09月26日 10:41 | 对方 | 早呀'))
    assert rows[0].sender_type=='user' and rows[1].sender_type=='person'
    assert rows[0].sent_at=='2026-09-26T10:40:00+08:00'
    assert parse_text('2026-09-26T20:00:00Z | person | hello')[0].sent_at.endswith('Z')
    with pytest.raises(ValueError):parse_text('2026年02月30日 10:40 | 我 | 错误日期')
