from __future__ import annotations

import sqlite3
from typing import Any

from app.services.model_reference import ModelReferenceService


def attach_model_reference_context(
    service: ModelReferenceService,
    conn: object,
    user_id: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Attach user references when a migrated database connection is available.

    A few legacy service unit tests intentionally use lightweight fake connections or
    bare in-memory SQLite databases without running migrations. Those contexts mean
    "no persisted reference library" and remain valid. Production startup/readiness
    still requires the real migrations, and any SQL failure other than the missing
    TEST-197 table is allowed to propagate.
    """

    if not hasattr(conn, "execute"):
        return dict(context)

    try:
        return service.attach_context(conn, user_id, context)  # type: ignore[arg-type]
    except sqlite3.OperationalError as exc:
        if "no such table: model_reference_assets" in str(exc).lower():
            return dict(context)
        raise
