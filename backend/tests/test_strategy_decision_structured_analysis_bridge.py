import sqlite3

from app.schemas.structured_analysis import StructuredAnalysis
from app.services.strategy_decision import StrategyDecisionContextService


class FakeSynthesisService:
    def get_synthesis(self, conn: sqlite3.Connection, user_id: str, person_id: str) -> dict:
        return {
            "person": {"id": person_id},
            "relationship": {"id": "relationship-1", "status": "active", "stage": "dating"},
            "strategy_constraints": {"existing": True},
            "candidates": [
                {
                    "recommendation_id": "recommendation-1",
                    "observed_outcome_count": 0,
                    "unknown_outcome_count": 1,
                }
            ],
        }


def make_analysis() -> StructuredAnalysis:
    return StructuredAnalysis(
        summary="derived summary",
        observed_facts=[],
        inferences=[],
        unknowns=[{"content": "unknown", "evidence_source_ids": []}],
        hypotheses=[],
        emotional_signals=[],
        relationship_signals=[],
        risk_signals=[],
        intent_signals=[],
        evidence_links=[],
        analysis_constraints=["derived_only"],
    )


def test_strategy_decision_context_can_include_structured_analysis():
    service = StrategyDecisionContextService(synthesis_service=FakeSynthesisService())

    context = service.get_context(
        sqlite3.connect(":memory:"),
        "user-1",
        "person-1",
        structured_analysis=make_analysis(),
    )

    assert context["structured_analysis"]["summary"] == "derived summary"
    assert context["strategy_constraints"]["existing"] is True
    assert context["strategy_constraints"]["must_treat_llm_output_as_derived"] is True
    assert context["strategy_constraints"]["must_preserve_evidence_provenance"] is True
    assert context["strategy_constraints"]["must_preserve_unknowns"] is True
    assert context["strategy_constraints"]["must_not_auto_select"] is True
    assert context["decision_inputs"]["selection_status"] == "requires_explicit_decision"


def test_strategy_decision_context_without_analysis_is_backward_compatible():
    service = StrategyDecisionContextService(synthesis_service=FakeSynthesisService())

    context = service.get_context(sqlite3.connect(":memory:"), "user-1", "person-1")

    assert "structured_analysis" not in context
    assert context["strategy_constraints"]["must_not_auto_select"] is True
