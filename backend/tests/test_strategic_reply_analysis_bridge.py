from app.schemas.structured_analysis import StructuredAnalysis
from app.services.strategic_reply_analysis_bridge import StrategicReplyAnalysisBridgeService


def structured_analysis():
    return StructuredAnalysis.model_validate({
        "summary": "derived reply context",
        "observed_facts": [{
            "content": "对方询问周末是否有空",
            "confidence": 1.0,
            "evidence_source_ids": ["message-1"],
        }],
        "inferences": [{
            "content": "可能存在主动建立联系的意愿",
            "confidence": 0.7,
            "evidence_source_ids": ["message-1"],
        }],
        "unknowns": [{
            "content": "询问周末的具体动机未知",
            "confidence": 1.0,
            "evidence_source_ids": ["message-1"],
        }],
        "hypotheses": [],
        "emotional_signals": [],
        "relationship_signals": [],
        "risk_signals": [],
        "intent_signals": [],
        "evidence_links": [{"evidence_id": "message-1", "type": "message"}],
        "analysis_constraints": ["must_preserve_unknowns"],
    })


def reply_context():
    return {
        "person": {"id": "person-1"},
        "relationship": {"id": "relationship-1"},
        "current_state": {"status": "active", "stage": "dating"},
        "evidence": [{"source_id": "message-1", "content": "原始证据"}],
        "facts": [],
        "inferences": [],
        "unknowns": [],
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


def test_bridge_preserves_structured_analysis_as_derived_input():
    result = StrategicReplyAnalysisBridgeService().build_context(
        reply_context(), structured_analysis()
    )
    assert result["structured_analysis"]["summary"] == "derived reply context"
    assert result["reply_inputs"]["analysis_is_derived"] is True
    assert result["reply_inputs"]["summary"] == "derived reply context"


def test_bridge_preserves_provenance_and_unknowns():
    result = StrategicReplyAnalysisBridgeService().build_context(
        reply_context(), structured_analysis()
    )
    assert result["reply_inputs"]["signals"]["observed_facts"][0]["evidence_source_ids"] == ["message-1"]
    assert result["reply_inputs"]["signals"]["inferences"][0]["evidence_source_ids"] == ["message-1"]
    assert result["reply_inputs"]["signals"]["unknowns"][0]["content"] == "询问周末的具体动机未知"
    assert result["reply_inputs"]["signals"]["unknowns"][0]["evidence_source_ids"] == ["message-1"]


def test_bridge_does_not_turn_analysis_into_reply_draft():
    result = StrategicReplyAnalysisBridgeService().build_context(
        reply_context(), structured_analysis()
    )
    assert result["draft"] is None
    assert result["recommendations"] == []


def test_bridge_does_not_change_existing_reply_constraints_semantics():
    result = StrategicReplyAnalysisBridgeService().build_context(
        reply_context(), structured_analysis()
    )
    assert result["reply_constraints"]["must_be_evidence_backed"] is True
    assert result["reply_constraints"]["must_preserve_unknowns"] is True
    assert result["reply_constraints"]["must_not_auto_send"] is True
    assert result["reply_constraints"]["must_not_change_relationship"] is True
    assert result["reply_constraints"]["must_treat_llm_output_as_derived"] is True
    assert result["reply_constraints"]["must_preserve_evidence_provenance"] is True


def test_bridge_rejects_non_dict_reply_context():
    try:
        StrategicReplyAnalysisBridgeService().build_context([], structured_analysis())
    except TypeError as exc:
        assert str(exc) == "reply_context must be a dict"
    else:
        raise AssertionError("expected TypeError")
