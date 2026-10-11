from pydantic import ValidationError

from app.schemas.recommendation import Recommendation, RecommendationContextResponse
from app.schemas.structured_analysis import StructuredAnalysis
from app.services.recommendation_producer import RecommendationProducer


def evidence():
    return [
        {"source_type": "interaction", "source_id": "interaction-1", "content": "对方主动联系"},
        {"source_type": "interaction", "source_id": "interaction-2", "content": "双方正常互动"},
    ]


def candidate(**overrides):
    value = {
        "id": "recommendation-1",
        "recommendation": "保持正常互动，不立即升级关系",
        "evidence_source_ids": ["interaction-1"],
        "action": "保持正常互动",
        "reply": "按正常节奏回复",
        "priority": "normal",
        "time_horizon": "short_term",
        "provenance": {"source": "explicit_strategy_candidate"},
    }
    value.update(overrides)
    return value


def test_recommendation_schema_is_strict_and_typed():
    recommendation = Recommendation(**candidate())
    assert recommendation.id == "recommendation-1"
    assert recommendation.evidence_source_ids == ["interaction-1"]
    assert recommendation.provenance["source"] == "explicit_strategy_candidate"


def test_recommendation_schema_rejects_unknown_fields():
    try:
        Recommendation(**candidate(unexpected="must-reject"))
    except ValidationError:
        pass
    else:
        raise AssertionError("unknown recommendation fields must be rejected")


def test_producer_accepts_only_explicit_evidence_backed_candidates():
    produced = RecommendationProducer.produce([candidate()], evidence())
    assert produced == [candidate()]


def test_producer_rejects_missing_or_unknown_evidence_provenance():
    candidates = [
        candidate(id="missing-provenance", evidence_source_ids=[]),
        candidate(id="unknown-source", evidence_source_ids=["interaction-404"]),
        candidate(id="partial-source", evidence_source_ids=["interaction-1", "interaction-404"]),
        candidate(id="bad-provenance", provenance=None),
    ]
    assert RecommendationProducer.produce(candidates, evidence()) == []


def test_producer_does_not_promote_structured_analysis():
    analysis = StructuredAnalysis(
        summary="应该继续互动",
        observed_facts=[],
        inferences=[],
        unknowns=[],
        hypotheses=[{
            "content": "应该立即发送消息",
            "confidence": 0.99,
            "evidence_source_ids": ["interaction-1"],
        }],
        emotional_signals=[],
        relationship_signals=[],
        risk_signals=[],
        intent_signals=[],
        evidence_links=[],
        analysis_constraints=["derived_only"],
    )
    assert RecommendationProducer.produce([analysis.model_dump(mode="json")], evidence()) == []


def test_producer_preserves_unknowns_without_promoting_them_to_facts():
    item = candidate(
        recommendation="暂不进行关系升级，先补充对方真实意愿信息",
        evidence_source_ids=["interaction-1"],
        provenance={"source": "explicit_strategy_candidate", "unknowns_preserved": ["真实动机未知"]},
    )
    produced = RecommendationProducer.produce([item], evidence())
    assert produced[0]["recommendation"] == item["recommendation"]
    assert produced[0]["provenance"]["unknowns_preserved"] == ["真实动机未知"]
    assert "facts" not in produced[0]


def test_producer_is_deterministic_and_preserves_candidate_order():
    first = candidate(id="recommendation-1")
    second = candidate(id="recommendation-2", evidence_source_ids=["interaction-2"])
    assert RecommendationProducer.produce([first, second], evidence()) == [first, second]


def test_produced_recommendation_is_compatible_with_existing_downstream_boundaries():
    produced = RecommendationProducer.produce([candidate()], evidence())

    from app.services.action_plan import ActionPlanService
    from app.services.strategic_reply import StrategicReplyService

    action_plan = ActionPlanService.build_action_plan(produced, evidence())
    assert action_plan == [{
        "recommendation_id": "recommendation-1",
        "action": "保持正常互动",
        "evidence_source_ids": ["interaction-1"],
        "status": "proposed",
        "requires_user_confirmation": True,
        "priority": "normal",
        "time_horizon": "short_term",
    }]
    assert StrategicReplyService.build_draft(produced, evidence()) == "按正常节奏回复"


def test_context_response_keeps_recommendation_items_typed():
    context = {
        "person": {"id": "person-1"},
        "relationship": {"id": "relationship-1"},
        "current_state": {"status": "active", "stage": "dating"},
        "evidence": evidence(),
        "facts": [],
        "inferences": [],
        "unknowns": [],
        "recommendations": [candidate()],
        "learning_strategy": {"candidates": []},
    }
    response = RecommendationContextResponse.model_validate(context)
    assert response.recommendations[0].id == "recommendation-1"
    assert response.recommendations[0].evidence_source_ids == ["interaction-1"]
