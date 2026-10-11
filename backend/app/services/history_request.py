"""Budget only disposable provider snapshots; never edit persisted evidence.

History windows are omissions, not summaries. Current-turn bodies and provenance
are indivisible: if those alone cannot fit, fail rather than silently cut them.
"""
import json


def _size(value):
    return len(json.dumps(value, ensure_ascii=False, default=str).encode("utf-8"))


def _report(context):
    return context.setdefault("history_window", {
        "partial_context": True,
        "policy": (
            "Older context was omitted only from this request, not deleted. "
            "This is not a complete history or a summary. Do not infer absence "
            "of facts from omitted history; preserve uncertainty."
        ),
    })


def _protected_ids(context):
    focus = context.get("conversation_focus") or {}
    protected = set(context.get("required_evidence_source_ids") or [])
    protected.update(focus.get("required_evidence_source_ids") or [])
    for key in ("latest_human_message", "latest_incoming_message", "reply_target_message"):
        item = focus.get(key)
        if isinstance(item, dict) and item.get("id"):
            protected.add(item["id"])
    # Recommendations must retain all their supporting canonical evidence.
    for item in context.get("recommendations") or []:
        if isinstance(item, dict):
            protected.update(item.get("evidence_source_ids") or [])
    return protected


def reduce_history(context, *, aggressive=False):
    """One monotone reduction; normal pass keeps eight recent messages.

Only identified message records may be windowed. Unknown input shapes remain
untouched. An aggressive second pass can keep two recent records, plus every
explicit current-turn/required ID. Message text, IDs and dates are never cut.
"""
    learning = context.get("learning_strategy")
    if isinstance(learning, dict) and isinstance(learning.get("learning_inputs"), dict):
        inputs = learning["learning_inputs"]
        if not inputs.get("omitted_for_input_budget") and _size(inputs) > 2048:
            # These are person-wide derived learning inputs, not current chat.
            # Keep the strategy constraints outside this block unchanged.
            learning["learning_inputs"] = {"omitted_for_input_budget": True}
            _report(context)["person_learning_inputs_omitted"] = True
            return True

    protected = _protected_ids(context)
    keep = 2 if aggressive else 8
    focus = context.get("conversation_focus") or {}
    for owner, key, label in (
        (context, "messages", "messages"),
        (focus, "recent_messages", "focus_messages"),
    ):
        records = owner.get(key)
        if not isinstance(records, list) or len(records) <= keep:
            continue
        if not all(isinstance(x, dict) and isinstance(x.get("id"), str) for x in records):
            continue
        # Drop the oldest half of eligible records, preserving source order.
        removable = [i for i, x in enumerate(records[:-keep]) if x["id"] not in protected]
        if not removable:
            continue
        remove = set(removable[:max(1, (len(removable) + 1) // 2)])
        retained = [x for i, x in enumerate(records) if i not in remove]
        report = _report(context)
        report.setdefault(label + "_original_count", len(records))
        report[label + "_retained_count"] = len(retained)
        report[label + "_omitted_count"] = report[label + "_original_count"] - len(retained)
        owner[key] = retained
        return True

    # Draft contexts repeat recent evidence in the focus; remove only optional
    # canonical records, never recommendation sources or current-turn records.
    evidence = context.get("evidence")
    if isinstance(evidence, list):
        for message in focus.get("recent_messages") or []:
            if isinstance(message, dict):
                protected.add(message.get("id"))
        removable = [i for i, x in enumerate(evidence)
                     if isinstance(x, dict) and x.get("source_id")
                     and x["source_id"] not in protected]
        if removable:
            remove = set(removable[:max(1, (len(removable) + 1) // 2)])
            context["evidence"] = [x for i, x in enumerate(evidence) if i not in remove]
            report = _report(context)
            report.setdefault("evidence_original_count", len(evidence))
            report["evidence_retained_count"] = len(context["evidence"])
            return True
    return False
