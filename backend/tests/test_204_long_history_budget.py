from copy import deepcopy
import json

import httpx
import pytest

from app.config.settings import get_settings
from app.services.history_request import reduce_history
from app.services.llm import LLMRequestError
from app.services.openai_chat_provider import OpenAIChatProvider
from app.services.qwen_provider import QwenProvider


def completion():
    return httpx.Response(200, json={'choices': [{'message': {'content': '{"summary":"ok"}'}}]})


def transcript(count=150):
    messages = [{'id': f'm{i}', 'sender_type': 'person' if i % 2 else 'user',
                 'content': '既往聊天记录，保留原始资料。' * 40 + str(i),
                 'sent_at': f'2026-10-07T10:{i % 60:02}:00+08:00'} for i in range(count)]
    messages[-1]['content'] = '今晚能见面吗？CURRENT_TARGET'
    return {'messages': messages, 'conversation_focus': {
        'recent_messages': deepcopy(messages[-8:]),
        'latest_human_message': deepcopy(messages[-1]),
        'latest_incoming_message': deepcopy(messages[-1]),
        'reply_target_message': deepcopy(messages[-1]),
        'required_evidence_source_ids': [messages[-1]['id']],
    }, 'learning_strategy': {'learning_inputs': {'action_feedback': [
        {'content': 'old derived learning' * 1000} for _ in range(20)]},
        'strategy_constraints': {'must_preserve_unknowns': True}}}


def make_provider(kind, handler):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    if kind == 'qwen':
        return QwenProvider(api_key='test-only', model='qwen-plus', client=client)
    return OpenAIChatProvider(api_key='test-only', base_url='https://unit.invalid/v1',
                              model='deepseek-chat', timeout_seconds=10, client=client)


@pytest.mark.parametrize('kind', ['deepseek', 'qwen'])
@pytest.mark.parametrize('method', ['analyze', 'generate_strategic_reply'])
def test_large_old_person_context_fits_and_preserves_target(monkeypatch, kind, method):
    monkeypatch.setattr(get_settings(), 'llm_input_budget_tokens', 16000)
    original = transcript()
    if method == 'generate_strategic_reply':
        original['recommendations'] = [{'id': 'r1', 'evidence_source_ids': ['m149'], 'content': 'Respond naturally'}]
        original['evidence'] = [{'source_type': 'message', 'source_id': x['id'], 'content': x['content']}
                                for x in original['messages']]
    before = deepcopy(original)
    calls = []
    def handler(request):
        payload = json.loads(request.content)
        calls.append(payload)
        assert len(json.dumps(payload, ensure_ascii=False).encode()) <= 16000
        sent = json.loads(payload['messages'][-1]['content'].split('\n\n', 1)[1])
        assert sent['conversation_focus']['reply_target_message'] == original['messages'][-1]
        assert sent['messages'][-1] == original['messages'][-1]
        assert sent['history_window']['partial_context'] is True
        assert sent['history_window']['messages_omitted_count'] > 0
        assert sent['learning_strategy']['strategy_constraints'] == original['learning_strategy']['strategy_constraints']
        assert sent['history_window']['person_learning_inputs_omitted']
        if method == 'generate_strategic_reply':
            assert sent['recommendations'] == original['recommendations']
            assert any(x['source_id'] == 'm149' for x in sent['evidence'])
        return completion()
    assert getattr(make_provider(kind, handler), method)(original) == {'summary': 'ok'}
    assert len(calls) == 1
    assert original == before


def test_small_context_remains_exact(monkeypatch):
    monkeypatch.setattr(get_settings(), 'llm_input_budget_tokens', 32768)
    original = {'messages': [{'id': 'm1', 'content': 'hello'}]}
    def handler(request):
        sent = json.loads(json.loads(request.content)['messages'][-1]['content'].split('\n\n', 1)[1])
        assert sent == original
        return completion()
    make_provider('deepseek', handler).analyze(original)


def test_required_old_evidence_survives_aggressive_window():
    data = transcript(40)
    data['required_evidence_source_ids'] = ['m0']
    data['recommendations'] = [{'id': 'r1', 'evidence_source_ids': ['m1']}]
    while reduce_history(data, aggressive=True):
        pass
    assert [x['id'] for x in data['messages']] == ['m0', 'm1', 'm38', 'm39']
    assert data['history_window']['messages_omitted_count'] == 36


