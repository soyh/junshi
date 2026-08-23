def create_person(client, name="状态测试对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id, **overrides):
    payload = {
        "person_id": person_id,
        "status": "active",
        "stage": "dating",
        "long_term_goal": "建立长期关系",
        "current_goal": "增加互动",
        "notes": "state test",
    }
    payload.update(overrides)
    response = client.post("/api/v1/relationships", json=payload)
    assert response.status_code == 201
    return response.json()


def test_relationship_state_returns_persisted_state_and_empty_analysis_buckets(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"], status="active", stage="exclusive")

    response = client.get(f"/api/v1/persons/{person['id']}/relationship-analysis/state")

    assert response.status_code == 200
    body = response.json()
    assert body["person"]["id"] == person["id"]
    assert body["relationship"]["id"] == relationship["id"]
    assert body["current_state"] == {
        "status": "active",
        "stage": "exclusive",
        "long_term_goal": "建立长期关系",
        "current_goal": "增加互动",
    }
    assert body["evidence"] == []
    assert body["facts"] == []
    assert body["inferences"] == []
    assert body["unknowns"] == []
    assert body["recommendations"] == []


def test_relationship_state_aggregates_message_and_interaction_evidence(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"])
    conversation = client.post(
        "/api/v1/conversations",
        json={"person_id": person["id"], "title": "状态分析会话", "status": "active"},
    )
    assert conversation.status_code == 201
    conversation_id = conversation.json()["id"]

    message = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation_id,
            "sender_type": "person",
            "content": "最近工作比较忙",
            "sent_at": "2026-08-23T10:00:00+00:00",
        },
    )
    interaction = client.post(
        "/api/v1/interactions",
        json={
            "person_id": person["id"],
            "relationship_id": relationship["id"],
            "type": "meeting",
            "occurred_at": "2026-08-23T11:00:00+00:00",
            "content": "线下见面",
        },
    )
    assert message.status_code == 201
    assert interaction.status_code == 201

    response = client.get(f"/api/v1/persons/{person['id']}/relationship-analysis/state")

    assert response.status_code == 200
    evidence = response.json()["evidence"]
    assert [item["source_type"] for item in evidence] == ["message", "interaction"]
    assert evidence[0]["source_id"] == message.json()["id"]
    assert evidence[1]["source_id"] == interaction.json()["id"]
    assert evidence[0]["conversation_id"] == conversation_id
    assert evidence[1]["conversation_id"] is None


def test_relationship_state_evidence_is_deterministically_ordered(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"])
    first = client.post(
        "/api/v1/interactions",
        json={
            "person_id": person["id"],
            "relationship_id": relationship["id"],
            "type": "call",
            "occurred_at": "2026-08-23T12:00:00+00:00",
            "content": "较晚事件",
        },
    )
    second = client.post(
        "/api/v1/interactions",
        json={
            "person_id": person["id"],
            "relationship_id": relationship["id"],
            "type": "message",
            "occurred_at": "2026-08-23T10:00:00+00:00",
            "content": "较早事件",
        },
    )
    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(f"/api/v1/persons/{person['id']}/relationship-analysis/state")

    assert response.status_code == 200
    evidence = response.json()["evidence"]
    assert [item["source_id"] for item in evidence] == [second.json()["id"], first.json()["id"]]


def test_relationship_state_isolated_by_user(client):
    person = create_person(client)
    create_relationship(client, person["id"])

    response = client.get(
        f"/api/v1/persons/{person['id']}/relationship-analysis/state",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )

    assert response.status_code == 404


def test_relationship_state_does_not_mix_other_person_evidence(client):
    first = create_person(client, "对象A")
    second = create_person(client, "对象B")
    create_relationship(client, first["id"])
    second_relationship = create_relationship(client, second["id"])
    interaction = client.post(
        "/api/v1/interactions",
        json={
            "person_id": second["id"],
            "relationship_id": second_relationship["id"],
            "type": "meeting",
            "occurred_at": "2026-08-23T12:00:00+00:00",
            "content": "只属于对象B",
        },
    )
    assert interaction.status_code == 201

    response = client.get(f"/api/v1/persons/{first['id']}/relationship-analysis/state")

    assert response.status_code == 200
    assert response.json()["evidence"] == []


def test_relationship_state_is_read_only(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"])

    before = client.get(f"/api/v1/persons/{person['id']}/relationship-analysis/state")
    after = client.get(f"/api/v1/persons/{person['id']}/relationship-analysis/state")

    assert before.status_code == 200
    assert after.status_code == 200
    assert after.json() == before.json()
    assert after.json()["relationship"]["id"] == relationship["id"]


def test_relationship_state_missing_person_returns_404(client):
    response = client.get(
        "/api/v1/persons/99999999-9999-9999-9999-999999999999/relationship-analysis/state"
    )
    assert response.status_code == 404


def test_relationship_state_without_relationship_returns_404(client):
    person = create_person(client)
    response = client.get(f"/api/v1/persons/{person['id']}/relationship-analysis/state")
    assert response.status_code == 404
