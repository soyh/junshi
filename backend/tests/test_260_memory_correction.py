"""Build 260: the person can correct the archive, and the correction wins."""

import json
import sqlite3

from app.services.compact_profile import entries, merge, project
from app.services.person_memory import apply_correction
from app.services.strategic_plan import load_memory


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE persons (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, name TEXT);
        CREATE TABLE conversations (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, person_id TEXT, title TEXT
        );
        CREATE TABLE messages (
            id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, user_id TEXT NOT NULL,
            sender TEXT, content TEXT, sender_type TEXT, sent_at TEXT, created_at TEXT
        );
        CREATE TABLE relationships (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, person_id TEXT, status TEXT,
            stage TEXT, notes TEXT, created_at TEXT, updated_at TEXT
        );
        CREATE TABLE person_memories (
            person_id TEXT NOT NULL, user_id TEXT NOT NULL, revision INTEGER,
            summary_json TEXT, coverage_json TEXT, updated_at TEXT,
            PRIMARY KEY (person_id, user_id)
        );
        CREATE TABLE person_update_events (
            id TEXT PRIMARY KEY, user_id TEXT, person_id TEXT, source TEXT,
            outcome TEXT, reason TEXT, before_json TEXT, after_json TEXT,
            evidence_json TEXT, created_at TEXT
        );
        INSERT INTO persons VALUES ('p1', 'u1', '桃雾漫');
        """
    )
    return conn


def _seed(conn, texts=("见面地点是喜茶。",)):
    summary = {
        "description": "她在深圳。",
        "inferences": list(texts),
        "_profile": [
            {"id": "ai-1", "kind": "inferences", "text": texts[0], "evidence": ["m1"], "active": True}
        ],
        "_profile_version": 1,
        "_consolidated": True,
    }
    conn.execute(
        "INSERT INTO person_memories VALUES ('p1','u1',1,?,?,?)",
        (json.dumps(summary, ensure_ascii=False), "{}", "2026-10-24T00:00:00Z"),
    )
    conn.commit()


def test_a_correction_is_listed_first_and_the_wrong_entry_can_be_deleted():
    conn = _conn()
    _seed(conn)

    apply_correction(conn, "u1", "p1", action="add", kind="facts", text="见面地点是破店烧烤。")
    conn.commit()
    rows = entries(json.loads(conn.execute("SELECT summary_json FROM person_memories").fetchone()[0]))
    assert rows[0]["text"] == "见面地点是破店烧烤。"
    assert rows[0]["source"] == "user"

    apply_correction(conn, "u1", "p1", action="delete", entry_id="ai-1")
    conn.commit()
    summary = json.loads(conn.execute("SELECT summary_json FROM person_memories").fetchone()[0])
    assert [row for row in summary["_profile"] if row["id"] == "ai-1"][0]["active"] is False


def test_the_planner_reads_the_correction_and_marks_it_as_ours():
    conn = _conn()
    _seed(conn)
    apply_correction(conn, "u1", "p1", action="add", kind="facts", text="见面地点是破店烧烤。")

    memory = load_memory(conn, "u1", "p1")
    assert memory["entries"][0] == {"kind": "facts", "text": "见面地点是破店烧烤。", "source": "user"}
    assert "本人亲自改正" in memory["rule"]


def test_a_model_revision_cannot_overwrite_a_correction():
    conn = _conn()
    _seed(conn)
    apply_correction(conn, "u1", "p1", action="add", kind="facts", text="见面地点是破店烧烤。")

    class Proposal:
        description = "更新"
        facts = []
        inferences = []
        constraints = []
        unknowns = []
        preferences = []
        events = []
        superseded_entry_ids = [row["id"] for row in entries(
            json.loads(conn.execute("SELECT summary_json FROM person_memories").fetchone()[0]))
            if row.get("source") == "user"]
        reason = "模型想改写"

        def model_dump(self, include=None):
            return {"description": self.description, "facts": [], "inferences": [],
                    "constraints": [], "unknowns": [], "preferences": [], "events": []}

    summary = json.loads(conn.execute("SELECT summary_json FROM person_memories").fetchone()[0])
    merged, _changes = merge(summary, Proposal(), ["m1"], True)
    survivor = [row for row in merged["_profile"]
                if row["text"] == "见面地点是破店烧烤。" and row.get("source") == "user"]
    assert survivor, "the correction must survive a summarisation pass"


def test_the_compact_budget_keeps_corrections_before_inferences():
    summary = {
        "inferences": ["推断一", "推断二"],
        "_corrections": [{"id": "user-1", "kind": "facts", "text": "见面地点是破店烧烤。"}],
    }
    summary["inferences"] = ["推断" + "很长的一句背景描述" * 12 for _ in range(6)]
    projected = project(summary, [{"content": "在哪里见"}], 4000)
    assert projected["summary"]["facts"] == ["见面地点是破店烧烤。"]
    assert projected["omitted_count"] >= 1
