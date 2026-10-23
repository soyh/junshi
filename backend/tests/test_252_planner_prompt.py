"""The planner call must actually carry the conversation, not the system text."""

import json

import httpx

from app.services.qwen_provider import QwenProvider

PLAN = {
    "read": "她在接话，可以顺着聊",
    "signal": "green",
    "stage": "刚认识",
    "goal_this_turn": "接住并问一句",
    "options": [
        {"tactic": "顺着聊", "why": "她主动回了", "line": "刚下班就来找我，累不累"}
    ],
    "avoid": ["别追问"],
    "confidence": 0.6,
}


def _context():
    return {
        "user_id": "u1",
        "conversation": {"id": "c1", "title": "和小美"},
        "person": {"name": "小美", "notes": ""},
        "relationship": {"stage": "刚认识", "status": "active", "current_goal": "约出来"},
        "transcript": [
            {"id": "m1", "who": "我", "content": "在忙吗", "sent_at": "2026-10-22 20:00"},
            {"id": "m2", "who": "她", "content": "刚下班，怎么啦", "sent_at": "2026-10-22 20:05"},
        ],
        "reply_target_message": {"id": "m2", "content": "刚下班，怎么啦"},
        "references": [{"name": "军师手册", "type": "skill", "content": "先判断温度再说话"}],
        "references_skipped": [],
        "self_profile": {},
        "self_style": {},
        "channel_rules": "",
    }


def test_planner_sends_the_transcript_and_references():
    seen = {}

    def handler(request):
        payload = json.loads(request.content)
        seen["system"] = payload["messages"][0]["content"]
        seen["user"] = payload["messages"][-1]["content"]
        return httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(PLAN, ensure_ascii=False)}}]}
        )

    provider = QwenProvider(
        api_key="test-only",
        model="qwen3.7-plus",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    plan = provider.generate_strategic_plan(_context())

    assert plan["read"] == PLAN["read"]
    assert "刚下班，怎么啦" in seen["user"]
    assert "军师手册" in seen["user"]
    assert seen["user"] != seen["system"]
    assert "战略" in seen["system"] or "军师" in seen["system"]


def test_planner_shrinks_the_transcript_instead_of_dropping_it(monkeypatch):
    from app.config.settings import get_settings

    monkeypatch.setattr(get_settings(), "llm_input_budget_tokens", 12000)
    sent = []

    def handler(request):
        payload = json.loads(request.content)
        sent.append(payload["messages"][-1]["content"])
        return httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(PLAN, ensure_ascii=False)}}]}
        )

    context = _context()
    context["transcript"] = [
        {"id": f"m{i}", "who": "她", "content": "很长的一句聊天记录" * 40, "sent_at": "2026-10-22 20:00"}
        for i in range(30)
    ]
    provider = QwenProvider(
        api_key="test-only",
        model="qwen3.7-plus",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    provider.generate_strategic_plan(context)

    assert sent
    assert "m29" in sent[-1]
