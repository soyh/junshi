from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


def create_person(client, name="学习综合对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201


def seed_decision(person_id, recommendation_id, decision="confirmed"):
    with get_connection() as conn:
        return ActionDecisionRepository.create(
            conn,
            "00000000-0000-0000-0000-000000000001",
            person_id,
            recommendation_id,
            decision,
            "用户决策",
        )


def create_outcome(client, person_id, decision_id, outcome):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "结果已记录"},
    )
    assert response.status_code == 201


def get_synthesis(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/action-plan/feedback/learning-synthesis")


def test_learning_synthesis_creates_source_backed_candidate(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"], "completed")
    response = get_synthesis(client, person["id"])
    assert response.status_code == 200
    candidate = response.json()["candidates"][0]
    assert candidate["recommendation_id"] == "recommendation-a"
    assert candidate["synthesis_status"] == "source_backed_candidate"
    assert candidate["observed_outcome_count"] == 1


def test_learning_synthesis_keeps_unknown_as_unknown(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"], "recommendation-a", "rejected")
    candidate = get_synthesis(client, person["id"]).json()["candidates"][0]
    assert candidate["synthesis_status"] == "outcome_unknown"
    assert candidate["unknown_outcome_count"] == 1
    assert "relationship_impact" in candidate["unknowns"]


def test_learning_synthesis_preserves_outcome_counts(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    first = seed_decision(person["id"], "recommendation-a")
    second = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], first["id"], "completed")
    create_outcome(client, person["id"], second["id"], "failed")
    candidate = get_synthesis(client, person["id"]).json()["candidates"][0]
    assert candidate["outcome_counts"] == {"completed": 1, "skipped": 0, "failed": 1}


def test_learning_synthesis_is_deterministic(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-b")
    create_outcome(client, person["id"], decision["id"], "skipped")
    first = get_synthesis(client, person["id"]).json()
    second = get_synthesis(client, person["id"]).json()
    assert first == second


def test_learning_synthesis_is_person_isolated(client):
    first = create_person(client, "第一个综合对象")
    second = create_person(client, "第二个综合对象")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"], "recommendation-a")
    create_outcome(client, first["id"], decision["id"], "completed")
    assert get_synthesis(client, second["id"]).json()["candidates"] == []


def test_learning_synthesis_exposes_non_inference_constraints(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    constraints = get_synthesis(client, person["id"]).json()["synthesis_constraints"]
    assert constraints["must_be_source_backed"] is True
    assert constraints["must_preserve_unknowns"] is True
    assert constraints["must_not_infer_recommendation_quality"] is True
    assert constraints["must_not_infer_success"] is True
    assert constraints["must_not_infer_relationship_impact"] is True


def test_learning_synthesis_is_read_only_and_execution_separate(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"], "recommendation-a")
    before = get_synthesis(client, person["id"]).json()
    after = get_synthesis(client, person["id"]).json()
    assert before == after
    assert before["synthesis_constraints"]["must_not_auto_execute"] is True
    assert before["synthesis_constraints"]["must_not_call_llm"] is True
