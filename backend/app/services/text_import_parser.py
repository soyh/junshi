import re
from datetime import datetime, timezone

from app.schemas.text_import import TextImportCandidate


LINE_PATTERN = re.compile(
    r"^\s*(?P<sent_at>[^|]+?)\s*\|\s*(?P<sender_type>[^|]+?)\s*\|\s*(?P<content>.+?)\s*$"
)

VALID_SENDER_TYPES = {"user", "person", "system", "assistant"}


def parse_text(text: str) -> list[TextImportCandidate]:
    if not text.strip():
        raise ValueError("Import text cannot be empty")

    candidates: list[TextImportCandidate] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue

        match = LINE_PATTERN.match(line)
        if match is None:
            raise ValueError(
                f"Invalid import format at line {line_number}"
            )

        candidates.append(
            TextImportCandidate(
                line_number=line_number,
                sent_at=match.group("sent_at").strip(),
                sender_type=match.group("sender_type").strip(),
                content=match.group("content").strip(),
            )
        )

    if not candidates:
        raise ValueError("Import text contains no messages")

    return candidates


def validate_candidates(
    candidates: list[TextImportCandidate],
) -> list[TextImportCandidate]:
    previous: datetime | None = None

    for candidate in candidates:
        if candidate.sender_type not in VALID_SENDER_TYPES:
            raise ValueError(
                f"Invalid message sender type at line {candidate.line_number}"
            )

        if not candidate.content.strip():
            raise ValueError(
                f"Message content cannot be empty at line {candidate.line_number}"
            )

        try:
            parsed = datetime.fromisoformat(
                candidate.sent_at.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise ValueError(
                f"Invalid timestamp at line {candidate.line_number}"
            ) from exc

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        if previous is not None and parsed < previous:
            raise ValueError(
                "Import messages must be ordered by sent_at"
            )

        previous = parsed

    return candidates
