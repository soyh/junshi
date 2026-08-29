def create_person(client, name="分析证据对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={
            "person_id": person_id,
            "status": "active",
            "stage": "dating",
            "long_term_goal": "建立长期关系",
            "current_goal": "增加互动",
            "notes": "canonical evidence bridge",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_conversation(client, person_id):
    response = client.post(
        "/api/v1/conversations",
        json={"person_id": person_id, "title": "分析证据会话", "status": "active"},
    )
    assert response.status_code == 201
    return response.json()


def test_analysis_context_reuses_canonical_evidence_buckets(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"])
    conversation = create_conversation(client, person["id"])

    message = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation["id"],
            "sender_type": "person",
            "content": "今天见面了",
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

    state = client.get(f"/api/v1/persons/{person['id']}/relationship-analysis/state")
    analysis = client.get(f"/api/v1/conversations/{conversation['id']}/analysis/context")
    assert state.status_code == 200
    assert analysis.status_code == 200

    state_body = state.json()
    analysis_body = analysis.json()
    assert analysis_body["facts"] == state_body["facts"]
    assert analysis_body["inferences"] == state_body["inferences"]
    assert analysis_body["unknowns"] == state_body["unknowns"]
    assert analysis_body["relationship_state"]["facts"] == state_body["facts"]
    assert analysis_body["relationship_state"]["inferences"] == state_body["inferences"]
    assert analysis_body["relationship_state"]["unknowns"] == state_body["unknowns"]


def test_analysis_context_does_not_promote_recommendations_from_relationship_state(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    conversation = create_conversation(client, person["id"])

    response = client.get(f"/api/v1/conversations/{conversation['id']}/analysis/context")
    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"] == []
    assert body["relationship_state"]["recommendations"] == []


def test_analysis_context_keeps_canonical_evidence_buckets_empty_without_relationship(client):
    person = create_person(client)
    conversation = create_conversation(client, person["id"])

    response = client.get(f"/api/v1/conversations/{conversation['id']}/analysis/context")
    assert response.status_code == 200
    body = response.json()
    assert body["facts"] == []
    assert body["inferences"] == []
    assert body["unknowns"] == []
    assert body["recommendations"] == []
