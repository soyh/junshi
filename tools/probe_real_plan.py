import json
import sqlite3
import sys

sys.path.insert(0, "/opt/ai-love-strategist")
from app.services import strategic_plan
from app.services.llm_provider_config import LLMProviderConfigService

conn = sqlite3.connect("data/app.sqlite3")
conn.row_factory = sqlite3.Row
user_id = "58ae55e6-1ce6-4da4-8bbf-c5cdd7597992"
row = conn.execute(
    "SELECT c.id, c.title, MAX(m.sent_at) AS last_at FROM conversations c "
    "JOIN messages m ON m.conversation_id = c.id WHERE c.user_id = ? "
    "GROUP BY c.id ORDER BY last_at DESC LIMIT 1",
    (user_id,),
).fetchone()
print("conversation", row["id"], row["title"], row["last_at"], flush=True)
context = strategic_plan.build_context(conn, user_id, row["id"])
print("transcript", len(context["transcript"]), "refs", [r["name"] for r in context["references"]], flush=True)
provider = LLMProviderConfigService().build_provider(conn, user_id)
plan = strategic_plan.generate(context, provider=provider)
payload = strategic_plan.plan_payload(
    plan, used=[r["name"] for r in context["references"]], skipped=context["references_skipped"]
)
strategic_plan.save_plan(
    conn, user_id, row["id"], payload,
    target_message_id=(context.get("reply_target_message") or {}).get("id"),
)
print(json.dumps(payload, ensure_ascii=False)[:1500], flush=True)
print("stored", strategic_plan.load_plan(conn, user_id, row["id"]) is not None, flush=True)
