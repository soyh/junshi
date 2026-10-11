import json
import pytest
from app.services import compact_profile as profile,person_memory as memory,reply_priority
from app.schemas.person_memory import PersonMemoryProposal
from app.core.database import get_connection
from tests.test_207_person_memory import setup_history,state,MemoryProvider,LOCAL_USER_ID


def proposal(**changes):
    data=MemoryProvider().summarize_person({'messages':[{'id':'message'}]})
    data.update(changes)
    return PersonMemoryProposal.model_validate(data)


def test_profile_preserves_old_boundaries_and_exact_qualifiers():
    old={'description':'已有摘要','facts':['对方喜欢晚间聊天'],'constraints':['本周末不要邀约，下周安排待确认。']}
    merged,changes=profile.merge(old,proposal(facts=['对方喜欢晚间聊天'],constraints=['不替用户承诺见面']),['message'],True)
    assert len([e for e in profile.entries(merged) if e['kind']=='facts'])==1
    assert any(e['text']=='本周末不要邀约，下周安排待确认。' for e in profile.entries(merged))
    assert merged['_consolidated']
    assert changes


@pytest.mark.parametrize('budget',[1000,4000,10000,64000,200000])
def test_uniform_serialized_budget_no_sentence_truncation(budget):
    summary={'description':'摘要'*300,'constraints':['这周不见面，只有下周确认后才可安排。']*2,
             'facts':[f'第{i}项完整事实，条件成立时才适用。' for i in range(200)]}
    result=profile.project(summary,[{'content':'第199项事实'}],budget)
    if result:
        assert profile.size(result)<=min(4096,budget//10)
        for kind in profile.KINDS:
            assert all(text in summary.get(kind,[]) for text in result['summary'][kind])
        assert result['omitted_count']>0
    else:assert budget//10<600


def test_explicit_revision_keeps_history_and_requires_replacement():
    old={'constraints':['本周不见面。']}
    key=profile.entries(old)[0]['id']
    p=proposal(constraints=['对方明确改为周日见面。'],superseded_entry_ids=[key])
    result,changes=profile.merge(old,p,['new-message'],True)
    original=next(x for x in result['_profile'] if x['id']==key)
    assert not original['active'] and original['revision_evidence']==['new-message']
    assert changes[-1]['before']['active']
    with pytest.raises(ValueError):profile.merge(old,proposal(constraints=[],superseded_entry_ids=[key]),['m'],True)


def test_full_profile_endpoint_and_projection_do_not_send_archive(client):
    c,rows=setup_history(client)
    memory.refresh_memory(LOCAL_USER_ID,c['person_id'],MemoryProvider())
    data=client.get(f"/api/v1/persons/{c['person_id']}/memory/profile?limit=1").json()
    assert len(data['items'])==1 and data['has_more']
    assert data['items'][0]['evidence']
    assert client.get(f"/api/v1/persons/{c['person_id']}/memory/profile",headers={'X-User-ID':'foreign'}).status_code==404
    with get_connection() as conn:
        view,kept=memory.context_memory(conn,LOCAL_USER_ID,c['person_id'],rows)
    assert '_profile' not in json.dumps(view)
    assert kept[-1]['id']==rows[-1]['id']


def test_foreground_reply_defers_memory_without_advancing_coverage(client):
    c,_=setup_history(client);provider=MemoryProvider()
    reply_priority.enter(LOCAL_USER_ID)
    try:assert memory.refresh_memory(LOCAL_USER_ID,c['person_id'],provider)['status']=='paused_for_reply'
    finally:reply_priority.leave(LOCAL_USER_ID)
    assert not provider.calls and state(client,c)['covered_count']==0
    memory.refresh_memory(LOCAL_USER_ID,c['person_id'],provider)
    assert state(client,c)['covered_count']==3


def test_existing_completed_summary_conversion_without_llm(client):
    c,_=setup_history(client);provider=MemoryProvider()
    memory.refresh_memory(LOCAL_USER_ID,c['person_id'],provider)
    with get_connection() as conn:
        old=memory.snapshot(conn,LOCAL_USER_ID,c['person_id'])['summary']
        old=profile.public_summary(old)
        conn.execute('UPDATE person_memories SET summary_json=? WHERE person_id=?',(json.dumps(old),c['person_id']))
    count=len(provider.calls)
    memory.refresh_memory(LOCAL_USER_ID,c['person_id'],provider)
    assert len(provider.calls)==count and state(client,c)['consolidated']
    assert state(client,c)['events'][0]['after']['legacy_conversion']
