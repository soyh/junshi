from app.api.routes import analysis_strategic_reply


PASSWORD = "correct-horse-battery-staple"


class FakeProvider:
    pass


class FakeStrategicReplyService:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def build_context(self, conn, user_id, conversation_id, *, provider=None):
        self.calls.append((user_id, conversation_id, provider))
        return self.result


def _register(client, username: str):
    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _auth(token: str):
    return {"Authorization": f"Bearer {token}"}


def _create_person_conversation(client, token: str):
    person = client.post(
        "/api/v1/persons",
        headers=_auth(token),
        json={"name": "TEST-153 Person"},
    )
    assert person.status_code == 201
    person_body = person.json()
    person_id = person_body["id"]
    user_id = person_body["user_id"]
    conversation = client.post(
        "/api/v1/conversations",
        headers=_auth(token),
        json={"person_id": person_id, "title": "TEST-153 Conversation"},
    )
    assert conversation.status_code == 201
    return user_id, person_id, conversation.json()["id"]


def _structured_analysis():
    return {
        "summary": "derived reply analysis",
        "observed_facts": [],
        "inferences": [],
        "unknowns": [],
        "hypotheses": [],
        "emotional_signals": [],
        "relationship_signals": [],
        "risk_signals": [],
        "intent_signals": [],
        "evidence_links": [],
        "analysis_constraints": ["derived_only"],
    }


def _reply_result(person_id: str):
    return {
        "person": {"id": person_id, "name": "TEST-153 Person"},
        "relationship": {},
        "current_state": {"status": "active", "stage": "dating"},
        "evidence": [
            {
                "source_type": "message",
                "source_id": "message-153",
                "content": "对方问今晚有没有空",
            }
        ],
        "facts": [],
        "inferences": [],
        "unknowns": [{"content": "对方具体安排未知"}],
        "recommendations": [
            {
                "recommendation": "先确认时间，再自然回应",
                "reply": "有空呀，你有什么安排？",
                "evidence_source_ids": ["message-153"],
            }
        ],
        "reply_constraints": {
            "must_not_auto_send": True,
            "must_preserve_unknowns": True,
            "must_treat_llm_output_as_derived": True,
        },
        "draft": "有空呀，你有什么安排？",
        "learning_strategy": {
            "constraints": {"must_not_auto_execute": True},
            "candidates": [],
        },
        "structured_analysis": _structured_analysis(),
        "reply_inputs": {"evidence_source_ids": ["message-153"]},
    }


def _strategic_reply_fragment(html: str) -> str:
    start = html.index("const strategicReplyStatus = byId('strategic-reply-status')")
    end = html.index("const strategyContextStatus = byId('strategy-context-status')", start)
    return html[start:end]


def test_product_shell_exposes_strategic_reply_workspace(client):
    html = client.get("/app").text
    for control_id in (
        "strategic-reply-workspace",
        "load-strategic-reply",
        "strategic-reply-status",
        "strategic-reply-draft",
        "copy-strategic-reply",
        "restore-strategic-reply",
        "prepare-strategic-reply-message",
        "strategic-reply-context",
        "strategic-reply-recommendations",
        "strategic-reply-constraints",
        "strategic-reply-learning",
    ):
        assert f'id="{control_id}"' in html
    assert '<textarea id="strategic-reply-draft"' in html
    assert 'href="#strategic-reply-workspace"' in html
    assert "/strategic-reply/context`" in html
    assert "Nothing was sent, saved as a message, confirmed, or executed." in html
    assert "再单独点击 Add message" in html


def test_strategic_reply_workspace_preserves_auth_and_safe_dom_boundary(client):
    html = client.get("/app").text
    assert "headers.set('Authorization', `Bearer ${requireToken()}`)" in html
    assert "currentAccessToken" in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "X-User-ID" not in html
    assert "innerHTML" not in html
    marker = 'id="load-strategic-reply" class="requires-auth"'
    assert marker in html
    assert "disabled" in html[html.index(marker): html.index(marker) + 180]


def test_strategic_reply_fragment_has_no_server_side_write_or_send(client):
    html = client.get("/app").text
    script = _strategic_reply_fragment(html)
    assert "method: 'POST'" not in script
    assert "method: 'PATCH'" not in script
    assert "method: 'DELETE'" not in script
    assert "/messages" not in script
    assert "/action-plan" not in script
    assert "/decisions" not in script
    assert "/executions" not in script
    assert "/strategic-reply/context`" in script


