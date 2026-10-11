from app.schemas.structured_analysis import StructuredAnalysis, StructuredAnalysisItem
from app.services.strategy_analysis_bridge import StrategyAnalysisBridgeService


def make_analysis() -> StructuredAnalysis:
    return StructuredAnalysis(
        summary="summary",
        observed_facts=[
            StructuredAnalysisItem(
                content="fact",
                confidence=0.9,
                evidence_source_ids=["message-1"],
            )
        ],
        inferences=[
            StructuredAnalysisItem(
                content="inference",
                confidence=0.7,
                evidence_source_ids=["message-1"],
            )
        ],
        unknowns=[StructuredAnalysisItem(content="unknown")],
        hypotheses=[],
        emotional_signals=[],
        relationship_signals=[],
        risk_signals=[],
        intent_signals=[],
        evidence_links=[{"source_id": "message-1"}],
        analysis_constraints=["preserve_unknowns"],
    )


def test_bridge_adds_structured_analysis_without_mutating_strategy_context():
    context = {
        "person": {"id": "person-1"},
        "strategy_constraints": {"existing": True},
        "candidates": [],
    }

    result = StrategyAnalysisBridgeService().build_input(context, make_analysis())

    assert "structured_analysis" in result
    assert result["structured_analysis"]["summary"] == "summary"
    assert result["structured_analysis"]["inferences"][0]["evidence_source_ids"] == ["message-1"]
    assert result["strategy_constraints"] == {
        "existing": True,
        "must_treat_llm_output_as_derived": True,
        "must_preserve_evidence_provenance": True,
        "must_preserve_unknowns": True,
        "must_not_auto_select": True,
    }
    assert "structured_analysis" not in context
    assert context["strategy_constraints"] == {"existing": True}


def test_bridge_does_not_turn_analysis_into_canonical_fields():
    context = {"facts": ["canonical-fact"], "unknowns": ["canonical-unknown"]}

    result = StrategyAnalysisBridgeService().build_input(context, make_analysis())

    assert result["facts"] == ["canonical-fact"]
    assert result["unknowns"] == ["canonical-unknown"]
    assert result["structured_analysis"]["unknowns"][0]["content"] == "unknown"


def test_bridge_rejects_invalid_strategy_context():
    try:
        StrategyAnalysisBridgeService().build_input([], make_analysis())
    except TypeError as exc:
        assert str(exc) == "strategy_context must be a dict"
    else:
        raise AssertionError("expected TypeError")
