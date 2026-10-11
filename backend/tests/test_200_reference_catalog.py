import json

import httpx
import pytest

from app.api.routes.analysis_strategic_reply import _safe_llm_failure_detail
from app.config.settings import get_settings
from app.core.database import get_connection
from app.services.analysis import AnalysisService
from app.services.llm import LLMRequestError
from app.services.openai_chat_provider import OpenAIChatProvider
from app.services.qwen_provider import QwenProvider
from app.services.reference_request import prepare_context
from app.services.reference_retrieval import retrieve
from tests.test_197_reference_skills_context import _conversation, _upload, LOCAL_USER_ID, OTHER_USER_ID


def item(key, content, name=None, kind="document"):
    return {"reference_id": key, "name": name or key + ".md", "original_filename": name or key + ".md",
            "type": kind, "priority": 100, "description": None, "content": content}


def context(library, query="发生冲突后应该如何修复关系"):
    refs = retrieve(library, query)
    refs.update(count=len(refs["items"]), conversation_id="c1", policy={"system_precedence": "system wins"})
    return {"messages": [{"id": "m1", "content": query}], "model_references": refs,
            "conversation_focus": {"model_references": refs, "required_evidence_source_ids": ["m1"]}}


def completion(result):
    return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(result)}}]})


def provider(handler, model="deepseek-chat"):
    return OpenAIChatProvider(api_key="secret-key", base_url="https://unit.invalid/v1", model=model,
                              timeout_seconds=10, client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_chinese_directory_aliases_and_tail_retrieval():
    library = [item(str(n), "天气和旅行" * 2000) for n in range(35)]
    library += [item("target", "其他主题。" * 11000 + "\n冲突修复需要先道歉，再具体补救。", "冲突指南.md"),
                item("guide", "- 冲突与修复：`references/冲突指南.md`\n- 情绪回应：[回应](缺失.md)\n- 外部：[外链](https://invalid/a.md)", "导读.md")]
    result = retrieve(library, "发生冲突后应该怎样道歉修复")
    target = next(x for x in result["items"] if x["reference_id"] == "target")
    assert "具体补救" in target["content"]
    assert max(target["chunk_offsets"]) > 40000
    assert target["truncated"]
    catalog = next(x for x in result["catalog"] if x["reference_id"] == "target")
    assert "冲突与修复" in catalog["topics"]
    assert result["retrieval"]["candidate_count"] == 24
    assert result["retrieval"]["omitted_from_catalog"] == len(library) - 24
    assert result["retrieval"]["warnings"] == [{"filename": "缺失.md", "reason": "not_enabled_or_missing"}]
    assert all(len(x["content"]) <= 1800 for x in result["candidates"])


def test_duplicate_filename_does_not_resolve_to_arbitrary_file():
    result = retrieve([item("a", "a", "同名.md"), item("b", "b", "同名.md"),
                       item("g", "- topic: `同名.md`", "导读.md")], "topic")
    assert result["retrieval"]["warnings"][0]["reason"] == "ambiguous"
    assert all(not x["topics"] for x in result["catalog"])


def test_catalog_enforces_user_and_conversation_permissions(client):
    convo = _conversation(client)
    _upload(client, "导读.md", "- 冲突：`私密.md`\n- 情绪：`停用.md`".encode())
    _upload(client, "私密.md", b"FOREIGN SECRET", headers={"X-User-ID": OTHER_USER_ID})
    _upload(client, "停用.md", b"DISABLED SECRET", enabled=False)
    target = _upload(client, "修复.md", "道歉与补救".encode())
    assert client.post("/api/v1/messages", json={"conversation_id": convo["id"], "sender_type": "person",
        "content": "需要道歉修复", "sent_at": "2026-10-05T00:00:00Z"}).status_code == 201
    response = client.get(f"/api/v1/conversations/{convo['id']}/references/context")
    assert response.status_code == 200
    data = response.json()
    assert "candidates" not in data  # internal excerpt pool is not the public preview
    assert target["id"] in [x["reference_id"] for x in data["catalog"]]
    assert len(data["retrieval"]["warnings"]) == 2
    assert "FOREIGN SECRET" not in response.text and "DISABLED SECRET" not in response.text
    assert client.get(f"/api/v1/conversations/{convo['id']}/references/context",
                      headers={"X-User-ID": OTHER_USER_ID}).status_code == 404
    with get_connection() as conn:
        internal = AnalysisService().get_context(conn, LOCAL_USER_ID, convo["id"])
    assert "candidates" in internal["model_references"]
    assert internal["model_references"]["retrieval"]["query"] == "需要道歉修复"


@pytest.mark.parametrize("model", ["deepseek-chat", "qwen-plus"])
@pytest.mark.parametrize("method", ["analyze", "generate_strategic_reply"])
def test_two_stage_transport_sends_catalog_then_selected_body_once(model, method):
    calls = []
    def handler(request):
        payload = json.loads(request.content)
        calls.append(payload)
        if len(calls) == 1:
            user = payload["messages"][-1]["content"]
            assert "SECRET_DOC_BODY" not in user
            assert "OTHER_DOC_BODY" not in user
            assert "target" in user
            return completion({"reference_ids": ["target"]})
        user = payload["messages"][-1]["content"]
        assert user.count("SECRET_DOC_BODY") == 1
        assert "OTHER_DOC_BODY" not in user
        assert "SKILL_METHOD" in user
        assert '"candidates"' not in user
        assert '"catalog"' not in user
        assert "m1" in user
        return completion({"summary": "ok"})
    original = context([item("target", "SECRET_DOC_BODY"), item("other", "OTHER_DOC_BODY"),
                        item("s", "SKILL_METHOD", kind="skill")])
    before = json.dumps(original)
    p = provider(handler, model)
    if model == "qwen-plus":
        p = QwenProvider(api_key="secret-key", model=model, client=p._client)
    assert getattr(p, method)(original) == {"summary": "ok"}
    assert len(calls) == 2
    assert json.dumps(original) == before


@pytest.mark.parametrize("answer", [None, ["foreign-id"], ["../../etc/passwd"], [123], "target"])
def test_invalid_model_selection_falls_back_to_local(answer):
    result = prepare_context(context([item("target", "body")]), lambda *_: answer)
    assert result["model_references"]["retrieval"]["mode"] == "local_fallback"
    assert result["model_references"]["items"][0]["reference_id"] == "target"


def test_empty_selection_keeps_core_skill_but_not_unselected_document():
    result = prepare_context(context([item("s", "method", kind="skill"), item("d", "doc")]), lambda *_: [])
    assert [x["reference_id"] for x in result["model_references"]["items"]] == ["s"]


def test_selector_timeout_falls_back_and_main_request_succeeds():
    calls = []
    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            raise httpx.ReadTimeout("SECRET transport body", request=request)
        assert "local_fallback" in request.content.decode()
        return completion({"summary": "ok"})
    assert provider(handler).analyze(context([item("d", "reference")])) == {"summary": "ok"}
    assert len(calls) == 2


@pytest.mark.parametrize("status,category", [(401, "auth"), (403, "auth"), (429, "rate_limit"), (503, "upstream")])
def test_typed_errors_reach_ui_without_provider_secrets_or_retries(status, category):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(status, json={"error": "SECRET sk-123 user private text"})
    with pytest.raises(LLMRequestError) as exc:
        provider(handler).analyze({"messages": []})
    assert exc.value.category == category
    detail = _safe_llm_failure_detail(exc.value)
    assert LLMRequestError.MESSAGES[category] in detail
    assert "SECRET" not in detail and "sk-123" not in detail
    assert len(calls) == 1


def test_input_budget_trims_only_references_and_preserves_canonical_evidence(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_input_budget_tokens", 12000)
    calls = []
    def handler(request):
        payload = json.loads(request.content)
        calls.append(payload)
        assert len(json.dumps(payload, ensure_ascii=False).encode()) <= 12000
        assert "canonical-evidence-do-not-trim" in payload["messages"][-1]["content"]
        return completion({"summary": "ok"})
    # Legacy contexts are also budgeted; repeated bodies must not inflate requests.
    refs = {"items": [item("d", "内容" * 40000)], "count": 1}
    original = {"messages": [{"id": "m", "content": "canonical-evidence-do-not-trim"}],
                "model_references": refs, "conversation_focus": {"model_references": refs}}
    provider(handler).analyze(original)
    assert len(calls) == 1
    assert len(original["model_references"]["items"][0]["content"]) == 80000


def test_oversized_chat_is_rejected_before_network_without_silent_truncation(monkeypatch):
    monkeypatch.setattr(get_settings(), "llm_input_budget_tokens", 4096)
    def handler(request):
        pytest.fail("oversized request must not reach network")
    with pytest.raises(LLMRequestError) as exc:
        provider(handler).analyze({"messages": [{"content": "canonical" * 5000}]})
    assert exc.value.category == "local_budget"


def test_context_limit_gets_only_one_smaller_retry():
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(400, json={"error": {"code": "context_length_exceeded"}})
    with pytest.raises(LLMRequestError) as exc:
        provider(handler).analyze({"messages": [], "model_references": {"items": [item("d", "x" * 18000)], "count": 1}})
    assert exc.value.category == "context_limit"
    assert len(calls) == 2
    assert len(calls[1]["messages"][-1]["content"]) < len(calls[0]["messages"][-1]["content"])
