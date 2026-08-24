from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository


def create_person(client, name="反馈信号对象"):
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


def create_outcome(client, person_id, decision_id, outcome="completed"):
    response = client.post(
        f"/api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}",
        json={"outcome": outcome, "note": "结果已记录"},
    )
    assert response.status_code == 201


def get_signals(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/action-plan/feedback/signals")


def test_feedback_signals_group_by_recommendation_identity(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    first = seed_decision(person["id"], "recommendation-a", "confirmed")
    second = seed_decision(person["id"], "recommendation-a", "rejected")
    create_outcome(client, person["id"], first["id"], "completed")
    body = get_signals(client, person["id"]).json()
    assert len(body["signals"]) == 1
    signal = body["signals"][0]
    assert signal["recommendation_id"] == "recommendation-a"
    assert signal["decision_count"] == 2
    assert signal["decision_counts"] == {"confirmed": 1, "rejected": 1}
    assert signal["outcome_observed_count"] == 1
    assert signal["outcome_unknown_count"] == 1


def test_feedback_signals_count_outcomes_without_quality_inference(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    completed = seed_decision(person["id"], "recommendation-a")
    skipped = seed_decision(person["id"], "recommendation-a")
    failed = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], completed["id"], "completed")
    create_outcome(client, person["id"], skipped["id"], "skipped")
    create_outcome(client, person["id"], failed["id"], "failed")
    signal = get_signals(client, person["id"]).json()["signals"][0]
    assert signal["outcome_counts"] == {"completed": 1, "skipped": 1, "failed": 1}
    assert signal["latest_observed_outcome"]["outcome"] == "failed"
    assert "quality" not in signal
    assert "success" not in signal


def test_feedback_signals_preserve_unknown_outcomes(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"], "recommendation-a")
    signal = get_signals(client, person["id"]).json()["signals"][0]
    assert signal["outcome_observed_count"] == 0
    assert signal["outcome_unknown_count"] == 1
    assert signal["outcome_counts"] == {"completed": 0, "skipped": 0, "failed": 0}
    assert signal["latest_observed_outcome"] is None


def test_feedback_signals_are_deterministically_ordered(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    seed_decision(person["id"], "recommendation-b")
    seed_decision(person["id"], "recommendation-a")
    seed_decision(person["id"], None)
    signals = get_signals(client, person["id"]).json()["signals"]
    assert [item["recommendation_id"] for item in signals] == ["recommendation-a", "recommendation-b", None]


def test_feedback_signals_keep_person_isolation(client):
    first = create_person(client, "第一个对象")
    second = create_person(client, "第二个对象")
    create_relationship(client, first["id"])
    create_relationship(client, second["id"])
    seed_decision(first["id"], "recommendation-a")
    body = get_signals(client, second["id"]).json()
    assert body["signals"] == []


def test_feedback_signals_require_source_backed_boundaries(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    body = get_signals(client, person["id"]).json()
    constraints = body["feedback_signal_constraints"]
    assert constraints["must_be_source_backed"] is True
    assert constraints["must_preserve_unknowns"] is True
    assert constraints["must_group_only_by_recommendation_identity"] is True
    assert constraints["must_not_infer_recommendation_quality"] is True
    assert constraints["must_not_infer_relationship_impact"] is True


def test_feedback_signals_are_read_only_and_deterministic(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], "recommendation-a")
    create_outcome(client, person["id"], decision["id"])
    first = get_signals(client, person["id"]).json()
    second = get_signals(client, person["id"]).json()
    assert first == second
    assert first["feedback_signal_constraints"]["must_not_change_relationship"] is True
    assert first["feedback_signal_constraints"]["must_not_auto_execute"] is True


def test_feedback_signals_support_unattributed_decisions_without_dropping_them(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    decision = seed_decision(person["id"], None, "rejected")
    body = get_signals(client, person["id"]).json()
    assert len(body["signals"]) == 1
    assert body["signals"][0]["recommendation_id"] is None
    assert body["signals"][0]["decision_count"] == 1
    assert body["signals"][0]["decision_counts"] == {"confirmed": 0, "rejected": 1}
