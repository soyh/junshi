from app.services.action_outcome import ActionOutcomeService


def create_person(client, name="行动结果测试对象"):
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


def test_action_outcome_history_is_empty_before_execution(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.get(f"/api/v1/persons/{person['id']}/action-plan/outcomes")
    assert response.status_code == 200
    assert response.json() == []


def test_action_outcome_cannot_reference_missing_decision(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes/missing",
        json={"outcome": "completed"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "action decision not found"


def test_action_outcome_requires_confirmed_decision():
    class FakeDecisionRepository:
        def get(self, conn, user_id, person_id, decision_id):
            return {"id": decision_id, "decision": "rejected"}

    service = ActionOutcomeService(decision_repository=FakeDecisionRepository())
    try:
        service.create_outcome(None, "u", "p", "d", "completed", None)
    except ValueError as exc:
        assert str(exc) == "outcome requires a confirmed action decision"
    else:
        raise AssertionError("expected ValueError")


def test_action_outcome_accepts_confirmed_decision():
    class FakeDecisionRepository:
        def get(self, conn, user_id, person_id, decision_id):
            return {"id": decision_id, "decision": "confirmed"}

    class FakeOutcomeRepository:
        def create(self, conn, user_id, person_id, decision_id, outcome, note):
            return {
                "id": "outcome-1",
                "user_id": user_id,
                "person_id": person_id,
                "decision_id": decision_id,
                "outcome": outcome,
                "note": note,
                "created_at": "2026-08-24T00:00:00+00:00",
            }

    service = ActionOutcomeService(FakeDecisionRepository(), FakeOutcomeRepository())
    result = service.create_outcome(None, "u", "p", "d", "completed", "done")
    assert result["decision_id"] == "d"
    assert result["outcome"] == "completed"
    assert result["note"] == "done"


def test_action_outcome_service_preserves_all_outcome_states():
    class FakeDecisionRepository:
        def get(self, conn, user_id, person_id, decision_id):
            return {"id": decision_id, "decision": "confirmed"}

    class FakeOutcomeRepository:
        def create(self, conn, user_id, person_id, decision_id, outcome, note):
            return {"outcome": outcome, "decision_id": decision_id}

    service = ActionOutcomeService(FakeDecisionRepository(), FakeOutcomeRepository())
    for state in ("completed", "skipped", "failed"):
        assert service.create_outcome(None, "u", "p", "d", state, None)["outcome"] == state


def test_action_outcome_history_isolated_by_user(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 200
    assert response.json() == []


def test_action_outcome_validation_rejects_unknown_state(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes/missing",
        json={"outcome": "unknown"},
    )
    assert response.status_code == 422