def test_latest_outgoing_does_not_restore_old_reply_target():
    data = transcript(40)
    data['messages'][-1]['sender_type'] = 'user'
    data['conversation_focus'].update(latest_human_message=deepcopy(data['messages'][-1]),
                                     latest_incoming_message=deepcopy(data['messages'][-2]),
                                     reply_target_message=None, required_evidence_source_ids=[])
    while reduce_history(data, aggressive=True):
        pass
    assert data['conversation_focus']['reply_target_message'] is None
    assert data['conversation_focus']['latest_human_message']['sender_type'] == 'user'
    assert data['messages'][-1]['id'] == 'm39'


def test_oversized_current_target_fails_without_network_or_mutation(monkeypatch):
    monkeypatch.setattr(get_settings(), 'llm_input_budget_tokens', 12000)
    data = transcript(10)
    data['conversation_focus']['reply_target_message']['content'] = '不可静默截断' * 10000
    before = deepcopy(data)
    def handler(request):
        pytest.fail('mandatory oversized evidence must not reach network')
    with pytest.raises(LLMRequestError) as exc:
        make_provider('deepseek', handler).analyze(data)
    assert exc.value.category == 'local_budget'
    assert data == before


def test_upstream_context_limit_retries_smaller_chat_without_references(monkeypatch):
    monkeypatch.setattr(get_settings(), 'llm_input_budget_tokens', 32768)
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        if len(calls) == 1:
            return httpx.Response(400, json={'error': 'context_length_exceeded'})
        return completion()
    make_provider('deepseek', handler).analyze(transcript())
    assert len(calls) == 2
    assert len(json.dumps(calls[1]).encode()) < len(json.dumps(calls[0]).encode())


@pytest.mark.parametrize('status', [401, 429, 503])
def test_long_history_does_not_retry_non_context_failures(monkeypatch, status):
    monkeypatch.setattr(get_settings(), 'llm_input_budget_tokens', 16000)
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(status, json={'error': 'private secret'})
    with pytest.raises(LLMRequestError) as exc:
        make_provider('deepseek', handler).analyze(transcript())
    assert len(calls) == 1
    assert 'private secret' not in str(exc.value)


def test_real_reply_pipeline_with_long_history_preserves_database(client, monkeypatch):
    from datetime import datetime, timedelta, timezone
    from app.api.routes import analysis_strategic_reply as route
    from tests.test_197_reference_skills_context import _conversation
    from tests.test_strategic_reply import create_relationship

    monkeypatch.setattr(get_settings(), 'llm_input_budget_tokens', 20000)
    convo = _conversation(client)
    create_relationship(client, convo['person_id'])
    endpoint = f"/api/v1/conversations/{convo['id']}/messages"
    latest = None
    for i in range(60):
        response = client.post('/api/v1/messages', json={
            'conversation_id': convo['id'], 'sender_type': 'person' if i % 2 else 'user',
            'content': ('旧聊天内容' * 100) if i < 59 else '今天晚上一起吃饭吗？',
            'sent_at': (datetime(2026, 10, 7, tzinfo=timezone.utc) + timedelta(minutes=i)).isoformat(),
        })
        assert response.status_code == 201, response.text
        latest = response.json()['id']
    before = client.get(endpoint).json()
    calls = []
    def handler(request):
        payload = json.loads(request.content)
        assert len(json.dumps(payload, ensure_ascii=False).encode()) <= 20000
        sent = json.loads(payload['messages'][-1]['content'].split('\n\n', 1)[1])
        calls.append(sent)
        assert sent['conversation_focus']['reply_target_message']['id'] == latest
        if len(calls) == 1:
            assert sent['history_window']['messages_omitted_count'] > 0
            result = {key: [] for key in ['observed_facts', 'inferences', 'unknowns', 'hypotheses',
                'emotional_signals', 'relationship_signals', 'risk_signals', 'intent_signals',
                'evidence_links', 'analysis_constraints']}
            result.update(summary='对方提出邀约', hypotheses=[{'content': '回应邀约',
                'confidence': 0.8, 'evidence_source_ids': [latest]}])
        else:
            result = {'reply': '好呀，你想吃什么？',
                'recommendation_ids': [sent['recommendations'][0]['id']],
                'evidence_source_ids': [latest]}
        return httpx.Response(200, json={'choices': [{'message': {'content': json.dumps(result)}}]})
    monkeypatch.setattr(route, '_build_provider', lambda *_: make_provider('qwen', handler))
    response = client.get(f"/api/v1/conversations/{convo['id']}/strategic-reply/context")
    assert response.status_code == 200, response.text
    assert response.json()['draft'] == '好呀，你想吃什么？'
    assert any(x.startswith('[历史窗口]') for x in response.json()['structured_analysis']['analysis_constraints'])
    assert len(calls) == 2
    assert client.get(endpoint).json() == before
