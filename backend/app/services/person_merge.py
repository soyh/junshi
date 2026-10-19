import json
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4


class PersonMergeError(Exception):
    """Base error for person merge operations."""


class PersonNotFoundForMerge(PersonMergeError):
    pass


class SamePersonMerge(PersonMergeError):
    pass


class PersonMergeService:
    """Merge a duplicate Person into a canonical one.

    Everything that points at the source person is repointed to the target:
    conversations (and their messages, transitively), interactions, media,
    memory/audit rows, platform accounts and the analysis lifecycle tables.
    The source Relationship is either adopted (target has none) or discarded
    after its conversations are moved.
    """

    PERSON_SCOPED_TABLES = (
        "interactions",
        "media_attachments",
        "memory_updates",
        "action_decisions",
        "action_outcomes",
        "action_executions",
        "person_update_events",
    )

    def merge(self, conn: sqlite3.Connection, user_id: str, target_id: str, source_id: str) -> dict:
        if target_id == source_id:
            raise SamePersonMerge("source and target are the same person")

        for person_id in (target_id, source_id):
            row = conn.execute(
                "SELECT id FROM persons WHERE id = ? AND user_id = ?",
                (person_id, user_id),
            ).fetchone()
            if row is None:
                raise PersonNotFoundForMerge(f"person not found: {person_id}")

        counts: dict[str, int] = {}

        target_relationship = conn.execute(
            "SELECT id FROM relationships WHERE user_id = ? AND person_id = ?",
            (user_id, target_id),
        ).fetchone()
        source_relationship = conn.execute(
            "SELECT id FROM relationships WHERE user_id = ? AND person_id = ?",
            (user_id, source_id),
        ).fetchone()

        # Adopt the source relationship when the target has none, otherwise keep
        # the target's and drop the source's after rewiring conversations.
        if source_relationship is not None and target_relationship is None:
            conn.execute(
                "UPDATE relationships SET person_id = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                (target_id, _now(), source_relationship["id"], user_id),
            )
            target_relationship = source_relationship

        target_relationship_id = target_relationship["id"] if target_relationship else None

        cursor = conn.execute(
            """
            UPDATE conversations
            SET person_id = ?, relationship_id = ?, updated_at = ?
            WHERE user_id = ? AND person_id = ?
            """,
            (target_id, target_relationship_id, _now(), user_id, source_id),
        )
        counts["conversations"] = cursor.rowcount

        if (
            source_relationship is not None
            and target_relationship is not None
            and source_relationship["id"] != target_relationship["id"]
        ):
            conn.execute(
                "DELETE FROM relationships WHERE id = ? AND user_id = ?",
                (source_relationship["id"], user_id),
            )
            counts["relationships_merged"] = 1

        for table in self.PERSON_SCOPED_TABLES:
            cursor = conn.execute(
                f"UPDATE {table} SET person_id = ? WHERE user_id = ? AND person_id = ?",
                (target_id, user_id, source_id),
            )
            counts[table] = cursor.rowcount

        # Snapshot rows are unique per (user, person, recommendation): drop the
        # source duplicates that would collide with existing target rows.
        duplicate_rows = conn.execute(
            """
            DELETE FROM action_plan_snapshots
            WHERE user_id = ? AND person_id = ? AND recommendation_id IN (
                SELECT recommendation_id FROM action_plan_snapshots
                WHERE user_id = ? AND person_id = ?
            )
            """,
            (user_id, source_id, user_id, target_id),
        )
        counts["action_plan_snapshots_dropped"] = duplicate_rows.rowcount
        cursor = conn.execute(
            "UPDATE action_plan_snapshots SET person_id = ? WHERE user_id = ? AND person_id = ?",
            (target_id, user_id, source_id),
        )
        counts["action_plan_snapshots"] = cursor.rowcount

        # person_memories is keyed by person_id: keep the target's memory.
        target_memory = conn.execute(
            "SELECT 1 FROM person_memories WHERE user_id = ? AND person_id = ?",
            (user_id, target_id),
        ).fetchone()
        if target_memory:
            cursor = conn.execute(
                "DELETE FROM person_memories WHERE user_id = ? AND person_id = ?",
                (user_id, source_id),
            )
            counts["person_memories_dropped"] = cursor.rowcount
        else:
            cursor = conn.execute(
                "UPDATE person_memories SET person_id = ? WHERE user_id = ? AND person_id = ?",
                (target_id, user_id, source_id),
            )
            counts["person_memories"] = cursor.rowcount

        # Platform accounts are unique per (user, platform, handle).
        accounts = conn.execute(
            "SELECT id, platform, account_handle FROM person_platform_accounts WHERE user_id = ? AND person_id = ?",
            (user_id, source_id),
        ).fetchall()
        moved_accounts = 0
        dropped_accounts = 0
        for account in accounts:
            clash = conn.execute(
                """
                SELECT 1 FROM person_platform_accounts
                WHERE user_id = ? AND platform = ? AND account_handle = ? AND person_id = ?
                """,
                (user_id, account["platform"], account["account_handle"], target_id),
            ).fetchone()
            if clash:
                conn.execute("DELETE FROM person_platform_accounts WHERE id = ?", (account["id"],))
                dropped_accounts += 1
            else:
                conn.execute(
                    "UPDATE person_platform_accounts SET person_id = ? WHERE id = ?",
                    (target_id, account["id"]),
                )
                moved_accounts += 1
        counts["platform_accounts"] = moved_accounts
        counts["platform_accounts_dropped"] = dropped_accounts

        conn.execute(
            """
            INSERT INTO person_update_events
                (id, user_id, person_id, source, outcome, reason,
                 before_json, after_json, evidence_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                user_id,
                target_id,
                "person_merge",
                "merged",
                f"merged person {source_id} into {target_id}",
                json.dumps({"source_person_id": source_id}, ensure_ascii=False),
                json.dumps({"target_person_id": target_id, "moved": counts}, ensure_ascii=False),
                json.dumps([{"source_person_id": source_id}], ensure_ascii=False),
                _now(),
            ),
        )

        conn.execute(
            "DELETE FROM persons WHERE id = ? AND user_id = ?",
            (source_id, user_id),
        )

        return {
            "target_person_id": target_id,
            "source_person_id": source_id,
            "moved": counts,
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
