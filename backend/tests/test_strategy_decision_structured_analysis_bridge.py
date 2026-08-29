from app.schemas.structured_analysis import StructuredAnalysis
from app.services.strategy_decision import StrategyDecisionContextService


def _analysis() -> StructuredAnalysis:
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


def test_strategy_decision_context_can_include_structured_analysis(client):
    from tests.helpers import create_person, create_relationship

    person = create_person(client)
    relationship = create_relationship(client, person["id"])

    service = StrategyDecisionContextService()
    conn = client.app.state._test_connection if hasattr(client.app.state, "_test_connection") else None
    if conn is None:
        import sqlite3
        from app.core.database import get_connection
        conn = get_connection()

    try:
        context = service.get_context(
            conn,
            "00000000-0000-0000-0000-000000000001",
            person["id"],
            structured_analysis=_analysis(),
        )
    finally:
        conn.close()

    assert context["structured_analysis"]["summary"] == "derived summary"
    assert context["strategy_constraints"]["must_treat_llm_output_as_derived"] is True
    assert context["strategy_constraints"]["must_preserve_unknowns"] is True
    assert context["strategy_constraints"]["must_not_auto_select"] is True
    assert context["relationship"]["id"] == relationship["id"]
