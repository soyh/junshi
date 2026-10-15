"""Bounded, local retrieval. Uploaded names are identifiers, never filesystem paths."""
from __future__ import annotations

import re
import unicodedata
from urllib.parse import unquote


MAX_CANDIDATES = 24  # compatibility constant; full enabled catalog is no longer sliced
MAX_SELECTED = 6
MAX_SKILLS = 2
EXCERPT_CHARS = 1800


def terms(text: str) -> set[str]:
    text = text.casefold()
    result = set(re.findall(r"[a-z0-9_]{2,}", text))
    for run in re.findall(r"[\u3400-\u9fff]+", text):
        result.update(run[i:i + 2] for i in range(len(run) - 1))
    return result


def filename(value: str) -> str:
    return unicodedata.normalize("NFC", unquote(value).replace("\\", "/").rsplit("/", 1)[-1]).strip().casefold()


def retrieve(library: list[dict], query: str) -> dict:
    """Rank all enabled documents, including their tails, with a complete enabled catalog."""
    query = query[-2400:]
    needles = terms(query)
    aliases: dict[str, set[str]] = {}
    for item in library:
        for name in (item["name"], item.get("original_filename")):
            if name:
                aliases.setdefault(filename(name), set()).add(item["reference_id"])

    topics: dict[str, list[str]] = {}
    category_labels = {}
    explicit_ids = {item["reference_id"] for item in library if item.get("is_guide")}
    warnings = []
    guides = {item["reference_id"] for item in library if item.get("is_guide")}
    automatic_guides = set()
    links = []
    for item in library:
        for line_number, line in enumerate(item["content"].splitlines(), 1):
            targets = re.findall(r"`([^`\n]+\.(?:md|markdown|txt|skill|docx))`|\[[^\]]*\]\(([^)]+)\)", line, re.I)
            for code, link in targets:
                target = code or link
                if "://" in target or target.startswith("#"):
                    continue
                matches = aliases.get(filename(target.split("#", 1)[0]), set())
                automatic_guides.add(item["reference_id"])
                source = {"source_id": item["reference_id"], "source_name": item["name"], "line": line_number}
                links.append({**source, "filename": target[:200], "matched_ids": sorted(matches)})
                if len(matches) == 1:
                    key = next(iter(matches))
                    topics.setdefault(key, []).append(line[:300])
                    if not explicit_ids or item["reference_id"] in explicit_ids:
                        label = re.split(r"`|\[[^\]]*\]\(", line, maxsplit=1)[0].strip(" -：:;；")[:160]
                        if label:
                            category_labels.setdefault(key, set()).add(label)
                else:
                    warnings.append({**source, "filename": target[:200], "reason": "ambiguous" if matches else "not_enabled_or_missing"})

    explicit_guides = bool(guides)
    if not explicit_guides:
        guides = automatic_guides
    scored = []
    for index, item in enumerate(library):
        content = item["content"]
        chunks = [(start, content[start:start + 900]) for start in range(0, len(content), 800)] or [(0, "")]
        ranked = sorted(chunks, key=lambda pair: (-len(needles & terms(pair[1])), pair[0]))
        best = ranked[:2] if needles else chunks[:2]
        best = sorted(best)
        # Preserve the opening methodology for skills; do not substitute a mid-file snippet.
        if item["type"] == "skill":
            excerpt = content[:EXCERPT_CHARS]
            offsets = [0]
        elif len(content) <= EXCERPT_CHARS:
            excerpt, offsets = content, [0]
        else:
            excerpt = "\n[...片段间省略...]\n".join(part for _, part in best)[:EXCERPT_CHARS]
            offsets = [start for start, _ in best]
        topic_text = "\n".join(topics.get(item["reference_id"], []))[:900]
        score = 4 * len(needles & terms(item["name"] + " " + topic_text))
        score += max((len(needles & terms(part)) for _, part in chunks), default=0)
        result = {**item, "content": excerpt, "description": (item.get("description") or "")[:200],
                  "truncated": len(excerpt) < len(content), "chunk_offsets": offsets}
        scored.append((score, index, result, topic_text))

    skills = [x for x in scored if x[2]["type"] == "skill"][:MAX_SKILLS]
    ranked = sorted(scored, key=lambda x: (-x[0], x[1]))
    guide_items = [x for x in scored if x[2]["reference_id"] in guides and x not in skills][:2]
    reserved = skills + guide_items
    candidates = reserved + [x for x in ranked if x not in reserved]
    defaults = skills + [x for x in candidates if x not in skills][:MAX_SELECTED]
    # Public preview stays in stable user priority order.
    defaults.sort(key=lambda x: x[1])
    return {
        "items": [x[2] for x in defaults],
        "candidates": [x[2] for x in candidates],
        "catalog": [{"reference_id": x[2]["reference_id"], "name": x[2]["name"][:200],
                     "type": x[2]["type"], "topics": x[3][:300],
                     "topic_labels": sorted(category_labels.get(x[2]["reference_id"], set())),
                     "description": x[2]["description"], "is_guide": x[2]["reference_id"] in guides}
                    for x in candidates],
        "retrieval": {"mode": "local_preview", "enabled_count": len(library),
                      "candidate_count": len(candidates), "omitted_from_catalog": len(library) - len(candidates),
                      "guide_count": len(guides), "guide_mode": "explicit" if explicit_guides else "automatic_compatibility",
                      "warnings": warnings, "links": links,
                      "query": query, "selected_ids": [x[2]["reference_id"] for x in defaults],
                      "note": "本地预选；模型还会从候选目录选文档。未入选资料不代表已阅读。"},
    }
