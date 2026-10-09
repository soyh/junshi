"""Exercise the real DashScope-compatible transport and orchestration, no paid calls."""
import json
from copy import deepcopy

import httpx
import pytest

from app.api.routes import analysis_strategic_reply as route
from app.services.qwen_provider import QwenProvider
from tests.test_197_reference_skills_context import _conversation
from tests.test_strategic_reply import create_relationship


@pytest.mark.parametrize('mode,analysis_calls,draft_calls,status', [
    ('fresh', 1, 1, 200),
    ('analysis_once', 2, 1, 200),
    ('draft_once', 1, 2, 200),
    ('both_once', 2, 2, 200),
    ('analysis_always', 2, 0, 502),
    ('draft_always', 1, 2, 502),
    ('invalid_id', 1, 1, 502),
    ('network', 1, 0, 502),
])
def test_qwen_latest_turn_recovery(client, monkeypatch, mode, analysis_calls, draft_calls, status):
    convo = _conversation(client)
    create_relationship(client, convo['person_id'])
    messages = []
    for sender, content, when in [
        ('user', '麻婆豆腐', '2026-09-26T12:51:04+08:00'),
        ('person', '你在干嘛呐', '2026-09-26T20:00:00Z'),
    ]:
        response = client.post('/api/v1/messages', json={
            'conversation_id': convo['id'], 'sender_type': sender,
            'content': content, 'sent_at': when,
        })
        assert response.status_code == 201
        messages.append(response.json())
    old, latest = [item['id'] for item in messages]
    calls = {'analysis': [], 'draft': []}

    def transport(request):
        payload = json.loads(request.content)
        assert str(request.url) == 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'
        assert payload['model'] == 'qwen3.7-flash'
        stage = 'analysis' if 'analysis layer' in payload['messages'][0]['content'] else 'draft'
        text = payload['messages'][1]['content']
        context = json.loads(text.split('\n\n', 1)[1])
        calls[stage].append(deepcopy(context))
        assert latest in text.split('\n\n', 1)[0]
        assert context['conversation_focus']['reply_target_message']['content'] == '你在干嘛呐'
        if mode == 'network':
            raise httpx.ConnectError('fake transport failure', request=request)
        attempt = len(calls[stage])
        stale = mode == stage + '_always' or (mode in (stage + '_once', 'both_once') and attempt == 1)
        if stage == 'analysis':
            result = {key: [] for key in [
                'observed_facts', 'inferences', 'unknowns', 'hypotheses',
                'emotional_signals', 'relationship_signals', 'risk_signals',
                'intent_signals', 'evidence_links', 'analysis_constraints',
            ]}
            result['summary'] = '对方问你在做什么'
            # Mentioning the latest message in observed facts is not enough:
            # the usable hypothesis must itself retain canonical provenance.
            result['observed_facts'] = [{'content': '对方发来问候', 'evidence_source_ids': [latest]}]
            result['hypotheses'] = [{
                'content': '继续聊菜' if stale else '回答当前在做什么，不猜测对方的隐藏动机',
                'evidence_source_ids': [old] if stale else [old, latest],
            }]
        else:
            result = {
                'reply': '继续聊菜' if stale else '刚忙完，你呢？',
                'recommendation_ids': [context['recommendations'][0]['id']],
                'evidence_source_ids': ['invented'] if mode == 'invalid_id' else [old] if stale else [latest],
            }
        return httpx.Response(200, json={'choices': [{'message': {'content': json.dumps(result)}}]})

    with httpx.Client(transport=httpx.MockTransport(transport)) as mock_client:
        provider = QwenProvider(api_key='synthetic-test-key',
            base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
            model='qwen3.7-flash', client=mock_client)
        monkeypatch.setattr(route, '_build_provider', lambda *_: provider)
        response = client.get(f"/api/v1/conversations/{convo['id']}/strategic-reply/context")
    assert response.status_code == status, response.text
    assert len(calls['analysis']) == analysis_calls
    assert len(calls['draft']) == draft_calls
    for stage in calls:
        if calls[stage]:
            assert 'latest_turn_correction' not in calls[stage][0]
        if len(calls[stage]) == 2:
            assert calls[stage][1]['latest_turn_correction']['stage'] == stage
    if status == 200:
        assert response.json()['draft'] == '刚忙完，你呢？'
        assert response.json()['reply_inputs']['conversation_focus']['reply_target_message']['id'] == latest
    elif mode.endswith('_always'):
        detail = response.json()['detail']
        assert '已自动纠正一次' in detail
        assert ('分析阶段' if mode == 'analysis_always' else '回复阶段') in detail
        assert latest not in detail and '你在干嘛呐' not in detail
    else:
        assert '已自动纠正一次' not in response.json()['detail']
    # The retry never edits stored history, timestamps or IDs.
    for message in messages:
        assert client.get('/api/v1/messages/' + message['id']).json() == message
