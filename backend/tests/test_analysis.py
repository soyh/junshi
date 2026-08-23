def _analysis_test_person(client, name="Analysis对象"):
    response = client.post(
        "/api/v1/persons",
        json={"name": name},
    )
    assert response.status_code == 201
    return response.json()


def test_analysis_context_contains_person_conversation_and_messages(client):
    person = _analysis_test_person(client)

    conversation_response = client.post(
        "/api/v1/conversations",
        json={
            "person_id": person["id"],
            "title": "分析测试",
        },
    )
    assert conversation_response.status_code == 201
    conversation = conversation_response.json()

    first_message = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation["id"],
            "sender_type": "user",
            "content": "你好",
            "sent_at": "2026-08-23T10:00:00+00:00",
        },
    )
    second_message = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation["id"],
            "sender_type": "person",
            "content": "你好呀",
            "sent_at": "2026-08-23T10:01:00+00:00",
        },
    )
    assert first_message.status_code == 201
    assert second_message.status_code == 201

    response = client.get(
        f"/api/v1/conversations/{conversation['id']}/analysis/context"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["conversation"]["id"] == conversation["id"]
    assert body["conversation"]["person_id"] == person["id"]
    assert body["person"]["id"] == person["id"]
    assert [message["content"] for message in body["messages"]] == [
        "你好",
        "你好呀",
    ]
    assert [message["conversation_id"] for message in body["messages"]] == [
        conversation["id"],
        conversation["id"],
    ]


def test_analysis_context_has_no_inferred_or_recommended_content(client):
    person = _analysis_test_person(client)
    conversation = client.post(
        "/api/v1/conversations",
        json={"person_id": person["id"]},
    ).json()

    response = client.get(
        f"/api/v1/conversations/{conversation['id']}/analysis/context"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["facts"] == []
    assert body["inferences"] == []
    assert body["unknowns"] == []
    assert body["recommendations"] == []


def test_analysis_context_enforces_user_isolation(client):
    person = _analysis_test_person(client)
    conversation = client.post(
        "/api/v1/conversations",
        json={"person_id": person["id"]},
    ).json()

    from app.api.routes import analysis as analysis_routes

    original_service = analysis_routes.service

    class OtherUserService:
        def get_context(self, conn, user_id, conversation_id):
            return original_service.get_context(
                conn,
                "00000000-0000-0000-0000-000000000002",
                conversation_id,
            )

    analysis_routes.service = OtherUserService()
    try:
        response = client.get(
            f"/api/v1/conversations/{conversation['id']}/analysis/context"
        )
    finally:
        analysis_routes.service = original_service

    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found"}


def test_analysis_context_missing_conversation_returns_404(client):
    response = client.get(
        "/api/v1/conversations/00000000-0000-0000-0000-000000000099/analysis/context"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found"}
