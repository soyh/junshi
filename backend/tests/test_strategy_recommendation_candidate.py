from app.services.recommendation_producer import RecommendationProducer
from app.services.strategy_recommendation_candidate import StrategyRecommendationCandidateService


def analysis():
    return {
        "summary": "保持正常互动",
        "observed_facts": [{"content": "对方主动联系"}],
        "inferences": [{"content": "仍有互动意愿"}],
        "hypotheses": [
            {
                "content": "保持正常互动，不立即升级关系",
                "confidence": 0.72,
                "evidence_source_ids": ["interaction-1", "interaction-1"],
            }
        ],
        "unknowns": ["对方真实动机未知"],
    }


def evidence():
    return [
        {"source_type": "interaction", "source_id": "interaction-1", "content": "对方主动联系"},
    ]


def test_strategy_candidate_has_minimal_recommendation_contract():
    candidate = StrategyRecommendationCandidateService.build_candidates(analysis())[0]
    assert set(candidate) == {"id", "recommendation", "evidence_source_ids", "provenance"}
    assert candidate["recommendation"] == "保持正常互动，不立即升级关系"
    assert candidate["evidence_source_ids"] == ["interaction-1"]
    assert candidate["provenance"]["source"] == "strategy_candidate"
    assert candidate["provenance"]["strategy_candidate_type"] == "analysis_hypothesis"


def test_strategy_candidate_identity_is_deterministic():
    first = StrategyRecommendationCandidateService.build_candidates(analysis())
    second = StrategyRecommendationCandidateService.build_candidates(analysis())
    assert first == second


def test_strategy_candidate_preserves_unknowns_as_provenance():
    candidate = StrategyRecommendationCandidateService.build_candidates(analysis())[0]
    assert candidate["provenance"]["unknowns_preserved"] == ["对方真实动机未知"]
    assert "facts" not in candidate
    assert "inferences" not in candidate


def test_strategy_candidate_rejects_unbacked_hypotheses():
    value = analysis()
    value["hypotheses"] = [
        {"content": "立即升级关系", "confidence": 0.9},
        {"content": "未知来源", "evidence_source_ids": ["missing"]},
    ]
    candidates = StrategyRecommendationCandidateService.build_candidates(value)
    assert len(candidates) == 2
    assert RecommendationProducer.produce(candidates, evidence()) == []


def test_strategy_candidate_does_not_accept_structured_analysis_as_recommendation():
    assert StrategyRecommendationCandidateService.build_candidates({
        "summary": "摘要",
        "observed_facts": [],
        "inferences": [],
        "hypotheses": [],
        "unknowns": [],
    }) == []
