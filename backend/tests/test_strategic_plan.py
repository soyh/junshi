"""The planner ("marshal") stage: references, normalisation and the hold path."""

import json
import sqlite3

import pytest
from pydantic import ValidationError

from app.schemas.strategic_plan import PlanOption, StrategicPlan
from app.services import strategic_plan
from app.services.analysis_strategic_reply import (
    AnalysisStrategicReplyService,
    _strategic_plan_enabled,
)
from app.services.llm import LLMAnalysisError


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE user_profiles (
            user_id TEXT PRIMARY KEY,
            nickname TEXT NOT NULL DEFAULT '',
            gender TEXT NOT NULL DEFAULT '',
            birth_year TEXT NOT NULL DEFAULT '',
            city TEXT NOT NULL DEFAULT '',
            hometown TEXT NOT NULL DEFAULT '',
            current_location TEXT NOT NULL DEFAULT '',
            work_address TEXT NOT NULL DEFAULT '',
            job TEXT NOT NULL DEFAULT '',
            hobbies TEXT NOT NULL DEFAULT '',
            relationship_status TEXT NOT NULL DEFAULT '',
            about TEXT NOT NULL DEFAULT '',
            reply_rules TEXT NOT NULL DEFAULT '',
            auto_send_authorized INTEGER NOT NULL DEFAULT 0,
            wechat_id TEXT NOT NULL DEFAULT '',
            contact_handoff_enabled INTEGER NOT NULL DEFAULT 0,
            strategic_plan_enabled INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE persons (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT,
            notes TEXT,
            tags TEXT,
            wechat_id TEXT
        );
        CREATE TABLE conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            person_id TEXT,
            title TEXT
        );
        CREATE TABLE relationships (
            user_id TEXT NOT NULL,
            person_id TEXT NOT NULL,
            stage TEXT,
            current_goal TEXT,
            long_term_goal TEXT,
            status TEXT
        );
        CREATE TABLE messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            sender_type TEXT,
            content TEXT,
            sent_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE model_references (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            reference_type TEXT NOT NULL DEFAULT 'document',
            content TEXT NOT NULL DEFAULT '',
            conversation_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE strategic_reply_plans (
            conversation_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            target_message_id TEXT,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.execute(
        "INSERT INTO user_profiles (user_id) VALUES ('u1')"
    )
    conn.execute(
        "INSERT INTO persons (id, user_id, name, notes, tags)"
        " VALUES ('p1', 'u1', '小美', '喜欢猫', '同事')"
    )
    conn.execute(
        "INSERT INTO conversations (id, user_id, person_id, title)"
        " VALUES ('c1', 'u1', 'p1', '和小美')"
    )
    conn.execute(
        "INSERT INTO relationships (user_id, person_id, stage, current_goal,"
        " long_term_goal, status) VALUES ('u1', 'p1', '刚认识', '约出来', '交往', 'active')"
    )
    conn.execute(
        "INSERT INTO messages (id, conversation_id, user_id, sender_type, content, sent_at)"
        " VALUES ('m1', 'c1', 'u1', 'person', '在吗', '2026-10-20 10:00:00')"
    )
    conn.commit()
    return conn


def _add_reference(conn, name, kind, content, conversation_id=None):
    conn.execute(
        "INSERT INTO model_references (user_id, name, reference_type, content,"
        " conversation_id) VALUES ('u1', ?, ?, ?, ?)",
        (name, kind, content, conversation_id),
    )
    conn.commit()


def test_references_load_skill_first_then_conversation_documents():
    conn = _conn()
    _add_reference(conn, "旧文档", "document", "通用背景", None)
    _add_reference(conn, "军师手册", "skill", "开场要轻", None)
    _add_reference(conn, "这段聊天纪要", "document", "只属于本次", "c1")

    refs, skipped = strategic_plan.load_references(conn, "u1", "c1")

    assert [item["name"] for item in refs] == ["军师手册", "这段聊天纪要", "旧文档"]
    assert skipped == []


def test_references_exclude_other_conversations_and_other_accounts():
    conn = _conn()
    _add_reference(conn, "别人的笔记", "document", "不该出现", "c2")
    conn.execute(
        "INSERT INTO model_references (user_id, name, reference_type, content)"
        " VALUES ('u2', '别的账号', 'document', '不该出现')"
    )
    _add_reference(conn, "我的笔记", "document", "该出现", "c1")

    refs, _ = strategic_plan.load_references(conn, "u1", "c1")

    assert [item["name"] for item in refs] == ["我的笔记"]


def test_references_respect_budget_and_per_document_cap():
    conn = _conn()
    _add_reference(conn, "长文", "document", "字" * 20_000, None)

    refs, skipped = strategic_plan.load_references(conn, "u1", "c1")

    assert len(refs) == 1
    assert refs[0]["content"].endswith("[已截断]")
    assert len(refs[0]["content"]) <= strategic_plan.REFERENCE_PER_DOC + 8
    assert skipped == []


def test_references_over_budget_are_skipped_not_truncated_silently():
    conn = _conn()
    filler = "字" * 5_500
    for index in range(3):
        _add_reference(conn, f"文{index}", "document", filler, None)

    refs, skipped = strategic_plan.load_references(conn, "u1", "c1")

    assert len(refs) * 5_500 <= strategic_plan.REFERENCE_BUDGET
    assert len(refs) + len(skipped) == 3
    assert skipped


class _Provider:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def generate_strategic_plan(self, context):
        self.calls.append(context)
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


def _plan_payload(**option_overrides):
    option = {
        "tactic": "顺着聊",
        "why": "她主动开场，接住即可",
        "line": "在，刚忙完，你呢",
        "send": True,
        "source": "军师手册",
        "risk": "显得太闲",
        "evidence_source_ids": ["not-a-real-id"],
    }
    option.update(option_overrides)
    return {
        "read": "她主动找人聊天，情绪平稳",
        "signal": "green",
        "stage": "刚认识",
        "goal_this_turn": "接住话题",
        "options": [option],
        "avoid": ["连发三条"],
        "confidence": 0.7,
    }


def test_generate_keeps_only_canonical_evidence_ids_and_adds_the_target():
    conn = _conn()
    context = strategic_plan.build_context(conn, "u1", "c1")
    provider = _Provider(_plan_payload())

    plan = strategic_plan.generate(context, provider=provider)

    assert plan is not None
    assert plan.options[0].evidence_source_ids == ["m1"]
    assert provider.calls and provider.calls[0]["reply_target_message"]["id"] == "m1"


def test_generate_never_keeps_a_send_option_without_a_line():
    conn = _conn()
    context = strategic_plan.build_context(conn, "u1", "c1")

    plan = strategic_plan.generate(context, provider=_Provider(_plan_payload(line="   ")))

    assert plan is not None
    assert plan.options[0].send is False
    assert plan.sendable() == []


def test_generate_rejects_an_empty_plan():
    conn = _conn()
    context = strategic_plan.build_context(conn, "u1", "c1")
    payload = _plan_payload()
    payload["options"] = []

    with pytest.raises(LLMAnalysisError):
        strategic_plan.generate(context, provider=_Provider(payload))


def test_plan_payload_reports_hold_when_nothing_is_sendable():
    plan = StrategicPlan.model_validate(
        {
            "read": "她在冷处理",
            "signal": "red",
            "options": [
                {"tactic": "收线", "why": "再发就是消耗", "line": "", "send": False}
            ],
        }
    )

    payload = strategic_plan.plan_payload(plan, used=["军师手册"], skipped=["旧文档"])

    assert payload["send_allowed"] is False
    assert payload["recommended_option_index"] is None
    assert payload["references_used"] == ["军师手册"]
    assert payload["references_skipped"] == ["旧文档"]


def test_plan_payload_points_at_the_recommended_sendable_option():
    plan = StrategicPlan.model_validate(
        {
            "read": "可以推进",
            "signal": "green",
            "options": [
                {"tactic": "静默", "why": "太早", "line": "", "send": False},
                {"tactic": "约咖啡", "why": "有来有回", "line": "周末喝咖啡？"},
            ],
        }
    )

    payload = strategic_plan.plan_payload(plan)

    assert payload["send_allowed"] is True
    assert payload["recommended_option_index"] == 1
    assert payload["options"][1]["tactic"] == "约咖啡"


def test_plan_rejects_more_than_four_tactics():
    with pytest.raises(ValidationError):
        StrategicPlan.model_validate(
            {
                "read": "x",
                "options": [
                    {"tactic": f"t{index}", "why": "w", "line": "l"} for index in range(5)
                ],
            }
        )


def test_plan_option_strips_pasted_whitespace():
    option = PlanOption.model_validate({"tactic": "  顺着聊 ", "why": "  接住 ", "line": " 在  "})

    assert option.tactic == "顺着聊"
    assert option.why == "接住"
    assert option.line == "在"


def test_planner_context_serialises_references_after_the_facts():
    context = {
        "person": {"name": "小美"},
        "transcript": [{"id": "m1", "who": "她", "text": "在吗"}],
        "references": [{"name": "军师手册", "type": "skill", "content": "开场要轻"}],
        "references_skipped": [],
    }

    prompt = strategic_plan.context_for_prompt(context)

    assert prompt.index("# 对话与背景") < prompt.index("# 参考资料")
    assert "开场要轻" in prompt
    assert "references_skipped" not in prompt


def test_planner_flag_defaults_on_and_can_be_turned_off():
    conn = _conn()
    assert _strategic_plan_enabled(conn, "u1") is True

    conn.execute("UPDATE user_profiles SET strategic_plan_enabled = 0 WHERE user_id = 'u1'")
    conn.commit()

    assert _strategic_plan_enabled(conn, "u1") is False


class _AnalysisService:
    calls = 0

    @staticmethod
    def get_context(conn, user_id, conversation_id):
        _AnalysisService.calls += 1
        return {
            "person": {"id": "p1", "name": "小美"},
            "conversation": {"id": conversation_id},
            "messages": [
                {"id": "m1", "sender_type": "person", "content": "在吗"},
            ],
            "model_references": None,
        }


class _AnalysisLLM:
    analysis_service = _AnalysisService

    @staticmethod
    def analyze_context(context, provider=None):
        # Reaching this proves the caller fell back to the classic chain.
        raise AssertionError("fell back to the classic chain")


def test_hold_plan_returns_without_running_analysis_or_draft(monkeypatch):
    conn = _conn()
    service = AnalysisStrategicReplyService(analysis_llm_service=_AnalysisLLM)
    monkeypatch.setattr(
        service.analysis_recommendation_service, "build_context", _boom, raising=False
    )
    monkeypatch.setattr(service.strategic_reply_llm_service, "generate", _boom, raising=False)
    provider = _Provider(
        {
            "read": "她连发三条你没回，再发只会更糟",
            "signal": "red",
            "options": [
                {"tactic": "先停", "why": "需求感已经很高", "line": "", "send": False}
            ],
            "avoid": ["解释", "追问"],
        }
    )

    result = service.build_context(conn, "u1", "c1", provider=provider)

    assert result["draft"] is None
    assert result["plan"]["send_allowed"] is False
    assert result["plan"]["options"][0]["tactic"] == "先停"
    assert result["recommendations"] == []


def _boom(*args, **kwargs):
    raise AssertionError("the hold path must not run analysis or draft")


def test_planner_failure_falls_back_to_the_classic_chain(monkeypatch):
    conn = _conn()
    service = AnalysisStrategicReplyService(analysis_llm_service=_AnalysisLLM)
    monkeypatch.setattr(
        strategic_plan, "generate",
        lambda context, provider: (_ for _ in ()).throw(LLMAnalysisError("planner down")),
    )
    monkeypatch.setattr(
        service.analysis_recommendation_service, "build_context", _boom, raising=False
    )

    with pytest.raises(AssertionError):
        service.build_context(conn, "u1", "c1", provider=_Provider({}))


def test_option_skips_the_planner_call(monkeypatch):
    conn = _conn()
    service = AnalysisStrategicReplyService(analysis_llm_service=_AnalysisLLM)
    called = {"plan": 0}

    def _count(context, provider):
        called["plan"] += 1
        raise LLMAnalysisError("should not run")

    monkeypatch.setattr(strategic_plan, "generate", _count)
    monkeypatch.setattr(
        service.analysis_recommendation_service, "build_context", _boom, raising=False
    )

    with pytest.raises(AssertionError):
        service.build_context(
            conn, "u1", "c1", provider=_Provider({}),
            option={"tactic": "顺着聊", "why": "w", "line": "在", "send": True},
        )
    assert called["plan"] == 0


def test_structured_analysis_from_plan_reuses_the_tactics_without_inventing_facts():
    plan = StrategicPlan.model_validate(
        {
            "read": "她只回了两个字，热度在降",
            "signal": "yellow",
            "options": [
                {
                    "tactic": "降压收线",
                    "why": "再追会更冷",
                    "line": "行，那你先忙",
                    "send": True,
                    "evidence_source_ids": [],
                },
                {"tactic": "先停", "why": "等她主动", "line": "", "send": False},
            ],
            "avoid": ["连发三条"],
            "confidence": 0.6,
        }
    )

    analysis = strategic_plan.structured_analysis_from_plan(plan, reply_target_id="m9")

    assert analysis.summary == "她只回了两个字，热度在降"
    assert [item.action for item in analysis.hypotheses] == ["send", "hold"]
    assert analysis.hypotheses[0].evidence_source_ids == ["m9"]
    assert analysis.observed_facts == []
    assert analysis.analysis_constraints == ["plan_derived"]
    assert [item.content for item in analysis.risk_signals] == ["连发三条"]


def test_plan_replaces_the_second_analysis_read_on_the_first_attempt():
    service = AnalysisStrategicReplyService(analysis_llm_service=_AnalysisLLM)
    plan = StrategicPlan.model_validate(
        {"read": "可以接住", "options": [{"tactic": "顺着聊", "why": "她主动", "line": "在呢"}]}
    )
    analysis = strategic_plan.structured_analysis_from_plan(plan, reply_target_id="m1")

    first = service._analysis_for_attempt(0, analysis, {"messages": []}, provider=None)

    assert first is analysis
    # Attempt 1 must still be able to ask the model when the fast path was rejected.
    with pytest.raises(AssertionError):
        service._analysis_for_attempt(1, analysis, {"messages": []}, provider=None)


def test_hold_payload_survives_response_model_validation():
    from app.schemas.analysis_strategic_reply import (
        AnalysisStrategicReplyContextResponse,
    )

    conn = _conn()
    service = AnalysisStrategicReplyService(analysis_llm_service=_AnalysisLLM)
    provider = _Provider(
        {
            "read": "她说别再发了",
            "signal": "red",
            "options": [{"tactic": "收线", "why": "边界已明确", "line": "", "send": False}],
        }
    )

    result = service.build_context(conn, "u1", "c1", provider=provider)

    validated = AnalysisStrategicReplyContextResponse.model_validate(result)
    assert validated.draft is None
    assert validated.structured_analysis.summary == "她说别再发了"


def _send_plan(**overrides):
    payload = {
        "read": "她在接话",
        "signal": "green",
        "stage": "刚认识",
        "goal_this_turn": "接住并抛回",
        "options": [{"tactic": "顺着聊", "why": "她主动", "line": "在呢"}],
    }
    payload.update(overrides)
    return payload


def test_plan_is_stored_and_read_back_with_its_target():
    conn = _conn()
    context = strategic_plan.build_context(conn, "u1", "c1")
    plan = strategic_plan.generate(context, provider=_Provider(_send_plan()))
    payload = strategic_plan.plan_payload(plan)

    strategic_plan.save_plan(conn, "u1", "c1", payload, target_message_id="m1")
    stored = strategic_plan.load_plan(conn, "u1", "c1")

    assert stored["read"] == "她在接话"
    assert stored["target_message_id"] == "m1"
    assert stored["created_at"]
    assert strategic_plan.load_plan(conn, "u2", "c1") is None


def test_same_target_reuses_the_stored_plan_without_calling_the_model():
    conn = _conn()
    context = strategic_plan.build_context(conn, "u1", "c1")
    plan = strategic_plan.generate(context, provider=_Provider(_send_plan()))
    strategic_plan.save_plan(
        conn, "u1", "c1", strategic_plan.plan_payload(plan), target_message_id="m1"
    )

    reused_plan, payload, reused = strategic_plan.create_plan(
        conn, context, provider=_Provider({})  # an empty answer would fail validation
    )

    assert reused is True
    assert reused_plan.read == "她在接话"
    assert payload["target_message_id"] == "m1"


def test_a_new_message_invalidates_the_stored_plan():
    conn = _conn()
    context = strategic_plan.build_context(conn, "u1", "c1")
    plan = strategic_plan.generate(context, provider=_Provider(_send_plan()))
    strategic_plan.save_plan(
        conn, "u1", "c1", strategic_plan.plan_payload(plan), target_message_id="m-old"
    )

    fresh_plan, payload, reused = strategic_plan.create_plan(
        conn, context, provider=_Provider(_send_plan(read="她又追问了一句"))
    )

    assert reused is False
    assert fresh_plan.read == "她又追问了一句"
    assert payload["read"] == "她又追问了一句"


def _memory_conn() -> sqlite3.Connection:
    conn = _conn()
    conn.executescript(
        """
        CREATE TABLE person_memories (
            person_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            summary_json TEXT,
            coverage_json TEXT,
            updated_at TEXT,
            PRIMARY KEY (person_id, user_id)
        );
        """
    )
    return conn


def test_long_term_archive_reaches_the_planner_within_a_budget():
    conn = _memory_conn()
    conn.execute(
        "INSERT INTO person_memories VALUES (?,?,?,?,?)",
        (
            "p1",
            "u1",
            json.dumps(
                {
                    "facts": ["在杭州做设计", "养了一只叫豆豆的猫"],
                    "preferences": ["不喜欢被追问年龄"],
                    "unknowns": ["真名"],
                },
                ensure_ascii=False,
            ),
            "{}",
            "2026-10-24T00:00:00+00:00",
        ),
    )

    memory = strategic_plan.load_memory(conn, "u1", "p1")

    texts = [row["text"] for row in memory["entries"]]
    assert "在杭州做设计" in texts
    assert "不喜欢被追问年龄" in texts
    assert memory["updated_at"] == "2026-10-24T00:00:00+00:00"


def test_long_term_archive_is_trimmed_to_the_character_budget():
    conn = _memory_conn()
    long_text = "很长的条目" * 200
    conn.execute(
        "INSERT INTO person_memories VALUES (?,?,?,?,?)",
        ("p1", "u1", json.dumps({"facts": [long_text]}, ensure_ascii=False), "{}", "now"),
    )

    assert strategic_plan.load_memory(conn, "u1", "p1", limit_chars=50) == {}
    assert strategic_plan.load_memory(conn, "u1", "p1", limit_chars=5_000)["entries"]


def test_missing_archive_does_not_break_the_planner():
    conn = _memory_conn()
    assert strategic_plan.load_memory(conn, "u1", "p1") == {}
    assert strategic_plan.load_memory(conn, "u1", "") == {}


def test_planner_context_carries_the_archive():
    conn = _memory_conn()
    conn.execute(
        "INSERT INTO person_memories VALUES (?,?,?,?,?)",
        ("p1", "u1", json.dumps({"facts": ["喜欢爬山"]}, ensure_ascii=False), "{}", "now"),
    )

    context = strategic_plan.build_context(conn, "u1", "c1")

    assert context["long_term_memory"]["entries"][0]["text"] == "喜欢爬山"
    assert "喜欢爬山" in strategic_plan.context_for_prompt(context)


def test_planner_context_carries_the_handoff_only_after_opt_in():
    conn = _conn()
    conn.execute("UPDATE persons SET wechat_id = 'her_wx_88' WHERE id = 'p1'")

    off = strategic_plan.build_context(conn, "u1", "c1")
    assert off["contact_handoff"] == {
        "enabled": False,
        "my_wechat": "",
        "their_wechat": "her_wx_88",
    }

    conn.execute(
        "UPDATE user_profiles SET wechat_id = 'lin_xiao96', contact_handoff_enabled = 1"
        " WHERE user_id = 'u1'"
    )
    on = strategic_plan.build_context(conn, "u1", "c1")
    assert on["contact_handoff"] == {
        "enabled": True,
        "my_wechat": "lin_xiao96",
        "their_wechat": "her_wx_88",
    }
