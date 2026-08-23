def create_person(client, name="建议测试对象"):
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
        "notes": "recommendation test",
    }
    payload.update(overrides)
    response = client.post("/api/v1/relationships", json=payload)
    assert response.status_code == 201
    return response.json()


def test_recommendation_context_returns_evidence_backed_input_and_empty_recommendations(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"], stage="exclusive")
    response = client.get(f"/api/v1/persons/{person['id']}/recommendation-analysis/context")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "person",
        "relationship",
        "current_state",
        "evidence",
        "facts",
        "inferences",
        "unknowns",
        "recommendations",
    }
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


def test_recommendation_context_reuses_relationship_state_evidence(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"])
    interaction = client.post(
        "/api/v1/interactions",
        json={
            "person_id": person["id"],
            "relationship_id": relationship["id"],
            "type": "meeting",
            "occurred_at": "2026-08-23T10:00:00+00:00",
            "content": "一起吃饭",
        },
    )
    assert interaction.status_code == 201
    response = client.get(f"/api/v1/persons/{person['id']}/recommendation-analysis/context")
    assert response.status_code == 200
    evidence = response.json()["evidence"]
    assert len(evidence) == 1
    assert evidence[0]["source_type"] == "interaction"
    assert evidence[0]["source_id"] == interaction.json()["id"]
    assert response.json()["facts"] == []
    assert response.json()["inferences"] == []
    assert response.json()["unknowns"] == []
    assert response.json()["recommendations"] == []


def test_recommendation_context_is_deterministically_ordered(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"])
    later = client.post(
        "/api/v1/interactions",
        json={
            "person_id": person["id"],
            "relationship_id": relationship["id"],
            "type": "call",
            "occurred_at": "2026-08-23T12:00:00+00:00",
            "content": "晚事件",
        },
    )
    earlier = client.post(
        "/api/v1/interactions",
        json={
            "person_id": person["id"],
            "relationship_id": relationship["id"],
            "type": "message",
            "occurred_at": "2026-08-23T10:00:00+00:00",
            "content": "早事件",
        },
    )
    assert later.status_code == 201
    assert earlier.status_code == 201
    response = client.get(f"/api/v1/persons/{person['id']}/recommendation-analysis/context")
    assert response.status_code == 200
    assert [item["source_id"] for item in response.json()["evidence"]] == [earlier.json()["id"], later.json()["id"]]


def test_recommendation_context_isolated_by_user(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/recommendation-analysis/context",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_recommendation_context_does_not_mix_other_person_evidence(client):
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
    response = client.get(f"/api/v1/persons/{first['id']}/recommendation-analysis/context")
    assert response.status_code == 200
    assert response.json()["evidence"] == []


def test_recommendation_context_is_read_only(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"])
    before = client.get(f"/api/v1/persons/{person['id']}/recommendation-analysis/context")
    after = client.get(f"/api/v1/persons/{person['id']}/recommendation-analysis/context")
    assert before.status_code == 200
    assert after.status_code == 200
    assert after.json() == before.json()
    assert after.json()["relationship"]["id"] == relationship["id"]


def test_recommendation_context_reflects_deleted_source(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"])
    interaction = client.post(
        "/api/v1/interactions",
        json={
            "person_id": person["id"],
            "relationship_id": relationship["id"],
            "type": "meeting",
            "occurred_at": "2026-08-23T12:00:00+00:00",
            "content": "将被删除",
        },
    )
    assert interaction.status_code == 201
    deleted = client.delete(f"/api/v1/interactions/{interaction.json()['id']}")
    assert deleted.status_code == 204
    response = client.get(f"/api/v1/persons/{person['id']}/recommendation-analysis/context")
    assert response.status_code == 200
    assert response.json()["evidence"] == []
    assert response.json()["recommendations"] == []


def test_recommendation_context_missing_person_returns_404(client):
    response = client.get("/api/v1/persons/99999999-9999-9999-9999-999999999999/recommendation-analysis/context")
    assert response.status_code == 404


def test_recommendation_context_without_relationship_returns_404(client):
    person = create_person(client)
    response = client.get(f"/api/v1/persons/{person['id']}/recommendation-analysis/context")
    assert response.status_code == 404
