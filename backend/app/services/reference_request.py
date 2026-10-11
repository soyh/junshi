"""Reference selection and deduplication at the provider boundary (no DB access)."""
from copy import deepcopy

from app.services.reference_retrieval import MAX_SELECTED, MAX_SKILLS


def prepare_context(context: dict, selector) -> dict:
    result = deepcopy(context)
    refs = result.get("model_references")
    if not isinstance(refs, dict):
        return result
    candidates = refs.get("candidates")
    if isinstance(candidates, list):
        pool = {item["reference_id"]: item for item in candidates}
        selected = [item["reference_id"] for item in refs.get("items", [])]
        report = refs.get("retrieval", {})
        mode = "local_fallback"
        if report.get("query") and refs.get("catalog"):
            proposed = selector(refs["catalog"], report["query"])
            if (isinstance(proposed, list) and len(proposed) <= MAX_SELECTED
                    and all(isinstance(key, str) and key in pool for key in proposed)):
                selected, mode = list(dict.fromkeys(proposed)), "model_catalog"
        skills = [key for key, item in pool.items() if item["type"] == "skill"][:MAX_SKILLS]
        selected = list(dict.fromkeys(skills + selected))[:MAX_SELECTED + MAX_SKILLS]
        refs["items"] = [pool[key] for key in selected if key in pool]
        refs["count"] = len(refs["items"])
        refs["retrieval"] = {**report, "mode": mode, "selected_ids": selected}
        refs["retrieval"].pop("query", None)
        refs.pop("candidates", None)
        refs.pop("catalog", None)
    # The reply pipeline repeats references inside conversation_focus and other
    # derived contexts. Preserve conversation evidence, carry reference bodies once.
    def deduplicate(value):
        if isinstance(value, dict):
            return {key: ({"same_as": "root.model_references"} if key == "model_references"
                          else deduplicate(child)) for key, child in value.items()}
        if isinstance(value, list):
            return [deduplicate(child) for child in value]
        return value
    return {key: refs if key == "model_references" else deduplicate(value)
            for key, value in result.items()}


def reduce_references(context: dict) -> bool:
    refs = context.get("model_references")
    if not isinstance(refs, dict) or not refs.get("items"):
        return False
    # Trim secondary material only. Never silently discard canonical chat evidence.
    items = refs["items"]
    largest = max(items, key=lambda item: len(item.get("content", "")))
    text = largest.get("content", "")
    if len(text) > 256:
        largest["content"] = text[:len(text) // 2]
        largest["truncated"] = True
    else:
        items.remove(largest)
    refs["count"] = len(items)
    report = refs.setdefault("retrieval", {})
    report["budget_reduced"] = True
    report["selected_ids"] = [item["reference_id"] for item in items]
    return True
