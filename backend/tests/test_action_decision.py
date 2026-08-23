from app.services.action_decision import ActionDecisionService


def create_person(client, name="行动确认测试对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201
    return response.json()


def get_context(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/action-plan/decisions/context")


def test_action_decision_context_has_locked_confirmation_contract(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"])
    response = get_context(client, person["id"])
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"person", "relationship", "action_plan", "action_constraints", "decisions"}
    assert body["person"]["id"] == person["id"]
    assert body["relationship"]["id"] == relationship["id"]
    assert body["action_plan"] == []
    assert body["decisions"] == []
    assert body["action_constraints"] == {
        "must_be_evidence_backed": True,
        "must_preserve_unknowns": True,
        "requires_user_confirmation": True,
        "must_not_auto_execute": True,
        "must_not_change_relationship": True,
        "must_record_user_decision": True,
    }


def test_action_decision_context_missing_relationship_returns_404(client):
    person = create_person(client)
    assert get_context(client, person["id"]).status_code == 404


def test_action_decision_context_isolated_by_user(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/decisions/context",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_rejected_decision_can_be_recorded_without_execution(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/decisions",
        json={"decision": "rejected", "note": "暂不执行"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["person_id"] == person["id"]
    assert body["decision"] == "rejected"
    assert body["recommendation_id"] is None


def test_confirmed_decision_requires_recommendation_id(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/decisions",
        json={"decision": "confirmed"},
    )
    assert response.status_code == 409


def test_decision_history_is_deterministically_ordered(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    for note in ["first", "second"]:
        response = client.post(
            f"/api/v1/persons/{person['id']}/action-plan/decisions",
            json={"decision": "rejected", "note": note},
        )
        assert response.status_code == 201
    decisions = get_context(client, person["id"]).json()["decisions"]
    assert [item["note"] for item in decisions] == ["second", "first"]


def test_decision_cannot_reference_unavailable_recommendation(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/decisions",
        json={"decision": "confirmed", "recommendation_id": "missing"},
    )
    assert response.status_code == 409


def test_service_requires_confirmed_decisions_to_name_an_action():
    class FakeActionPlanService:
        def get_context(self, conn, user_id, person_id):
            return {"person": {"id": person_id}, "relationship": {"id": "rel"}, "action_plan": []}

    service = ActionDecisionService(action_plan_service=FakeActionPlanService())
    try:
        service.create_decision(None, "u", "p", None, "confirmed", None)
    except ValueError as exc:
        assert str(exc) == "confirmed decision requires recommendation_id"
    else:
        raise AssertionError("expected ValueError")
