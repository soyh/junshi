from app.core.database import get_connection
from app.services.action_decision import ActionDecisionService
from app.services.analysis_action_plan import AnalysisActionPlanService
from app.services.analysis_llm import AnalysisLLMService

USER_ID = "00000000-0000-0000-0000-000000000001"


def test_real_recommendation_reaches_action_decision_without_fake_action_plan(client):
    person = client.post("/api/v1/persons", json={"name": "真实推荐决策桥接对象"}).json()
    assert client.post(
        "/api/v1/relationships",
        json={"person_id": person["id"], "status": "active", "stage": "dating"},
    ).status_code == 201
    conversation = client.post(
        "/api/v1/conversations",
        json={"person_id": person["id"], "title": "真实推荐决策桥接"},
    ).json()
    message = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation["id"],
            "sender_type": "user",
            "content": "当前需要基于证据形成下一步建议",
            "sent_at": "2026-09-16T10:00:00+00:00",
        },
    ).json()

    class Provider:
        def analyze(self, context):
            assert context["person"]["id"] == person["id"]
            return {
                "summary": "形成下一步策略建议",
                "observed_facts": [{
                    "content": "用户提供了当前关系证据",
                    "confidence": 1.0,
                    "evidence_source_ids": [message["id"]],
                }],
                "inferences": [],
                "unknowns": [{
                    "content": "对方后续反应未知",
                    "confidence": 1.0,
                    "evidence_source_ids": [message["id"]],
                }],
                "hypotheses": [{
                    "content": "保持低压力互动并观察后续反馈",
                    "confidence": 0.8,
                    "evidence_source_ids": [message["id"]],
                    "action": "保持低压力互动并观察后续反馈",
                }],
                "emotional_signals": [],
                "relationship_signals": [],
                "risk_signals": [],
                "intent_signals": [],
                "evidence_links": [{"evidence_id": message["id"], "type": "message"}],
                "analysis_constraints": ["must_preserve_unknowns"],
            }

    service = AnalysisActionPlanService(analysis_llm_service=AnalysisLLMService())
    with get_connection() as conn:
        result = service.build_context(
            conn,
            USER_ID,
            conversation["id"],
            provider=Provider(),
        )

    assert len(result["recommendations"]) == 1
    recommendation = result["recommendations"][0]
    assert recommendation["evidence_source_ids"] == [message["id"]]
    assert recommendation["provenance"]["source"] == "strategy_candidate"
    assert recommendation["action"] == "保持低压力互动并观察后续反馈"

    assert len(result["action_plan"]) == 1
    action_plan = result["action_plan"][0]
    assert action_plan["recommendation_id"] == recommendation["id"]
    assert action_plan["action"] == recommendation["action"]
    assert action_plan["evidence_source_ids"] == [message["id"]]
    assert action_plan["status"] == "proposed"
    assert action_plan["requires_user_confirmation"] is True

    with get_connection() as conn:
        decision = ActionDecisionService().create_decision(
            conn,
            USER_ID,
            person["id"],
            recommendation["id"],
            "confirmed",
            "用户显式确认",
        )

    assert decision["recommendation_id"] == recommendation["id"]
    assert decision["decision"] == "confirmed"
