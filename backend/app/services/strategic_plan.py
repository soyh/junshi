"""Build and run the planner call that sits in front of the reply draft.

The planner reads the conversation, the person, the relationship stage and every
uploaded reference in full, then returns a *plan*: what her message means, which
stage we are in, and a few tactics. A tactic may explicitly say "do not send".
Wording happens later, in the existing draft layer.
"""

import json
import sqlite3
from typing import Any

from app.schemas.strategic_plan import PlanOption, StrategicPlan
from app.services.llm import LLMAnalysisError

TRANSCRIPT_LIMIT = 30
REFERENCE_BUDGET = 12_000
REFERENCE_PER_DOC = 6_000


def _clip(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n[已截断]"


def load_references(
    conn: sqlite3.Connection, user_id: str, conversation_id: str
) -> tuple[list[dict[str, str]], list[str]]:
    """Return (selected references, names skipped for budget), skill first.

    Order: skills, then conversation-scoped documents, then global documents.
    The first item is the one allowed to use the largest per-document budget.
    """
    try:
        rows = conn.execute(
            """
            SELECT name, reference_type, content, conversation_id
            FROM model_references
            WHERE user_id = ?
              AND (
                conversation_id IS NULL
                OR conversation_id = ''
                OR conversation_id = ?
              )
            ORDER BY CASE reference_type WHEN 'skill' THEN 0 ELSE 1 END,
                     CASE WHEN conversation_id = ? THEN 0 ELSE 1 END,
                     created_at ASC
            """,
            (user_id, conversation_id, conversation_id),
        ).fetchall()
    except sqlite3.OperationalError:
        return [], []

    selected: list[dict[str, str]] = []
    skipped: list[str] = []
    used = 0
    for row in rows:
        name = str(row["name"] or "未命名资料")
        text = _clip(str(row["content"] or ""), REFERENCE_PER_DOC)
        if not text:
            continue
        if used + len(text) > REFERENCE_BUDGET:
            skipped.append(name)
            continue
        used += len(text)
        selected.append(
            {
                "name": name,
                "type": str(row["reference_type"] or "document"),
                "content": text,
            }
        )
    return selected, skipped


def load_transcript(
    conn: sqlite3.Connection, user_id: str, conversation_id: str
) -> list[dict[str, str]]:
    rows = conn.execute(
        """
        SELECT id, sender_type, content, sent_at
        FROM messages
        WHERE conversation_id = ? AND user_id = ?
        ORDER BY julianday(sent_at) ASC, created_at ASC, rowid ASC
        """,
        (conversation_id, user_id),
    ).fetchall()
    rows = rows[-TRANSCRIPT_LIMIT:]
    out = []
    for row in rows:
        sender = str(row["sender_type"] or "")
        out.append(
            {
                "id": str(row["id"]),
                "who": "我" if sender == "user" else ("她" if sender == "person" else "系统"),
                "text": str(row["content"] or ""),
                "at": str(row["sent_at"] or "")[:16],
            }
        )
    return out


def build_context(
    conn: sqlite3.Connection,
    user_id: str,
    conversation_id: str,
    *,
    channel_rules: str = "",
    self_profile: dict[str, str] | None = None,
    self_style: dict[str, Any] | None = None,
) -> dict[str, Any]:
    conversation = conn.execute(
        "SELECT id, title FROM conversations WHERE id = ? AND user_id = ?",
        (conversation_id, user_id),
    ).fetchone()
    if conversation is None:
        raise ValueError("Conversation not found")
    person = conn.execute(
        """
        SELECT p.id, p.name, p.notes
        FROM conversations c JOIN persons p ON p.id = c.person_id
        WHERE c.id = ? AND p.user_id = ?
        """,
        (conversation_id, user_id),
    ).fetchone()
    relationship = conn.execute(
        """
        SELECT r.stage, r.current_goal, r.long_term_goal, r.status
        FROM conversations c
        JOIN relationships r ON r.person_id = c.person_id AND r.user_id = c.user_id
        WHERE c.id = ? AND r.user_id = ?
        """,
        (conversation_id, user_id),
    ).fetchone()

    transcript = load_transcript(conn, user_id, conversation_id)
    references, skipped = load_references(conn, user_id, conversation_id)
    target = next((item for item in reversed(transcript) if item["who"] == "她"), None)
    return {
        "user_id": user_id,
        "conversation": {"id": conversation_id, "title": conversation["title"]},
        "person": {
            "name": person["name"] if person else "",
            "notes": (person["notes"] or "") if person else "",
        },
        "relationship": {
            "stage": (relationship["stage"] if relationship else "") or "",
            "status": (relationship["status"] if relationship else "") or "",
            "current_goal": (relationship["current_goal"] if relationship else "") or "",
            "long_term_goal": (relationship["long_term_goal"] if relationship else "") or "",
        },
        "transcript": transcript,
        "reply_target_message": target,
        "references": references,
        "references_skipped": skipped,
        "self_profile": {k: v for k, v in (self_profile or {}).items() if str(v).strip()},
        "self_style": self_style or {},
        "channel_rules": (channel_rules or "").strip(),
    }


def _normalise(plan: StrategicPlan, context: dict[str, Any]) -> StrategicPlan:
    """Keep the plan honest: real message ids only, no empty sendable lines."""
    canonical = {item["id"] for item in context.get("transcript") or []}
    target = (context.get("reply_target_message") or {}).get("id")
    options: list[PlanOption] = []
    for option in plan.options:
        ids = [source for source in option.evidence_source_ids if source in canonical]
        if option.send and target and target not in ids:
            ids.append(target)
        if option.send and not option.line.strip():
            option = option.model_copy(update={"send": False})
        options.append(option.model_copy(update={"evidence_source_ids": ids}))
    return plan.model_copy(update={"options": options})


def generate(context: dict[str, Any], *, provider: Any) -> StrategicPlan | None:
    """Ask the provider for a plan. Returns None when the provider cannot plan."""
    method = getattr(provider, "generate_strategic_plan", None)
    if method is None:
        return None
    try:
        raw = method(context)
    except LLMAnalysisError:
        raise
    except Exception:
        raise LLMAnalysisError("LLM strategic plan provider failed") from None
    if not isinstance(raw, dict):
        raise LLMAnalysisError("LLM provider returned a non-object strategic plan")
    try:
        plan = StrategicPlan.model_validate(raw)
    except Exception:
        raise LLMAnalysisError("LLM provider returned invalid strategic plan") from None
    if not plan.options:
        raise LLMAnalysisError("LLM provider returned an empty strategic plan")
    return _normalise(plan, context)


def plan_payload(
    plan: StrategicPlan,
    *,
    used: list[str] | None = None,
    skipped: list[str] | None = None,
) -> dict[str, Any]:
    sendable = plan.sendable()
    return {
        "read": plan.read,
        "signal": plan.signal,
        "stage": plan.stage,
        "goal_this_turn": plan.goal_this_turn,
        "avoid": plan.avoid,
        "confidence": plan.confidence,
        "options": [option.model_dump(mode="json") for option in plan.options],
        "recommended_option_index": (
            plan.options.index(sendable[0]) if sendable else None
        ),
        "send_allowed": bool(sendable),
        "references_used": used or [],
        "references_skipped": skipped or [],
    }


def structured_analysis_from_plan(plan, *, reply_target_id=None):
    """Derive the analysis stage's input from the plan so the draft needs no second read.

    The plan already contains the reading, the tactics and the risks; re-asking the
    analysis model the same question only adds latency. Anything the plan cannot
    support (observed facts, unknowns) stays empty rather than being invented.
    """
    from app.schemas.structured_analysis import StructuredAnalysis, StructuredAnalysisItem

    target = reply_target_id if isinstance(reply_target_id, str) else None
    hypotheses: list[StructuredAnalysisItem] = []
    for option in plan.options:
        ids = list(option.evidence_source_ids)
        if not ids and target:
            ids = [target]
        hypotheses.append(
            StructuredAnalysisItem(
                content=f"{option.tactic}：{option.why}",
                confidence=plan.confidence,
                evidence_source_ids=ids,
                action="send" if option.send else "hold",
            )
        )
    inferences: list[StructuredAnalysisItem] = []
    if plan.read:
        inferences.append(
            StructuredAnalysisItem(
                content=plan.read,
                confidence=plan.confidence,
                evidence_source_ids=[target] if target else [],
            )
        )
    return StructuredAnalysis(
        summary=plan.read or f"{plan.stage}：{plan.goal_this_turn}".strip("："),
        observed_facts=[],
        inferences=inferences,
        unknowns=[],
        hypotheses=hypotheses,
        emotional_signals=[StructuredAnalysisItem(content=f"signal={plan.signal}")],
        relationship_signals=[],
        risk_signals=[StructuredAnalysisItem(content=text) for text in plan.avoid],
        intent_signals=[],
        evidence_links=[],
        analysis_constraints=["plan_derived"],
    )


def save_plan(
    conn: sqlite3.Connection,
    user_id: str,
    conversation_id: str,
    payload: dict[str, Any],
    *,
    target_message_id: str | None = None,
) -> None:
    """Remember the latest plan so the pages and the bridge can show it later."""
    try:
        conn.execute(
            """
            INSERT INTO strategic_reply_plans
                (conversation_id, user_id, target_message_id, payload, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(conversation_id) DO UPDATE SET
                user_id = excluded.user_id,
                target_message_id = excluded.target_message_id,
                payload = excluded.payload,
                created_at = CURRENT_TIMESTAMP
            """,
            (
                conversation_id,
                user_id,
                target_message_id,
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        conn.commit()
    except sqlite3.OperationalError:
        return


def load_plan(
    conn: sqlite3.Connection, user_id: str, conversation_id: str
) -> dict[str, Any] | None:
    """Return the stored plan payload plus its timestamp, or None."""
    try:
        row = conn.execute(
            """
            SELECT payload, target_message_id, created_at
            FROM strategic_reply_plans
            WHERE conversation_id = ? AND user_id = ?
            """,
            (conversation_id, user_id),
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    if row is None:
        return None
    try:
        payload = json.loads(row["payload"])
    except (TypeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    payload["created_at"] = row["created_at"]
    payload["target_message_id"] = row["target_message_id"]
    return payload


def create_plan(
    conn: sqlite3.Connection,
    context: dict[str, Any],
    *,
    provider: Any,
) -> tuple[StrategicPlan, dict[str, Any], bool]:
    """Plan once per target message: reuse the stored plan when nothing new arrived.

    Returns (plan, payload, reused). A fresh message invalidates the cache; a
    retry, a re-generate or a second channel reading the same turn does not.
    """
    target = (context.get("reply_target_message") or {}).get("id")
    if target:
        stored = load_plan(conn, context["user_id"], context["conversation"]["id"])
        if stored and stored.get("target_message_id") == target:
            try:
                plan = StrategicPlan.model_validate(
                    {key: stored[key] for key in stored if key in StrategicPlan.model_fields}
                )
            except Exception:
                plan = None
            if plan is not None:
                return plan, stored, True
    plan = generate(context, provider=provider)
    if plan is None:
        raise LLMAnalysisError("LLM provider cannot produce a strategic plan")
    payload = plan_payload(
        plan,
        used=[item["name"] for item in context.get("references") or []],
        skipped=context.get("references_skipped") or [],
    )
    return plan, payload, False


def context_for_prompt(context: dict[str, Any]) -> str:
    """Serialise the planner input. References go last so they stay readable."""
    payload = {
        key: value
        for key, value in context.items()
        if key not in {"references", "references_skipped", "user_id"}
    }
    lines = [
        "# 对话与背景",
        json.dumps(payload, ensure_ascii=False, indent=1),
        "",
        "# 参考资料（方法论，可引用其打法，不能当作对话事实）",
    ]
    for item in context.get("references") or []:
        lines.append(f"## {item['name']}（{item['type']}）")
        lines.append(item["content"])
        lines.append("")
    return "\n".join(lines)
