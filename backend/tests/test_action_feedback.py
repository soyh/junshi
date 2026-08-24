from app.core.context import LOCAL_USER_ID


def create_person(client, name="反馈对象"):
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


def create_decision(client, person_id, recommendation_id=None, decision="confirmed"):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/decisions",
        json={"recommendation_id": recommendation_id, "decision": decision},
    )
    assert response.status_code == 201
    return response.json()


def create_outcome(client, person_id, decision_id, outcome="completed"):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "结果记录"},
    )
    assert response.status_code == 201
    return response.json()


def test_action_feedback_context_requires_existing_person(client):
    response = client.get("/api/v1/persons/00000000-0000-0000-0000-000000000099/action-plan/feedback/context")
    assert response.status_code == 404


def test_action_feedback_context_includes_empty_feedback(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.get(f"/api/v1/persons/{person['id']}/action-plan/feedback/context")
    assert response.status_code == 200
    body = response.json()
    assert body["person"]["id"] == person["id"]
    assert body["feedback"] == []
    assert body["feedback_constraints"]["must_not_change_relationship"] is True


def test_action_feedback_synthesizes_decision_without_outcome_as_unknown(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = create_decision(client, person["id"], decision="confirmed")
    response = client.get(f"/api/v1/persons/{person['id']}/action-plan/feedback/context")
    assert response.status_code == 200
    item = response.json()["feedback"][0]
    assert item["decision_id"] == decision["id"]
    assert item["decision"] == "confirmed"
    assert item["outcome"] is None


def test_action_feedback_synthesizes_completed_outcome(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = create_decision(client, person["id"])
    outcome = create_outcome(client, person["id"], decision["id"], "completed")
    response = client.get(f"/api/v1/persons/{person['id']}/action-plan/feedback/context")
    assert response.status_code == 200
    item = response.json()["feedback"][0]
    assert item["outcome_id"] == outcome["id"]
    assert item["outcome"] == "completed"


def test_action_feedback_preserves_failed_outcome_without_inference(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = create_decision(client, person["id"])
    create_outcome(client, person["id"], decision["id"], "failed")
    response = client.get(f"/api/v1/persons/{person['id']}/action-plan/feedback/context")
    item = response.json()["feedback"][0]
    assert item["outcome"] == "failed"
    assert response.json()["feedback_constraints"]["must_preserve_unknowns"] is True


def test_action_feedback_preserves_skipped_outcome(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = create_decision(client, person["id"])
    create_outcome(client, person["id"], decision["id"], "skipped")
    response = client.get(f"/api/v1/persons/{person['id']}/action-plan/feedback/context")
    assert response.json()["feedback"][0]["outcome"] == "skipped"


def test_action_feedback_isolated_by_person(client):
    first = create_person(client, "对象A")
    second = create_person(client, "对象B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = create_decision(client, first["id"])
    create_outcome(client, first["id"], decision["id"])
    response = client.get(f"/api/v1/persons/{second['id']}/action-plan/feedback/context")
    assert response.status_code == 200
    assert response.json()["feedback"] == []


def test_action_feedback_is_read_only(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = create_decision(client, person["id"])
    create_outcome(client, person["id"], decision["id"])
    first = client.get(f"/api/v1/persons/{person['id']}/action-plan/feedback/context").json()
    second = client.get(f"/api/v1/persons/{person['id']}/action-plan/feedback/context").json()
    assert first == second
