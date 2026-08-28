from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="分析学习策略对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201


def create_conversation(client, person_id):
    response = client.post(
        "/api/v1/conversations",
        json={"person_id": person_id, "title": "分析学习策略会话"},
    )
    assert response.status_code == 201
    return response.json()


def seed_decision(person_id, recommendation_id="analysis-recommendation"):
    with get_connection() as conn:
        return ActionDecisionRepository.create(
            conn,
            USER_ID,
            person_id,
            recommendation_id,
            "confirmed",
            "分析学习策略测试决策",
        )


def create_outcome(client, person_id, decision_id):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": "completed", "note": "分析学习策略测试结果"},
    )
    assert response.status_code == 201


def test_analysis_context_exposes_learning_strategy_bridge(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    conversation = create_conversation(client, person["id"])

    response = client.get(f"/api/v1/conversations/{conversation['id']}/analysis/context")

    assert response.status_code == 200
    body = response.json()
    assert set(body["learning_strategy"]) == {"learning_inputs", "strategy_constraints"}
    assert body["learning_strategy"]["learning_inputs"]["action_feedback"] == []
    assert body["learning_strategy"]["learning_inputs"]["memory_updates"] == []
    assert body["learning_strategy"]["learning_inputs"]["strategy_decision"]["items"] == []
    assert body["learning_strategy"]["strategy_constraints"]["must_preserve_source_provenance"] is True
    assert body["learning_strategy"]["strategy_constraints"]["must_preserve_unknowns"] is True


def test_analysis_context_learning_strategy_matches_person_context(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    conversation = create_conversation(client, person["id"])
    decision = seed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])

    analysis = client.get(f"/api/v1/conversations/{conversation['id']}/analysis/context")
    strategy = client.get(f"/api/v1/persons/{person['id']}/learning-strategy/context")

    assert analysis.status_code == 200
    assert strategy.status_code == 200
    assert analysis.json()["learning_strategy"] == {
        "learning_inputs": strategy.json()["learning_inputs"],
        "strategy_constraints": strategy.json()["strategy_constraints"],
    }


def test_analysis_context_learning_strategy_preserves_source_provenance_and_unknowns(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    conversation = create_conversation(client, person["id"])
    decision = seed_decision(person["id"], "analysis-observed")
    create_outcome(client, person["id"], decision["id"])

    body = client.get(f"/api/v1/conversations/{conversation['id']}/analysis/context").json()
    strategy_decision = body["learning_strategy"]["learning_inputs"]["strategy_decision"]

    assert strategy_decision["items"][0]["source"]["decision_id"] == decision["id"]
    assert strategy_decision["items"][0]["source"]["recommendation_id"] == "analysis-observed"
    assert strategy_decision["items"][0]["unknowns"] == []
    assert body["learning_strategy"]["strategy_constraints"]["must_preserve_source_provenance"] is True
    assert body["learning_strategy"]["strategy_constraints"]["must_preserve_learning_unknowns"] is True


def test_analysis_context_learning_strategy_is_user_isolated(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    conversation = create_conversation(client, person["id"])

    response = client.get(
        f"/api/v1/conversations/{conversation['id']}/analysis/context",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )

    assert response.status_code == 404


def test_analysis_context_learning_strategy_is_deterministic_and_read_only(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    conversation = create_conversation(client, person["id"])
    decision = seed_decision(person["id"])
    create_outcome(client, person["id"], decision["id"])

    first = client.get(f"/api/v1/conversations/{conversation['id']}/analysis/context")
    second = client.get(f"/api/v1/conversations/{conversation['id']}/analysis/context")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["learning_strategy"] == second.json()["learning_strategy"]
    assert first.json()["learning_strategy"]["strategy_constraints"]["must_not_auto_execute"] is True
    assert first.json()["learning_strategy"]["strategy_constraints"]["must_not_auto_send"] is True
    assert first.json()["learning_strategy"]["strategy_constraints"]["must_not_call_llm"] is True
