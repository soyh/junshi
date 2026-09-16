from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository
from app.services.analysis_llm import AnalysisLLMService
from app.services.analysis_recommendation import AnalysisRecommendationService

USER_ID = "00000000-0000-0000-0000-000000000001"


def test_outcome_feedback_learning_reaches_fresh_analysis_and_recommendation(client):
    person = client.post("/api/v1/persons", json={"name": "闭环对象"}).json()
    assert client.post(
        "/api/v1/relationships",
        json={"person_id": person["id"], "status": "active", "stage": "dating"},
    ).status_code == 201
    conversation = client.post(
        "/api/v1/conversations",
        json={"person_id": person["id"], "title": "闭环会话"},
    ).json()
    message = client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conversation["id"],
            "sender_type": "user",
            "content": "上一轮行动已经产生结果",
            "sent_at": "2026-08-30T14:00:00+00:00",
        },
    ).json()
    with get_connection() as conn:
        decision = ActionDecisionRepository.create(
            conn,
            USER_ID,
            person["id"],
            "recommendation-previous",
            "confirmed",
            "用户显式确认",
        )

    assert client.post(
        f"/api/v1/persons/{person['id']}/action-plan/executions/{decision['id']}",
        json={"note": "显式执行"},
    ).status_code == 201
    assert client.post(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes/{decision['id']}",
        json={"outcome": "completed", "note": "上一轮行动完成"},
    ).status_code == 201

    class Provider:
        def __init__(self):
            self.context = None
            self.learning_consumed = None

        def analyze(self, context):
            self.context = context
            learning = context["learning_strategy"]["learning_inputs"]["action_feedback"]
            assert len(learning) == 1
            assert learning[0]["recommendation_id"] == "recommendation-previous"
            assert learning[0]["learning_status"] == "observed_feedback"
            assert learning[0]["observed_outcome_count"] == 1
            assert learning[0]["outcome_counts"]["completed"] == 1
            assert learning[0]["outcome_unknown_count"] == 0
            assert learning[0]["source"]["observed_outcomes"] == 1
            self.learning_consumed = learning[0]["recommendation_id"]

            evidence_id = message["id"]
            return {
                "summary": f"re-analysis-consumed:{self.learning_consumed}",
                "observed_facts": [
                    {
                        "content": "上一轮行动已产生结果",
                        "confidence": 1.0,
                        "evidence_source_ids": [evidence_id],
                    }
                ],
                "inferences": [],
                "unknowns": [
                    {
                        "content": "长期影响未知",
                        "confidence": 1.0,
                        "evidence_source_ids": [evidence_id],
                    }
                ],
                "hypotheses": [
                    {
                        "content": f"基于{self.learning_consumed}进入下一轮低压力沟通",
                        "confidence": 0.7,
                        "evidence_source_ids": [evidence_id],
                    }
                ],
                "emotional_signals": [],
                "relationship_signals": [],
                "risk_signals": [],
                "intent_signals": [],
                "evidence_links": [{"evidence_id": evidence_id, "type": "message"}],
                "analysis_constraints": ["must_preserve_unknowns"],
            }

    provider = Provider()
    service = AnalysisRecommendationService(analysis_llm_service=AnalysisLLMService())
    with get_connection() as conn:
        result = service.build_context(
            conn,
            USER_ID,
            conversation["id"],
            provider=provider,
        )

    assert provider.learning_consumed == "recommendation-previous"
    assert result["structured_analysis"]["summary"] == (
        "re-analysis-consumed:recommendation-previous"
    )
    assert len(result["recommendations"]) == 1
    assert result["recommendations"][0]["recommendation"] == (
        "基于recommendation-previous进入下一轮低压力沟通"
    )
    assert result["recommendations"][0]["evidence_source_ids"] == [message["id"]]
    assert result["recommendations"][0]["provenance"]["source"] == "strategy_candidate"
    assert result["recommendation_constraints"]["must_not_auto_select"] is True
    assert result["recommendation_constraints"]["must_not_auto_execute"] is True
