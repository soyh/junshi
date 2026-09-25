import io
import json
import zipfile

from app.core.database import get_connection
from app.services.analysis import AnalysisService
from app.services.analysis_action_plan import AnalysisActionPlanService
from app.services.analysis_strategic_reply import AnalysisStrategicReplyService
from app.services.analysis_strategy import AnalysisStrategyService
from app.services.openai_chat_provider import OpenAIChatProvider
from app.services.reference_context import ReferenceContextService
from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML


LOCAL_USER_ID = "00000000-0000-0000-0000-000000000001"
OTHER_USER_ID = "11111111-1111-1111-1111-111111111111"


def _conversation(client, *, name="Reference测试对象"):
    person = client.post(
        "/api/v1/persons",
        json={"name": name, "nickname": None, "notes": None},
    )
    assert person.status_code == 201
    conversation = client.post(
        "/api/v1/conversations",
        json={"person_id": person.json()["id"], "title": "参考上下文会话"},
    )
    assert conversation.status_code == 201
    return conversation.json()


def _upload(
    client,
    filename,
    content,
    *,
    reference_type="auto",
    priority=100,
    enabled=True,
    headers=None,
):
    response = client.post(
        "/api/v1/references",
        files={"file": (filename, content, "application/octet-stream")},
        data={
            "reference_type": reference_type,
            "priority": str(priority),
            "enabled_by_default": "true" if enabled else "false",
        },
        headers=headers or {},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _skill_zip(text="# Skill\nUse attachment theory."):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("my-skill/SKILL.md", text)
        archive.writestr("my-skill/notes.txt", "supporting notes")
    return buffer.getvalue()


def test_reference_migration_tables_exist(client):
    with get_connection() as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert "model_references" in tables
    assert "conversation_model_reference_overrides" in tables


def test_multi_document_multi_skill_and_mixed_upload(client):
    _upload(client, "background.md", b"relationship background", priority=30)
    skill_md = _upload(client, "SKILL.md", b"# Method\nUse a cautious lens.", priority=10)
    explicit_skill = _upload(
        client,
        "custom.txt",
        b"Prefer observable evidence.",
        reference_type="skill",
        priority=20,
    )
    zipped_skill = _upload(client, "bundle.zip", _skill_zip(), priority=15)
    second_doc = _upload(client, "notes.csv", b"topic,value\npace,slow\n", priority=40)

    assert skill_md["reference_type"] == "skill"
    assert explicit_skill["reference_type"] == "skill"
    assert zipped_skill["reference_type"] == "skill"
    assert second_doc["reference_type"] == "document"

    listed = client.get("/api/v1/references")
    assert listed.status_code == 200
    items = listed.json()
    assert len(items) == 5
    assert [item["priority"] for item in items] == [10, 15, 20, 30, 40]
    assert [item["reference_type"] for item in items].count("skill") == 3
    assert [item["reference_type"] for item in items].count("document") == 2


def test_docx_is_supported_without_external_parser(client):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body><w:p><w:r><w:t>第一段参考资料</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>第二段</w:t></w:r></w:p></w:body></w:document>',
        )
    item = _upload(client, "guide.docx", buffer.getvalue())
    assert item["reference_type"] == "document"
    assert "第一段参考资料" in item["content_preview"]
    assert "第二段" in item["content_preview"]


def test_unsupported_pdf_is_rejected_explicitly(client):
    response = client.post(
        "/api/v1/references",
        files={"file": ("guide.pdf", b"%PDF-1.7 fake", "application/pdf")},
        data={"reference_type": "document"},
    )
    assert response.status_code == 422
    assert "supported reference files" in response.json()["detail"]


def test_global_disable_and_conversation_override(client):
    conversation = _conversation(client)
    enabled = _upload(client, "enabled.md", b"enabled content", priority=20)
    disabled = _upload(
        client,
        "disabled.md",
        b"disabled content",
        priority=10,
        enabled=False,
    )

    global_context = client.get(
        f"/api/v1/conversations/{conversation['id']}/references/context"
    )
    assert global_context.status_code == 200
    assert [item["name"] for item in global_context.json()["items"]] == ["enabled.md"]

    response = client.put(
        f"/api/v1/conversations/{conversation['id']}/references/{disabled['id']}",
        json={"enabled": True, "priority": 5},
    )
    assert response.status_code == 200
    assert response.json()["effective_enabled"] is True
    assert response.json()["effective_priority"] == 5

    response = client.put(
        f"/api/v1/conversations/{conversation['id']}/references/{enabled['id']}",
        json={"enabled": False},
    )
    assert response.status_code == 200
    assert response.json()["effective_enabled"] is False

    context = client.get(
        f"/api/v1/conversations/{conversation['id']}/references/context"
    ).json()
    assert [item["reference_id"] for item in context["items"]] == [disabled["id"]]
    assert context["items"][0]["priority"] == 5

    cleared = client.delete(
        f"/api/v1/conversations/{conversation['id']}/references/{disabled['id']}/override"
    )
    assert cleared.status_code == 200
    assert cleared.json()["effective_enabled"] is False


