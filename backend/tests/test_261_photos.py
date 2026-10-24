"""Build 261: the user's own photos live in a library the planner may hand out."""

import sqlite3

import pytest

from app.schemas.strategic_plan import PlanOption, StrategicPlan
from app.services import user_photos
from app.services.strategic_plan import _normalise


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE user_photos (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, caption TEXT NOT NULL DEFAULT '',
            mime TEXT NOT NULL DEFAULT 'image/jpeg', filename TEXT NOT NULL DEFAULT 'p.jpg',
            content BLOB NOT NULL, created_at TEXT NOT NULL
        );
        """
    )
    return conn


def test_a_photo_round_trips_and_is_scoped_to_its_owner():
    conn = _conn()
    saved = user_photos.add_photo(
        conn, "u1", content=b"\x89PNG", mime="image/png", filename="a.png", caption="健身房"
    )
    assert [row["caption"] for row in user_photos.list_photos(conn, "u1")] == ["健身房"]
    assert user_photos.list_photos(conn, "u2") == []
    row = user_photos.read_photo(conn, "u1", saved["id"])
    assert row["content"] == b"\x89PNG"
    assert user_photos.read_photo(conn, "u2", saved["id"]) is None
    assert user_photos.delete_photo(conn, "u2", saved["id"]) is False
    assert user_photos.delete_photo(conn, "u1", saved["id"]) is True


def test_an_oversized_or_foreign_file_is_refused():
    conn = _conn()
    with pytest.raises(ValueError):
        user_photos.add_photo(conn, "u1", content=b"x" * (user_photos.MAX_BYTES + 1),
                              mime="image/jpeg", filename="big.jpg")
    with pytest.raises(ValueError):
        user_photos.add_photo(conn, "u1", content=b"x", mime="application/pdf",
                              filename="cv.pdf")
    with pytest.raises(ValueError):
        user_photos.add_photo(conn, "u1", content=b"", mime="image/jpeg", filename="empty.jpg")


def test_the_planner_only_keeps_photo_ids_that_exist():
    plan = StrategicPlan(
        read="她要照片",
        options=[
            PlanOption(tactic="发一张", why="她明确要了", line="", photo_id="p1"),
            PlanOption(tactic="编一张", why="乱填", line="", photo_id="ghost"),
        ],
    )
    normalised = _normalise(
        plan,
        {
            "transcript": [{"id": "m1", "who": "她", "text": "发张照片"}],
            "reply_target_message": {"id": "m1"},
            "photos": [{"id": "p1", "caption": "健身房"}],
        },
    )
    first, second = normalised.options
    assert first.photo_id == "p1" and first.send is True
    # An invented id is dropped; with no line left there is nothing to send.
    assert second.photo_id == "" and second.send is False
