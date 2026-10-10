from app.services import person_memory as memory
from app.services.llm import LLMRequestError
from tests.test_207_person_memory import setup_history, state, MemoryProvider, LOCAL_USER_ID


def test_second_batch_corrects_without_losing_first_batch(client):
    c,_=setup_history(client,40)
    class Provider(MemoryProvider):
        def summarize_person(self,context):
            result=super().summarize_person(context)
            if len(self.calls)==2:
                result['facts']=['超长摘要' * 400]
            return result
    provider=Provider()
    assert memory.refresh_memory(LOCAL_USER_ID,c['person_id'],provider)['status']=='current'
    data=state(client,c)
    assert data['covered_count']==40
    assert len(provider.calls)==3
    assert provider.calls[2]['messages']==provider.calls[1]['messages']
    assert provider.calls[2]['correction']['fields']==['facts']
    assert data['events'][0]['after']['attempts']==2


def test_exhaustion_preserves_coverage_and_sanitizes_diagnostic(client):
    c,_=setup_history(client,40)
    class Provider(MemoryProvider):
        def summarize_person(self,context):
            result=super().summarize_person(context)
            if len(self.calls)>1: result['evidence_source_ids']=['private-foreign-message-secret']
            return result
    provider=Provider()
    assert memory.refresh_memory(LOCAL_USER_ID,c['person_id'],provider)['status']=='failed'
    data=state(client,c)
    assert data['covered_count']==32 and len(provider.calls)==5
    assert data['events'][0]['after']=={'error_code':'evidence','attempts':4}
    assert 'private-foreign-message-secret' not in str(data)
    good=MemoryProvider()
    memory.refresh_memory(LOCAL_USER_ID,c['person_id'],good)
    assert len(good.calls[0]['messages'])==8
    assert state(client,c)['covered_count']==40


def test_budget_shrinks_batch_and_only_covers_processed_messages(client):
    c,_=setup_history(client,32)
    class Provider(MemoryProvider):
        def summarize_person(self,context):
            if len(context['messages'])>8: raise LLMRequestError('local_budget')
            return super().summarize_person(context)
    provider=Provider()
    memory.refresh_memory(LOCAL_USER_ID,c['person_id'],provider,max_batches=1)
    assert state(client,c)['covered_count']==8
    assert provider.calls[0]['remaining_message_count']==24


def test_auth_error_does_not_retry(client):
    c,_=setup_history(client)
    class Provider(MemoryProvider):
        def summarize_person(self,context):
            self.calls.append(context)
            raise LLMRequestError('auth')
    provider=Provider()
    memory.refresh_memory(LOCAL_USER_ID,c['person_id'],provider)
    assert len(provider.calls)==1
    data=state(client,c)
    assert data['covered_count']==0
    assert data['events'][0]['after']['error_code']=='auth'


def test_unknown_exception_is_not_exposed(client):
    c,_=setup_history(client)
    class Provider(MemoryProvider):
        def summarize_person(self,context):raise RuntimeError('sk-secret private-chat')
    memory.refresh_memory(LOCAL_USER_ID,c['person_id'],Provider())
    data=state(client,c)
    assert data['events'][0]['after']['error_code']=='internal'
    assert 'sk-secret' not in str(data) and 'private-chat' not in str(data)
