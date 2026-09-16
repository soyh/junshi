from app.core.database import get_connection
from app.repositories.action_plan_proposal import ActionPlanProposalRepository
from app.services.action_decision import ActionDecisionService


def create_person(client, name="proposal bridge object"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "active", "stage": "dating"},
    )
    assert response.status_code == 201


def test_confirmed_decision_requires_server_proposal(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/decisions",
        json={"decision": "confirmed", "recommendation_id": "client-invented"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "recommendation is not an available evidence-backed action"


def test_proposal_isolated_by_user_and_person(client):
    person = create_person(client)
    create_relationship(client, person["id"])

    with get_connection() as conn:
        proposal = ActionPlanProposalRepository.create(
            conn,
            "00000000-0000-0000-0000-000000000001",
            person["id"],
            "recommendation-1",
            "保持低压力互动",
            ["message-1"],
        )
        assert ActionPlanProposalRepository.get_available_by_recommendation(
            conn,
            "11111111-1111-1111-1111-111111111111",
            person["id"],
            proposal["recommendation_id"],
        ) is None
        assert ActionPlanProposalRepository.get_available_by_recommendation(
            conn,
            proposal["user_id"],
            "different-person",
            proposal["recommendation_id"],
        ) is None


def test_proposal_evidence_must_still_exist_before_confirmation(client):
    person = create_person(client, "evidence bridge object")
    create_relationship(client, person["id"])

    with get_connection() as conn:
        proposal = ActionPlanProposalRepository.create(
            conn,
            "00000000-0000-0000-0000-000000000001",
            person["id"],
            "recommendation-1",
            "保持低压力互动",
            ["message-1"],
        )

    class FakeActionPlanService:
        def get_context(self, conn, user_id, person_id):
            return {
                "person": {"id": person_id},
                "relationship": {"id": "relationship-1"},
                "evidence": [],
                "action_plan": [],
            }

    with get_connection() as conn:
        service = ActionDecisionService(action_plan_service=FakeActionPlanService())
        try:
            service.create_decision(
                conn,
                "00000000-0000-0000-0000-000000000001",
                person["id"],
                proposal["recommendation_id"],
                "confirmed",
                None,
            )
        except ValueError as exc:
            assert str(exc) == "action plan proposal is no longer evidence-backed"
        else:
            raise AssertionError("expected evidence-backed proposal validation to fail")


def test_rejected_decision_does_not_require_proposal(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/decisions",
        json={"decision": "rejected", "note": "暂不执行"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["recommendation_id"] is None
    assert body["action_plan_proposal_id"] is None
