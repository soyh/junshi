def create_person(client, name="策略回复测试对象"):
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
        "notes": "strategic reply test",
    }
    payload.update(overrides)
    response = client.post("/api/v1/relationships", json=payload)
    assert response.status_code == 201
    return response.json()


def get_context(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/strategic-reply/context")


def test_strategic_reply_context_locks_response_shape_and_constraints(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"], stage="exclusive")
    response = get_context(client, person["id"])
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
        "reply_constraints",
        "draft",
    }
    assert body["person"]["id"] == person["id"]
    assert body["relationship"]["id"] == relationship["id"]
    assert body["draft"] is None
    assert body["reply_constraints"] == {
        "must_be_evidence_backed": True,
        "must_preserve_unknowns": True,
        "must_not_auto_send": True,
        "must_not_change_relationship": True,
    }


def test_strategic_reply_context_reuses_recommendation_analysis_buckets(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = get_context(client, person["id"])
    assert response.status_code == 200
    body = response.json()
    assert body["facts"] == []
    assert body["inferences"] == []
    assert body["unknowns"] == []
    assert body["recommendations"] == []


def test_strategic_reply_context_preserves_evidence_order(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"])
    later = client.post("/api/v1/interactions", json={
        "person_id": person["id"], "relationship_id": relationship["id"],
        "type": "call", "occurred_at": "2026-08-23T12:00:00+00:00", "content": "晚",
    })
    earlier = client.post("/api/v1/interactions", json={
        "person_id": person["id"], "relationship_id": relationship["id"],
        "type": "message", "occurred_at": "2026-08-23T10:00:00+00:00", "content": "早",
    })
    assert later.status_code == 201
    assert earlier.status_code == 201
    response = get_context(client, person["id"])
    assert response.status_code == 200
    assert [item["source_id"] for item in response.json()["evidence"]] == [earlier.json()["id"], later.json()["id"]]


def test_strategic_reply_context_isolated_by_user(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/strategic-reply/context",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_strategic_reply_context_does_not_mix_other_person_data(client):
    first = create_person(client, "对象A")
    second = create_person(client, "对象B")
    create_relationship(client, first["id"])
    second_relationship = create_relationship(client, second["id"])
    interaction = client.post("/api/v1/interactions", json={
        "person_id": second["id"], "relationship_id": second_relationship["id"],
        "type": "meeting", "occurred_at": "2026-08-23T12:00:00+00:00", "content": "B",
    })
    assert interaction.status_code == 201
    response = get_context(client, first["id"])
    assert response.status_code == 200
    assert response.json()["evidence"] == []


def test_strategic_reply_context_is_read_only(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"])
    before = get_context(client, person["id"])
    after = get_context(client, person["id"])
    assert before.status_code == 200
    assert after.status_code == 200
    assert after.json() == before.json()
    assert after.json()["relationship"]["id"] == relationship["id"]


def test_strategic_reply_context_reflects_deleted_evidence(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"])
    interaction = client.post("/api/v1/interactions", json={
        "person_id": person["id"], "relationship_id": relationship["id"],
        "type": "meeting", "occurred_at": "2026-08-23T12:00:00+00:00", "content": "删除",
    })
    assert interaction.status_code == 201
    deleted = client.delete(f"/api/v1/interactions/{interaction.json()['id']}")
    assert deleted.status_code == 204
    response = get_context(client, person["id"])
    assert response.status_code == 200
    assert response.json()["evidence"] == []


def test_strategic_reply_context_missing_person_returns_404(client):
    response = get_context(client, "99999999-9999-9999-9999-999999999999")
    assert response.status_code == 404


def test_strategic_reply_context_without_relationship_returns_404(client):
    person = create_person(client)
    response = get_context(client, person["id"])
    assert response.status_code == 404
