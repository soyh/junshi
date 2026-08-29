from app.services.strategic_reply_decision_bridge import StrategicReplyDecisionBridgeService


class FakeStrategicReplyService:
    def get_context(self, conn, user_id, person_id):
        return {
            "person": {"id": person_id},
            "relationship": {"id": "relationship-1"},
            "current_state": {"status": "active", "stage": "dating"},
            "evidence": [{"source_id": "message-1"}],
            "facts": [],
            "inferences": [],
            "unknowns": [{"content": "unknown"}],
            "recommendations": [],
            "reply_constraints": {
                "must_be_evidence_backed": True,
                "must_preserve_unknowns": True,
                "must_not_auto_send": True,
                "must_not_change_relationship": True,
            },
            "draft": None,
            "learning_strategy": {"candidates": []},
        }


class FakeDecisionResultService:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def get_context(self, conn, user_id, person_id):
        self.calls.append((conn, user_id, person_id))
        return {
            "person": {"id": person_id},
            "relationship": {"id": "relationship-1"},
            "results": self.results,
        }


def test_bridge_requires_explicit_decision_when_no_confirmed_decision_exists():
    result_service = FakeDecisionResultService([])
    service = StrategicReplyDecisionBridgeService(
        strategic_reply_service=FakeStrategicReplyService(),
        decision_result_service=result_service,
    )

    result = service.get_context("conn", "user-1", "person-1")

    assert result["decision_downstream"] == {
        "confirmed_decisions": [],
        "selection_status": "requires_explicit_decision",
        "selection_is_automatic": False,
    }
    assert result["reply_constraints"]["must_require_explicit_decision"] is True
    assert result["reply_constraints"]["must_not_auto_select"] is True
    assert result["reply_constraints"]["must_not_auto_confirm"] is True
    assert result["reply_constraints"]["must_not_auto_send"] is True
    assert result["reply_constraints"]["must_not_auto_execute"] is True
    assert result["draft"] is None


def test_bridge_exposes_confirmed_decisions_without_selecting_or_executing():
    result_service = FakeDecisionResultService([
        {
            "id": "decision-1",
            "recommendation_id": "recommendation-1",
            "decision": "confirmed",
            "result_status": "confirmed_pending_execution",
            "created_at": "2026-08-29T12:00:00+00:00",
            "execution": None,
            "outcome": None,
        },
        {
            "id": "decision-2",
            "recommendation_id": "recommendation-2",
            "decision": "rejected",
            "result_status": "not_actionable",
            "created_at": "2026-08-29T11:00:00+00:00",
            "execution": None,
            "outcome": None,
        },
    ])
    service = StrategicReplyDecisionBridgeService(
        strategic_reply_service=FakeStrategicReplyService(),
        decision_result_service=result_service,
    )

    result = service.get_context("conn", "user-1", "person-1")

    assert result["decision_downstream"]["confirmed_decisions"] == [{
        "decision_id": "decision-1",
        "recommendation_id": "recommendation-1",
        "decision": "confirmed",
        "result_status": "confirmed_pending_execution",
        "created_at": "2026-08-29T12:00:00+00:00",
    }]
    assert result["decision_downstream"]["selection_status"] == "explicitly_confirmed"
    assert result["decision_downstream"]["selection_is_automatic"] is False
    assert result["draft"] is None
    assert result["recommendations"] == []
    assert result_service.calls == [("conn", "user-1", "person-1")]


def test_bridge_preserves_reply_context_and_does_not_call_llm():
    result_service = FakeDecisionResultService([])
    service = StrategicReplyDecisionBridgeService(
        strategic_reply_service=FakeStrategicReplyService(),
        decision_result_service=result_service,
    )

    result = service.get_context("conn", "user-1", "person-1")

    assert result["person"]["id"] == "person-1"
    assert result["evidence"] == [{"source_id": "message-1"}]
    assert result["unknowns"] == [{"content": "unknown"}]
    assert result["learning_strategy"] == {"candidates": []}