def test_strategic_reply_handoff_is_local_edit_and_explicit_copy(client):
    html = client.get("/app").text
    script = _strategic_reply_fragment(html)

    assert "let generatedStrategicReplyDraft = '';" in script
    assert "strategicReplyDraft.value = generatedStrategicReplyDraft;" in script
    assert "navigator.clipboard.writeText(draft)" in script
    assert "Draft edited locally. Changes are not saved or sent." in script
    assert "Generated draft restored locally. Nothing was saved or sent." in script

    copy_start = script.index("async function copyStrategicReply()")
    restore_start = script.index("function restoreStrategicReply()", copy_start)
    copy_fragment = script[copy_start:restore_start]
    assert "api(" not in copy_fragment
    assert "fetch(" not in copy_fragment
    assert "method:" not in copy_fragment

    prepare_start = script.index("function prepareStrategicReplyMessageRecord()", restore_start)
    restore_fragment = script[restore_start:prepare_start]
    assert "api(" not in restore_fragment
    assert "fetch(" not in restore_fragment
    assert "method:" not in restore_fragment


def test_strategic_reply_prepares_existing_message_composer_without_persisting(client):
    html = client.get("/app").text
    script = _strategic_reply_fragment(html)

    start = script.index("function prepareStrategicReplyMessageRecord()")
    end = script.index("const baseResetWorkspaceForStrategicReply", start)
    fragment = script[start:end]

    assert "byId('message-sender').value = 'user';" in fragment
    assert "byId('message-content').value = draft;" in fragment
    assert "byId('message-sent-at').value = '';" in fragment
    assert "then click Add message" in fragment
    assert "Add message remains a separate explicit action" in fragment
    assert "api(" not in fragment
    assert "fetch(" not in fragment
    assert "createMessage(" not in fragment
    assert "method:" not in fragment
    assert "bind('prepare-strategic-reply-message', prepareStrategicReplyMessageRecord" in script


def test_conversation_and_person_change_only_reset_strategic_reply(client):
    html = client.get("/app").text
    script = _strategic_reply_fragment(html)
    conversation_listener = script[
        script.index("byId('conversation-select').addEventListener('change'"):
        script.index("byId('person-select').addEventListener('change'")
    ]
    person_listener = script[script.index("byId('person-select').addEventListener('change'"):]
    assert "resetStrategicReply" in conversation_listener
    assert "loadStrategicReply()" not in conversation_listener
    assert "copyStrategicReply()" not in conversation_listener
    assert "prepareStrategicReplyMessageRecord()" not in conversation_listener
    assert "resetStrategicReply" in person_listener
    assert "loadStrategicReply()" not in person_listener
    assert "copyStrategicReply()" not in person_listener
    assert "prepareStrategicReplyMessageRecord()" not in person_listener


def test_real_bearer_identity_flows_into_strategic_reply_route(client, monkeypatch):
    token = _register(client, "test153-reply-user")
    user_id, person_id, conversation_id = _create_person_conversation(client, token)
    fake_service = FakeStrategicReplyService(_reply_result(person_id))
    fake_provider = FakeProvider()
    monkeypatch.setattr(analysis_strategic_reply, "service", fake_service)
    monkeypatch.setattr(analysis_strategic_reply, "QwenProvider", lambda: fake_provider)

    response = client.get(
        f"/api/v1/conversations/{conversation_id}/strategic-reply/context",
        headers=_auth(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["draft"] == "有空呀，你有什么安排？"
    assert body["structured_analysis"]["summary"] == "derived reply analysis"
    assert body["reply_constraints"]["must_not_auto_send"] is True
    assert fake_service.calls == [(user_id, conversation_id, fake_provider)]


def test_foreign_conversation_is_rejected_before_strategic_reply_generation(client):
    alice = _register(client, "test153-alice")
    bob = _register(client, "test153-bob")
    _, _, conversation_id = _create_person_conversation(client, alice)

    response = client.get(
        f"/api/v1/conversations/{conversation_id}/strategic-reply/context",
        headers=_auth(bob),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"


def test_strategic_reply_workspace_uses_existing_derived_context_fields(client):
    html = client.get("/app").text
    script = _strategic_reply_fragment(html)
    for field in (
        "data.draft",
        "data.structured_analysis",
        "data.current_state",
        "data.evidence",
        "data.recommendations",
        "data.reply_constraints",
        "data.learning_strategy",
    ):
        assert field in script
    assert "Generate explicitly when you want to call the analysis pipeline." in script