def test_cross_user_reference_isolation(client):
    conversation = _conversation(client)
    owned = _upload(client, "private.md", b"private reference")
    other_headers = {"X-User-ID": OTHER_USER_ID}

    assert client.get("/api/v1/references", headers=other_headers).json() == []

    patch = client.patch(
        f"/api/v1/references/{owned['id']}",
        json={"priority": 1},
        headers=other_headers,
    )
    assert patch.status_code == 404

    delete = client.delete(
        f"/api/v1/references/{owned['id']}",
        headers=other_headers,
    )
    assert delete.status_code == 404

    override = client.put(
        f"/api/v1/conversations/{conversation['id']}/references/{owned['id']}",
        json={"enabled": True},
        headers=other_headers,
    )
    assert override.status_code == 404


def test_delete_reference_cascades_conversation_override(client):
    conversation = _conversation(client)
    item = _upload(client, "delete-me.skill", b"Use concise analysis")
    assert client.put(
        f"/api/v1/conversations/{conversation['id']}/references/{item['id']}",
        json={"enabled": True, "priority": 9},
    ).status_code == 200

    assert client.delete(f"/api/v1/references/{item['id']}").status_code == 204
    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM conversation_model_reference_overrides WHERE reference_id = ?",
            (item["id"],),
        ).fetchone()[0]
    assert count == 0


def test_reference_context_has_stable_sources_and_guardrail_policy(client):
    conversation = _conversation(client)
    doc = _upload(client, "facts.md", b"Secondary background", priority=20)
    skill = _upload(client, "SKILL.md", b"Use a slow evidence-first method", priority=10)

    payload = client.get(
        f"/api/v1/conversations/{conversation['id']}/references/context"
    ).json()
    assert payload["count"] == 2
    assert [item["reference_id"] for item in payload["items"]] == [skill["id"], doc["id"]]
    assert [item["type"] for item in payload["items"]] == ["skill", "document"]
    assert payload["items"][0]["name"] == "SKILL.md"
    assert "safety rules" in payload["policy"]["system_precedence"]
    assert "never be cited as canonical evidence" in payload["policy"]["skill_semantics"]
    assert "secondary reference material" in payload["policy"]["document_semantics"]


def test_analysis_context_consumes_mixed_references(client):
    conversation = _conversation(client)
    _upload(client, "guide.md", b"Background guide", priority=20)
    _upload(client, "SKILL.md", b"Reason from observable behavior", priority=10)

    with get_connection() as conn:
        context = AnalysisService().get_context(
            conn,
            LOCAL_USER_ID,
            conversation["id"],
        )

    refs = context["model_references"]
    assert refs["count"] == 2
    assert [item["type"] for item in refs["items"]] == ["skill", "document"]
    assert "Background guide" in refs["items"][1]["content"]
    assert all("reference_id" in item for item in refs["items"])


class _FakeStructuredAnalysis:
    def model_dump(self, mode="json"):
        return {
            "summary": "derived",
            "observed_facts": [],
            "inferences": [],
            "unknowns": [],
            "hypotheses": [],
            "emotional_signals": [],
            "relationship_signals": [],
            "risk_signals": [],
            "intent_signals": [],
            "evidence_links": [],
            "analysis_constraints": [],
        }


class _FakeAnalysisService:
    def __init__(self, context):
        self.context = context

    def get_context(self, conn, user_id, conversation_id):
        return self.context


class _FakeAnalysisLLMService:
    def __init__(self, context):
        self.analysis_service = _FakeAnalysisService(context)

    def analyze_context(self, context, provider=None):
        assert context["model_references"]["items"][0]["type"] == "skill"
        return _FakeStructuredAnalysis()


class _FakeStrategyDecision:
    def get_context(self, conn, user_id, person_id, structured_analysis=None):
        return {"person": {"id": person_id}, "strategy_constraints": {}, "marker": "strategy"}


