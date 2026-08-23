from app.services.strategic_reply import StrategicReplyService


def evidence():
    return [
        {"source_id": "m1", "source_type": "message"},
        {"source_id": "i1", "source_type": "interaction"},
    ]


def test_synthesizes_first_explicit_evidence_backed_reply():
    recommendations = [
        {
            "id": "r1",
            "reply": "可以，周六下午有空。",
            "evidence_source_ids": ["m1"],
        }
    ]
    assert StrategicReplyService.build_draft(recommendations, evidence()) == "可以，周六下午有空。"


def test_skips_recommendation_without_reply():
    recommendations = [
        {"id": "r1", "action": "约周六见面", "evidence_source_ids": ["m1"]},
        {"id": "r2", "reply": "可以周六见面。", "evidence_source_ids": ["m1"]},
    ]
    assert StrategicReplyService.build_draft(recommendations, evidence()) == "可以周六见面。"


def test_skips_reply_without_evidence_sources():
    recommendations = [{"id": "r1", "reply": "可以。"}]
    assert StrategicReplyService.build_draft(recommendations, evidence()) is None


def test_skips_reply_with_unknown_evidence_source():
    recommendations = [{"id": "r1", "reply": "可以。", "evidence_source_ids": ["missing"]}]
    assert StrategicReplyService.build_draft(recommendations, evidence()) is None


def test_skips_empty_reply():
    recommendations = [{"id": "r1", "reply": "   ", "evidence_source_ids": ["m1"]}]
    assert StrategicReplyService.build_draft(recommendations, evidence()) is None


def test_preserves_recommendation_order():
    recommendations = [
        {"id": "r1", "reply": "第一候选", "evidence_source_ids": ["m1"]},
        {"id": "r2", "reply": "第二候选", "evidence_source_ids": ["i1"]},
    ]
    assert StrategicReplyService.build_draft(recommendations, evidence()) == "第一候选"


def test_does_not_invent_reply_from_action_only():
    recommendations = [
        {
            "id": "r1",
            "action": "主动联系对方",
            "evidence_source_ids": ["m1"],
        }
    ]
    assert StrategicReplyService.build_draft(recommendations, evidence()) is None


def test_does_not_accept_non_string_recommendation():
    recommendations = [
        None,
        {"id": "r1", "reply": "可以。", "evidence_source_ids": ["m1"]},
    ]
    assert StrategicReplyService.build_draft(recommendations, evidence()) == "可以。"


def test_requires_non_empty_evidence_list():
    recommendations = [{"id": "r1", "reply": "可以。", "evidence_source_ids": []}]
    assert StrategicReplyService.build_draft(recommendations, evidence()) is None


def test_strips_only_outer_whitespace_without_rewriting_content():
    recommendations = [
        {"id": "r1", "reply": "  可以，周六下午有空。  ", "evidence_source_ids": ["m1"]}
    ]
    assert StrategicReplyService.build_draft(recommendations, evidence()) == "可以，周六下午有空。"
