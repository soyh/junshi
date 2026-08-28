from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="行动计划学习对象"):
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
            conn,
            USER_ID,
            person_id,
            recommendation_id,
            "confirmed",
            "行动计划学习桥接测试决策",
        )


def create_outcome(client, person_id, decision_id, outcome="completed"):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "行动计划学习桥接测试结果"},
    )
    assert response.status_code == 201


def get_context(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/action-plan/context")


def test_action_plan_context_exposes_observed_learning(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-observed")
    create_outcome(client, person["id"], decision["id"])

    response = get_context(client, person["id"])
    assert response.status_code == 200
    body = response.json()
    learning = body["learning_strategy"]

    assert body["action_plan"] == []
    assert learning["candidates"] == [
        {
            "recommendation_id": "recommendation-observed",
            "observed_outcome_count": 1,
            "outcome_counts": {"completed": 1, "failed": 0, "skipped": 0},
            "unknown_outcome_count": 0,
            "memory_update_count": 1,
            "synthesis_status": "source_backed_candidate",
            "unknowns": [
                "recommendation_quality",
                "success",
                "relationship_impact",
            ],
            "source": {
                "recommendation_id": "recommendation-observed",
                "observed_outcomes": 1,
                "unknown_outcomes": 0,
            },
        }
    ]
    assert learning["strategy_decision_learning"]["learning_candidate_decision_ids"] == [decision["id"]]
    assert learning["constraints"]["must_not_auto_execute"] is True


def test_action_plan_context_keeps_unobserved_learning_unknown(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-pending")

    learning = get_context(client, person["id"]).json()["learning_strategy"]
    bridge = learning["strategy_decision_learning"]

    assert learning["candidates"] == []
    assert bridge["learning_candidate_decision_ids"] == []
    assert bridge["unknown_decision_ids"] == [decision["id"]]
    assert bridge["unknown_count"] == 1
    assert learning["constraints"]["must_preserve_unknowns"] is True


def test_action_plan_context_learning_is_person_and_user_isolated(client):
    first = create_person(client, "计划学习A")
    second = create_person(client, "计划学习B")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    decision = seed_decision(first["id"], "recommendation-a")
    create_outcome(client, first["id"], decision["id"])

    second_learning = get_context(client, second["id"]).json()["learning_strategy"]
    assert second_learning["candidates"] == []
    assert second_learning["strategy_decision_learning"]["unknown_count"] == 0

    response = client.get(
        f"/api/v1/persons/{first['id']}/action-plan/context",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_action_plan_context_learning_is_read_only_and_deterministic(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"])

    first = get_context(client, person["id"])
    second = get_context(client, person["id"])
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()
    assert second.json()["learning_strategy"]["constraints"]["must_not_turn_learning_into_fact"] is True


def test_downstream_learning_candidate_contract_is_identical_between_action_plan_and_strategic_reply(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    first = seed_decision(person["id"], "recommendation-a")
    second = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], first["id"], "completed")
    create_outcome(client, person["id"], second["id"], "failed")

    action_plan_learning = get_context(client, person["id"]).json()["learning_strategy"]
    strategic_reply_learning = client.get(
        f"/api/v1/persons/{person['id']}/strategic-reply/context"
    ).json()["learning_strategy"]

    expected_candidate = {
        "recommendation_id": "recommendation-a",
        "observed_outcome_count": 2,
        "outcome_counts": {"completed": 1, "failed": 1, "skipped": 0},
        "unknown_outcome_count": 0,
        "memory_update_count": 2,
        "synthesis_status": "source_backed_candidate",
        "unknowns": [
            "recommendation_quality",
            "success",
            "relationship_impact",
        ],
        "source": {
            "recommendation_id": "recommendation-a",
            "observed_outcomes": 2,
            "unknown_outcomes": 0,
        },
    }
    assert action_plan_learning["candidates"] == [expected_candidate]
    assert strategic_reply_learning["candidates"] == [expected_candidate]


def test_action_plan_context_learning_source_is_not_inferred_quality(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-source")
    create_outcome(client, person["id"], decision["id"], "completed")

    learning = get_context(client, person["id"]).json()["learning_strategy"]
    candidate = learning["candidates"][0]
    assert candidate["source"]["recommendation_id"] == "recommendation-source"
    assert candidate["source"]["observed_outcomes"] == 1
    assert learning["constraints"]["must_not_infer_recommendation_quality"] is True
    assert learning["constraints"]["must_not_change_relationship"] is True
