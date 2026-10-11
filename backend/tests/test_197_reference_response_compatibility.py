"""Reference metadata is additive; legacy responses remain usable."""

from types import SimpleNamespace

import pytest
from fastapi.exceptions import ResponseValidationError

from app.api.routes import (
    analysis_action_plan,
    analysis_recommendation,
    analysis_strategic_reply,
    analysis_strategy,
)


ROUTES = [
    (analysis_action_plan, "action-plan"),
    (analysis_recommendation, "recommendation"),
    (analysis_strategic_reply, "strategic-reply"),
    (analysis_strategy, "strategy"),
]


def legacy_context(kind):
    analysis = {
        "summary": "Legacy derived analysis",
        **{key: [] for key in (
            "observed_facts", "inferences", "unknowns", "hypotheses",
            "emotional_signals", "relationship_signals", "risk_signals",
            "intent_signals", "evidence_links", "analysis_constraints",
        )},
    }
    result = {
        "person": {"id": "p1"}, "relationship": {}, "current_state": {},
        "structured_analysis": analysis,
    }
    if kind == "strategy":
        return {**result, "strategy_constraints": {}, "candidates": [], "decision_inputs": {}}
    result.update({key: [] for key in (
        "evidence", "facts", "inferences", "unknowns", "recommendations",
    )})
    result["learning_strategy"] = {}
    if kind == "action-plan":
        result.update(action_constraints={}, action_plan=[], action_plan_inputs={})
    elif kind == "recommendation":
        result["recommendation_constraints"] = {}
    else:
        result.update(reply_constraints={}, draft=None, reply_inputs={})
    return result


def install_context(monkeypatch, route, payload):
    def build(*args, **kwargs):
        return payload
    monkeypatch.setattr(route, "service", SimpleNamespace(
        build_context=build, build_strategy_context=build,
    ))
    monkeypatch.setattr(route, "_build_provider", lambda *args: object())


@pytest.mark.parametrize("route,kind", ROUTES)
@pytest.mark.parametrize("state", ["missing", "null", "empty", "mixed"])
def test_reference_metadata_is_additive(client, monkeypatch, route, kind, state):
    payload = legacy_context(kind)
    expected = None
    if state == "null":
        payload["model_references"] = None
    elif state in {"empty", "mixed"}:
        items = [] if state == "empty" else [
            {"reference_id": "d1", "type": "document", "content": "Background"},
            {"reference_id": "s1", "type": "skill", "content": "Method"},
        ]
        expected = {"conversation_id": "c1", "count": len(items),
                    "policy": {"system_precedence": "system wins"}, "items": items}
        payload["model_references"] = expected
    install_context(monkeypatch, route, payload)
    response = client.get(f"/api/v1/conversations/c1/{kind}/context")
    assert response.status_code == 200
    assert response.json()["model_references"] == expected
    assert response.json()["structured_analysis"] == payload["structured_analysis"]


@pytest.mark.parametrize("route,kind", ROUTES)
def test_present_but_incomplete_reference_metadata_is_rejected(client, monkeypatch, route, kind):
    payload = legacy_context(kind)
    payload["model_references"] = {"items": []}
    install_context(monkeypatch, route, payload)
    with pytest.raises(ResponseValidationError):
        client.get(f"/api/v1/conversations/c1/{kind}/context")
