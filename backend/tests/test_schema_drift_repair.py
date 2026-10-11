import sqlite3
from pathlib import Path

from app.config.settings import get_settings
from app.core.migrations import run_migrations


def test_014_repairs_action_plan_snapshot_schema_after_version_collision(
    tmp_path: Path,
    monkeypatch,
):
    database = tmp_path / "drifted.sqlite3"
    original_008_applied_at = "2026-09-16 10:49:45"

    with sqlite3.connect(database) as conn:
        conn.execute(
            """
            CREATE TABLE schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        for value in range(1, 14):
            version = f"{value:03d}"
            applied_at = original_008_applied_at if version == "008" else "2026-09-16 00:00:00"
            conn.execute(
                "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (version, applied_at),
            )

    monkeypatch.setenv("DATABASE_PATH", str(database))
    get_settings.cache_clear()

    try:
        run_migrations()
        run_migrations()
    finally:
        get_settings.cache_clear()

    with sqlite3.connect(database) as conn:
        versions = [
            row[0]
            for row in conn.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            ).fetchall()
        ]
        original_008 = conn.execute(
            "SELECT applied_at FROM schema_migrations WHERE version = '008'"
        ).fetchone()
        table = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'action_plan_snapshots'
            """
        ).fetchone()
        index = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'index' AND name = 'idx_action_plan_snapshots_user_person'
            """
        ).fetchone()

    expected_through_014 = [f"{value:03d}" for value in range(1, 15)]
    assert versions[:14] == expected_through_014
    assert versions.count("014") == 1
    assert original_008 is not None
    assert original_008[0] == original_008_applied_at
    assert table == ("action_plan_snapshots",)
    assert index == ("idx_action_plan_snapshots_user_person",)
