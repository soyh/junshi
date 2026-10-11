import json
import httpx
import pytest
from app.services.memory_evidence import prepare,resolve
from app.services.memory_errors import MemoryProvenanceError
from app.schemas.person_memory import PersonMemoryProposal
from app.services.qwen_provider import QwenProvider
from app.services import person_memory as memory
from tests.test_207_person_memory import MemoryProvider,setup_history,state,LOCAL_USER_ID


def test_labels_scoped_to_batch_and_no_identifier_distractions():
    context={'person':{'id':'person-id','name':'甲'},'relationship':{'id':'rel-id','person_id':'person-id','stage':'unknown'},
             'messages':[{'id':'message-a','user_id':'u','conversation_id':'c','content':'你好'}]}
    wire,schema,mapping=prepare(context,PersonMemoryProposal.model_json_schema())
    label=next(iter(mapping))
    assert wire['messages'][0]=={'id':label,'content':'你好'}
    assert wire['person']=={'name':'甲'}
    assert wire['relationship']=={'stage':'unknown'}
    assert schema['properties']['evidence_source_ids']['items']['enum']==[label]
    assert context['messages'][0]['id']=='message-a'
    assert resolve({'evidence_source_ids':[label]},mapping)['evidence_source_ids']==['message-a']
    _,_,other=prepare({'messages':[{'id':'message-b'}]},PersonMemoryProposal.model_json_schema())
    with pytest.raises(MemoryProvenanceError):resolve({'evidence_source_ids':[label]},other)
    with pytest.raises(MemoryProvenanceError):resolve({'evidence_source_ids':[label,'fabricated']},mapping)


def test_real_transport_memory_roundtrip_and_audit_canonical_ids(client):
    c,rows=setup_history(client,40)
    calls=[]
    def handle(request):
        payload=json.loads(request.content)
        wire=json.loads(payload['messages'][1]['content']);calls.append(wire)
        labels=wire['allowed_evidence_source_ids']
        assert all(m['id'] in labels for m in wire['messages'])
        proposal=MemoryProvider().summarize_person(wire)
        # First attempt of batch two wrongly cites a prior batch; correction
        # must still fail closed, then recover using the actual new allowlist.
        if len(calls)==2:proposal['evidence_source_ids']=[calls[0]['messages'][0]['id']]
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(proposal)}}]})
    with httpx.Client(transport=httpx.MockTransport(handle)) as transport:
        provider=QwenProvider(api_key='synthetic',model='qwen-plus',client=transport)
        assert memory.refresh_memory(LOCAL_USER_ID,c['person_id'],provider)['status']=='current'
    data=state(client,c)
    assert data['covered_count']==40 and len(calls)==3
    assert calls[2]['correction']['error_code']=='evidence'
    actual={row['id'] for row in rows}
    assert all(set(e['evidence'])<=actual for e in data['events'])
    assert not any(e['outcome']=='failed' for e in data['events'])
