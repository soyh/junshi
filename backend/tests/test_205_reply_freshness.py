import pytest
from pydantic import ValidationError

from app.schemas.strategic_reply_generation import StrategicReplyGeneration
from app.services.analysis import AnalysisService
from app.services.analysis_strategic_reply import AnalysisStrategicReplyService
from app.core.database import get_connection
from app.services.reference_retrieval import retrieve
from tests.test_197_reference_skills_context import _conversation, LOCAL_USER_ID


@pytest.mark.parametrize('reply', ['', ' ', '\t\n', '\u200b', '\ufeff', '\u200e\u200f', '\x00'])
def test_invisible_draft_is_not_success(reply):
    with pytest.raises(ValidationError):
        StrategicReplyGeneration(reply=reply, recommendation_ids=['r'], evidence_source_ids=['m'])


def test_reply_is_trimmed_without_changing_meaning():
    result = StrategicReplyGeneration(reply='  你呢？\n', recommendation_ids=['r'], evidence_source_ids=['m'])
    assert result.reply == '你呢？'


def test_reported_transcript_and_mixed_timezone_target(client):
    convo = _conversation(client)
    records = [
        ('user', '舒服', '2026-09-26T12:51:02+08:00'),
        ('person', '啊哈', '2026-09-26T12:51:03+08:00'),
        ('user', '麻婆豆腐', '2026-09-26T12:51:04+08:00'),
        ('user', '番茄鸡蛋', '2026-09-26T12:51:05+08:00'),
        ('user', '回锅肉', '2026-09-26T12:51:06+08:00'),
        ('person', '都是下饭菜', '2026-09-26T12:51:07+08:00'),
        ('user', '对', '2026-09-26T12:51:08+08:00'),
        ('person', '你在干嘛呐', '2026-09-26T20:00:00+00:00'),
        # Imported later but chronologically earlier. Lexical sorting gets this wrong.
        ('user', '这条是较早的历史', '2026-09-26T23:00:00+08:00'),
    ]
    newest = None
    for sender, content, sent_at in records:
        result = client.post('/api/v1/messages', json={'conversation_id': convo['id'],
            'sender_type': sender, 'content': content, 'sent_at': sent_at})
        assert result.status_code == 201
        if content == '你在干嘛呐':
            newest = result.json()['id']
    with get_connection() as conn:
        context = AnalysisService().get_context(conn, LOCAL_USER_ID, convo['id'])
    focus = AnalysisStrategicReplyService._build_conversation_focus(context)
    assert focus['reply_target_message']['id'] == newest
    assert focus['reply_target_message']['content'] == '你在干嘛呐'
    assert focus['required_evidence_source_ids'] == [newest]


def test_missing_guide_is_warning_not_generation_blocker():
    library = [{'reference_id': str(i), 'name': f'资料{i}.md', 'type': 'document',
                'content': '聊天接话'} for i in range(44)]
    library[0]['content'] = '- 导读：`00-导读与使用分级.md`'
    data = retrieve(library, '你在干嘛呐')
    assert data['retrieval']['candidate_count'] == 24
    assert data['retrieval']['omitted_from_catalog'] == 20
    assert data['retrieval']['warnings'] == [{'filename': '00-导读与使用分级.md', 'reason': 'not_enabled_or_missing'}]
    assert data['items']


@pytest.mark.parametrize('mode', ['empty', 'whitespace'])
def test_explicit_generation_never_returns_success_with_blank_draft(client, monkeypatch, mode):
    from app.api.routes import analysis_strategic_reply as route
    from tests.test_strategic_reply import create_relationship
    convo = _conversation(client)
    create_relationship(client, convo['person_id'])
    sender = 'user' if mode == 'empty' else 'person'
    msg = client.post('/api/v1/messages', json={'conversation_id': convo['id'],
        'sender_type': sender, 'content': '你在干嘛呐', 'sent_at': '2026-09-26T20:00:00Z'}).json()
    class Fake:
        def analyze(self, context):
            result = {key: [] for key in ['observed_facts','inferences','unknowns','hypotheses',
                'emotional_signals','relationship_signals','risk_signals','intent_signals',
                'evidence_links','analysis_constraints']}
            result['summary'] = '当前聊天'
            if mode == 'whitespace':
                result['hypotheses'] = [{'content':'回应最新消息','confidence':0.8,'evidence_source_ids':[msg['id']]}]
            return result
        def generate_strategic_reply(self, context):
            assert mode == 'whitespace'
            return {'recommendation_ids':[context['recommendations'][0]['id']],
                    'evidence_source_ids':[msg['id']], 'reply':'   \n'}
    monkeypatch.setattr(route, '_build_provider', lambda *_: Fake())
    response = client.get(f"/api/v1/conversations/{convo['id']}/strategic-reply/context")
    assert response.status_code == 502, response.text
    assert '未返回有效回复草稿' in response.json()['detail']
