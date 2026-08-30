from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository

USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="策略确认合成对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201


def seed_decision(person_id, recommendation_id):
    with get_connection() as conn:
        return ActionDecisionRepository.create(
            conn, USER_ID, person_id, recommendation_id, "confirmed", "合成测试"
        )


def create_outcome(client, person_id, decision_id):
    execution = client.post(
        f"/api/v1/persons/{person_id}/strategy-decision/executions/{decision_id}",
        json={"note": "测试执行"},
    )
    assert execution.status_code == 201

    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": "completed", "note": "合成测试结果"},
    )
    assert response.status_code == 201


def create_confirmation(client, person_id, recommendation_id, decision):
    response = client.post(
        f"/api/v1/persons/{person_id}/strategy-decision/confirmations",
        json={"recommendation_id": recommendation_id, "decision": decision},
    )
    assert response.status_code == 201
    return response.json()


def get_synthesis(client, person_id):
    return client.get(
        f"/api/v1/persons/{person_id}/strategy-decision/confirmation-synthesis"
    )


def test_confirmation_synthesis_counts_confirmed_and_rejected(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    first = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], first["id"])
    second = seed_decision(person["id"], "recommendation-b")
    create_outcome(client, person["id"], second["id"])
    create_confirmation(client, person["id"], "recommendation-a", "confirmed")
    create_confirmation(client, person["id"], "recommendation-b", "rejected")
    body = get_synthesis(client, person["id"]).json()
    assert body["confirmation_summary"]["confirmed_count"] == 1
    assert body["confirmation_summary"]["rejected_count"] == 1
    assert body["confirmed_recommendation_ids"] == ["recommendation-a"]
    assert body["rejected_recommendation_ids"] == ["recommendation-b"]


def test_confirmation_synthesis_is_empty_without_decisions(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    body = get_synthesis(client, person["id"]).json()
    assert body["confirmation_summary"]["decision_count"] == 0
    assert body["confirmation_summary"]["latest_decision_id"] is None
    assert body["confirmed_recommendation_ids"] == []
    assert body["rejected_recommendation_ids"] == []


def test_confirmation_synthesis_tracks_latest_decision(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    first = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], first["id"])
    second = seed_decision(person["id"], "recommendation-b")
    create_outcome(client, person["id"], second["id"])
    create_confirmation(client, person["id"], "recommendation-a", "confirmed")
    latest = create_confirmation(client, person["id"], "recommendation-b", "rejected")
    body = get_synthesis(client, person["id"]).json()
    assert body["confirmation_summary"]["latest_decision_id"] == latest["id"]


def test_confirmation_synthesis_never_marks_execution_ready(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    body = get_synthesis(client, person["id"]).json()
    assert body["execution"]["ready"] is False
    assert body["execution"]["execution_is_automatic"] is False
    assert body["execution"]["requires_explicit_execution_step"] is True
    assert body["confirmation_constraints"]["must_not_send_from_confirmation"] is True


def test_confirmation_synthesis_is_person_isolated(client):
    first = create_person(client, "合成A")
    second = create_person(client, "合成B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"], "recommendation-a")
    create_outcome(client, first["id"], decision["id"])
    create_confirmation(client, first["id"], "recommendation-a", "confirmed")
    body = get_synthesis(client, second["id"]).json()
    assert body["confirmation_summary"]["decision_count"] == 0


def test_confirmation_synthesis_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/strategy-decision/confirmation-synthesis",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_confirmation_synthesis_is_deterministic(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"])
    create_confirmation(client, person["id"], "recommendation-a", "confirmed")
    first = get_synthesis(client, person["id"]).json()
    second = get_synthesis(client, person["id"]).json()
    assert first == second


def test_confirmation_synthesis_preserves_constraints(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    body = get_synthesis(client, person["id"]).json()
    constraints = body["confirmation_constraints"]
    assert constraints["must_record_user_decision"] is True
    assert constraints["must_not_auto_confirm"] is True
    assert constraints["must_not_auto_execute"] is True
    assert constraints["must_not_execute_from_confirmation"] is True