class _FakeRecommendation:
    def __init__(self, refs):
        self.refs = refs

    def build_context(self, conn, user_id, conversation_id, provider=None, structured_analysis=None):
        return {
            "current_state": {},
            "evidence": [{"source_type": "message", "source_id": "m1"}],
            "unknowns": [],
            "recommendations": [
                {"id": "r1", "reply": "reply", "evidence_source_ids": ["m1"]}
            ],
            "model_references": self.refs,
        }


class _FakeActionPlan:
    def get_context(self, conn, user_id, person_id):
        return {"recommendations": [], "action_plan": [], "action_constraints": {}}

    def build_action_plan(self, recommendations, evidence):
        return [{"step": "wait"}]


class _CaptureReplyLLM:
    def __init__(self):
        self.context = None

    def generate(self, context, provider=None):
        self.context = context
        return {"recommendation_ids": ["r1"], "reply": "reply", "evidence_source_ids": ["m1"]}


class _FakeStrategicReply:
    def build_context_from_recommendation_context(self, context, *, reply_candidates=None, derived=False):
        return {**context, "draft": "reply"}


class _FakeLearningBridge:
    def get_context(self, conn, user_id, person_id):
        return {"learning_strategy": {"candidates": []}}


class _FakeAnalysisBridge:
    def build_context(self, reply_context, structured_analysis):
        return reply_context


def _chain_context():
    refs = {
        "count": 2,
        "policy": {"system_precedence": "system wins"},
        "items": [
            {"reference_id": "s1", "name": "skill", "type": "skill", "priority": 1, "content": "method"},
            {"reference_id": "d1", "name": "doc", "type": "document", "priority": 2, "content": "background"},
        ],
    }
    return {
        "conversation": {"id": "c1"},
        "person": {"id": "p1"},
        "messages": [{"id": "m1", "sender_type": "person", "content": "hi"}],
        "learning_strategy": {"candidates": []},
        "model_references": refs,
    }


def test_strategy_and_action_plan_context_preserve_references():
    context = _chain_context()
    llm = _FakeAnalysisLLMService(context)

    strategy = AnalysisStrategyService(
        analysis_llm_service=llm,
        strategy_decision_service=_FakeStrategyDecision(),
    ).build_strategy_context(None, "u", "c", provider=object())
    assert strategy["model_references"] == context["model_references"]

    action = AnalysisActionPlanService(
        analysis_llm_service=llm,
        action_plan_service=_FakeActionPlan(),
        analysis_recommendation_service=_FakeRecommendation(context["model_references"]),
    ).build_context(None, "u", "c", provider=object())
    assert action["model_references"] == context["model_references"]
    assert action["action_plan"] == [{"step": "wait"}]


def test_strategic_reply_generation_consumes_reference_context():
    context = _chain_context()
    capture = _CaptureReplyLLM()
    service = AnalysisStrategicReplyService(
        analysis_llm_service=_FakeAnalysisLLMService(context),
        strategic_reply_service=_FakeStrategicReply(),
        analysis_bridge_service=_FakeAnalysisBridge(),
        learning_strategy_bridge_service=_FakeLearningBridge(),
        analysis_recommendation_service=_FakeRecommendation(context["model_references"]),
        strategic_reply_llm_service=capture,
    )
    result = service.build_context(None, "u", "c", provider=object())
    assert capture.context["model_references"] == context["model_references"]
    assert capture.context["conversation_focus"]["model_references"] == context["model_references"]
    assert result["model_references"] == context["model_references"]


def test_provider_prompt_marks_references_lower_priority_and_source_distinct():
    system_prompt = OpenAIChatProvider._system_prompt()
    reply_prompt = OpenAIChatProvider._strategic_reply_system_prompt()
    context = _chain_context()
    user_prompt = OpenAIChatProvider._user_prompt(context)

    for prompt in (system_prompt, reply_prompt):
        assert "lower-priority" in prompt
        assert "user isolation" in prompt
        assert "canonical evidence" in prompt
    assert "reference_id" in user_prompt
    assert '"type": "skill"' in user_prompt
    assert '"type": "document"' in user_prompt
    assert "method" in user_prompt
    assert "background" in user_prompt


def test_reference_settings_ui_supports_multi_and_mixed_sources():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML
    assert "参考资料 / Skills" in html
    assert "reference-context-settings" in html
    assert "reference-files" in html
    assert "files.multiple = true" in html
    assert "自动判断（推荐）" in html
    assert "当前会话启用" in html
    assert "当前会话禁用" in html
    assert "可同时启用多个文档、多个 Skill，或混合参考" in html
    assert "包含 SKILL.md 的 Skill ZIP" in html
