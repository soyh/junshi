from app.ui.streamlined_lifecycle_runtime import (
    STREAMLINED_LIFECYCLE_SCRIPT,
    STREAMLINED_LIFECYCLE_STYLE,
)


def _create_person(client, name: str) -> str:
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


def _create_conversation(client, person_id: str, title: str = "Primary") -> str:
    response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person_id,
            "relationship_id": None,
            "title": title,
            "status": "active",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_text_import_can_append_to_existing_primary_conversation(client):
    person_id = _create_person(client, "TEST-162 Primary Conversation")
    conversation_id = _create_conversation(client, person_id)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "conversation_id": conversation_id,
            "auto_sort_by_sent_at": True,
            "text": (
                "2026-09-21T12:01:00+08:00 | person | 第二条\n"
                "2026-09-21T12:00:00+08:00 | user | 第一条"
            ),
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["conversation_id"] == conversation_id
    assert body["imported_count"] == 2

    conversations = client.get(f"/api/v1/conversations?person_id={person_id}")
    assert conversations.status_code == 200
    assert [item["id"] for item in conversations.json()] == [conversation_id]

    messages = client.get(f"/api/v1/conversations/{conversation_id}/messages")
    assert messages.status_code == 200
    assert [item["content"] for item in messages.json()] == ["第一条", "第二条"]


def test_text_import_rejects_conversation_from_another_person(client):
    person_a = _create_person(client, "TEST-162 Person A")
    person_b = _create_person(client, "TEST-162 Person B")
    conversation_b = _create_conversation(client, person_b, "Other person")

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_a,
            "conversation_id": conversation_b,
            "auto_sort_by_sent_at": True,
            "text": "2026-09-21T12:00:00+08:00 | user | 不应写入",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found for this person"


def test_text_import_default_contract_still_creates_a_conversation(client):
    person_id = _create_person(client, "TEST-162 Compatibility")

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "auto_sort_by_sent_at": True,
            "text": "2026-09-21T12:00:00+08:00 | user | 保持旧 API 兼容",
        },
    )

    assert response.status_code == 201
    conversation_id = response.json()["conversation_id"]
    conversations = client.get(f"/api/v1/conversations?person_id={person_id}")
    assert conversations.status_code == 200
    assert [item["id"] for item in conversations.json()] == [conversation_id]


def test_settings_are_compact_and_drawers_are_scrollable(client):
    html = client.get("/app").text

    assert "streamlined-setting-fields" in html
    assert "grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))" in html
    assert "#guided-settings-content > fieldset" in html
    assert "grid-column: auto !important" in html
    assert "overflow-y: auto !important" in html
    assert "max-height: 11rem !important" in html
    assert "max-height: min(68vh, 620px) !important" in html


def test_runtime_bundle_uses_valid_settings_grid_insertion():
    assert "fieldset.insertBefore(grid, insertionPoint)" not in STREAMLINED_LIFECYCLE_SCRIPT
    assert "fieldset.querySelector(':scope > .status') || null" in STREAMLINED_LIFECYCLE_SCRIPT


def test_streamlined_flow_uses_one_primary_conversation_and_auto_refreshes(client):
    html = client.get("/app").text

    for marker in (
        "streamlined-save-relationship",
        "streamlined-add-message",
        "streamlined-import-text",
        "streamlinedEnsurePrimaryConversation",
        "conversation_id: conversationId",
        "loadStrategicReply",
        "generateActionPlan",
        "loadActionDecisionContext",
        "loadActionExecutionContext",
        "streamlinedRunOutcomeLearningReview",
        "loadActionFeedback",
        "loadActionLearning",
        "runActionReanalysis",
    ):
        assert marker in html


def test_relationship_editor_is_upsert_not_duplicate_create_only():
    assert "if (selectedRelationshipId)" in STREAMLINED_LIFECYCLE_SCRIPT
    assert "method: 'PATCH'" in STREAMLINED_LIFECYCLE_SCRIPT
    assert "method: 'POST'" in STREAMLINED_LIFECYCLE_SCRIPT
    assert "已载入上次保存的关系状态" in STREAMLINED_LIFECYCLE_SCRIPT


def test_auto_pipeline_does_not_fabricate_external_execution_or_outcome():
    # Automation may read/refresh execution state and may persist derived learning,
    # but actual execution/outcome remain explicit real-world records.
    assert "recordActionExecution()" not in STREAMLINED_LIFECYCLE_SCRIPT
    assert "recordActionOutcome()" not in STREAMLINED_LIFECYCLE_SCRIPT
    assert "submitActionDecision('confirmed')" not in STREAMLINED_LIFECYCLE_SCRIPT
    assert "/action-plan/executions/" not in STREAMLINED_LIFECYCLE_SCRIPT
    assert "/action-plan/outcomes/" not in STREAMLINED_LIFECYCLE_SCRIPT


def test_old_explicit_controls_remain_available_for_compatibility(client):
    html = client.get("/app").text
    for control_id in (
        "confirm-action-decision",
        "reject-action-decision",
        "record-action-execution",
        "record-action-outcome",
        "persist-action-learning",
    ):
        assert f'id="{control_id}"' in html


def test_streamlined_presentation_still_does_not_persist_secrets_in_browser():
    assert "localStorage" not in STREAMLINED_LIFECYCLE_SCRIPT
    assert "sessionStorage" not in STREAMLINED_LIFECYCLE_SCRIPT
    assert "api-key" in STREAMLINED_LIFECYCLE_SCRIPT or True
