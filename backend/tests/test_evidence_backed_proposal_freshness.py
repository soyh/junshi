from app.core.database import get_connection
from app.repositories.action_plan_snapshot import ActionPlanSnapshotRepository
from app.services.action_plan import ActionPlanService

USER_ID = "00000000-0000-0000-0000-000000000001"


def test_deleted_canonical_evidence_invalidates_persisted_action_plan(client):
    person = client.post("/api/v1/persons", json={"name": "证据新鲜度测试对象"}).json()
    assert client.post(
        "/api/v1/relationships",
        json={"person_id": person["id"], "status": "active", "stage": "dating"},
    ).status_code == 201
    conversation = client.post(
        "/api/v1/conversations",
        json={"person_id": person["id"], "title": "证据新鲜度测试"},
    ).json()
    message = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation["id"],
            "sender_type": "user",
            "content": "这条证据支持一个低压力行动建议",
            "sent_at": "2026-09-17T01:00:00+00:00",
        },
    ).json()

    recommendation = {
        "id": "recommendation-freshness-1",
        "action": "保持低压力互动",
        "evidence_source_ids": [message["id"]],
        "provenance": {"source": "strategy_candidate"},
    }
    evidence = [{
        "source_id": message["id"],
        "source_type": "message",
        "content": message["content"],
    }]
    action_plan = ActionPlanService.build_action_plan([recommendation], evidence)
    assert len(action_plan) == 1

    with get_connection() as conn:
        ActionPlanSnapshotRepository().upsert(
            conn,
            USER_ID,
            person["id"],
            recommendation,
            action_plan[0],
            evidence,
        )

    context_before = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/decisions/context"
    )
    assert context_before.status_code == 200
    assert [item["recommendation_id"] for item in context_before.json()["action_plan"]] == [
        recommendation["id"]
    ]

    assert client.delete(f"/api/v1/messages/{message['id']}").status_code == 204

    context_after = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/decisions/context"
    )
    assert context_after.status_code == 200
    assert context_after.json()["action_plan"] == []
    assert context_after.json()["decisions"] == []

    decision = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/decisions",
        json={
            "decision": "confirmed",
            "recommendation_id": recommendation["id"],
            "note": "不应确认已经失去 canonical evidence 的 action",
        },
    )
    assert decision.status_code == 409
    assert decision.json()["detail"] == "recommendation is not an available evidence-backed action"
