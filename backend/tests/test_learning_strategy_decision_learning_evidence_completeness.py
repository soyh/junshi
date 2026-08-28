from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


USER_ID = "00000000-0000-0000-0000-000000000001"


def create_person(client, name="决策证据完整性对象"):
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
            USER_ID,
            person_id,
            recommendation_id,
            decision,
            "决策证据完整性测试",
        )


def create_outcome(client, person_id, decision_id):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": "completed", "note": "决策证据完整性测试结果"},
    )
    assert response.status_code == 201


def test_strategy_decision_learning_synthesis_exposes_provenance_for_observed_and_unknown(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    observed = seed_decision(person["id"], "recommendation-observed")
    unknown = seed_decision(person["id"], "recommendation-unknown", "rejected")
    create_outcome(client, person["id"], observed["id"])

    response = client.get(
        f"/api/v1/persons/{person['id']}/learning-strategy/synthesis"
    )
    assert response.status_code == 200

    learning = response.json()["strategy_decision_learning"]
    assert learning["learning_candidate_provenance"] == [
        {
            "decision_id": observed["id"],
            "recommendation_id": "recommendation-observed",
            "outcome_id": learning["learning_candidate_provenance"][0]["outcome_id"],
            "feedback_status": "outcome_observed",
        }
    ]
    assert learning["unknown_decision_provenance"] == [
        {
            "decision_id": unknown["id"],
            "recommendation_id": "recommendation-unknown",
            "outcome_id": None,
            "feedback_status": "outcome_unknown",
        }
    ]


def test_strategy_decision_learning_provenance_arrays_follow_decision_id_order(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    first = seed_decision(person["id"], "recommendation-a")
    second = seed_decision(person["id"], "recommendation-b")
    create_outcome(client, person["id"], first["id"])
    create_outcome(client, person["id"], second["id"])

    learning = client.get(
        f"/api/v1/persons/{person['id']}/learning-strategy/synthesis"
    ).json()["strategy_decision_learning"]

    assert learning["learning_candidate_decision_ids"] == [
        item["decision_id"] for item in learning["learning_candidate_provenance"]
    ]
    assert learning["unknown_decision_ids"] == [
        item["decision_id"] for item in learning["unknown_decision_provenance"]
    ]
    assert learning["learning_candidate_count"] == len(
        learning["learning_candidate_provenance"]
    )
    assert learning["unknown_count"] == len(learning["unknown_decision_provenance"])


def test_strategy_decision_learning_provenance_is_identical_across_downstream_layers(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"])

    synthesis = client.get(
        f"/api/v1/persons/{person['id']}/learning-strategy/synthesis"
    )
    action_plan = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/context"
    )
    strategic_reply = client.get(
        f"/api/v1/persons/{person['id']}/strategic-reply/context"
    )

    assert synthesis.status_code == 200
    assert action_plan.status_code == 200
    assert strategic_reply.status_code == 200

    expected = synthesis.json()["strategy_decision_learning"]
    assert action_plan.json()["learning_strategy"]["strategy_decision_learning"] == expected
    assert strategic_reply.json()["learning_strategy"]["strategy_decision_learning"] == expected
