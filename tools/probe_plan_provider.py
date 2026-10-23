import json
import sqlite3
import sys

sys.path.insert(0, "/opt/ai-love-strategist")
from app.services.llm_provider_config import LLMProviderConfigService

conn = sqlite3.connect("data/app.sqlite3")
conn.row_factory = sqlite3.Row
user_id = "58ae55e6-1ce6-4da4-8bbf-c5cdd7597992"
provider = LLMProviderConfigService().build_provider(conn, user_id)
print("model", provider.model, type(provider).__name__, flush=True)
context = {
    "conversation": {"id": "c1", "title": "测试"},
    "person": {"name": "小美", "notes": ""},
    "relationship": {"stage": "刚认识", "status": "active", "current_goal": "约出来"},
    "transcript": [
        {"id": "m1", "who": "我", "content": "在忙吗", "sent_at": "2026-10-22 20:00"},
        {"id": "m2", "who": "她", "content": "刚下班，怎么啦", "sent_at": "2026-10-22 20:05"},
    ],
    "reply_target_message": {"id": "m2", "content": "刚下班，怎么啦"},
    "references": [],
    "references_skipped": [],
    "self_profile": {},
    "self_style": {},
    "channel_rules": "",
}
try:
    plan = provider.generate_strategic_plan(context)
    print("ok", json.dumps(plan, ensure_ascii=False)[:600], flush=True)
except Exception as exc:
    print("error", type(exc).__name__, str(exc)[:600], flush=True)
