from app.core.database import get_connection


EXPECTED_FOREIGN_KEYS = {
    "persons": {
        ("user_id", "users", "id", "CASCADE"),
    },
    "relationships": {
        ("user_id", "users", "id", "CASCADE"),
        ("person_id", "persons", "id", "CASCADE"),
    },
    "conversations": {
        ("user_id", "users", "id", "CASCADE"),
        ("person_id", "persons", "id", "CASCADE"),
        ("relationship_id", "relationships", "id", "SET NULL"),
    },
    "messages": {
        ("user_id", "users", "id", "CASCADE"),
        ("conversation_id", "conversations", "id", "CASCADE"),
    },
}


def test_sqlite_foreign_keys_are_enabled(client):
    with get_connection() as conn:
        value = conn.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

    assert value == 1


def test_required_foreign_keys_have_expected_actions(client):
    with get_connection() as conn:
        for table_name, expected in EXPECTED_FOREIGN_KEYS.items():
            rows = conn.execute(
                f'PRAGMA foreign_key_list("{table_name}")'
            ).fetchall()

            actual = {
                (
                    row["from"],
                    row["table"],
                    row["to"],
                    row["on_delete"],
                )
                for row in rows
            }

            assert actual == expected, (
                f"{table_name} foreign keys mismatch: "
                f"expected={expected}, actual={actual}"
            )
