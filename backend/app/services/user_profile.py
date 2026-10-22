import sqlite3

from app.schemas.user_profile import UserProfilePayload, UserProfileResponse

FIELDS = (
    "nickname",
    "gender",
    "birth_year",
    "city",
    "job",
    "hobbies",
    "relationship_status",
    "about",
    "reply_rules",
)

#: Names the draft prompt understands; `relationship_status` is stored as
#: `relationship` so it lines up with the prompt's profile field list.
PROMPT_FIELDS = {
    "nickname": "nickname",
    "gender": "gender",
    "birth_year": "birth_year",
    "city": "city",
    "job": "job",
    "hobbies": "hobbies",
    "relationship_status": "relationship",
    "about": "about",
}


class UserProfileService:
    """The signed-in user's own facts and default reply style.

    Stored per account so the same person gets the same voice on the web page,
    the PC client and the phone, instead of a per-device JSON file.
    """

    def get(self, conn: sqlite3.Connection, user_id: str) -> UserProfileResponse:
        row = conn.execute(
            "SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row is None:
            return UserProfileResponse()
        data = {field: str(row[field] or "") for field in FIELDS}
        return UserProfileResponse(**data, updated_at=str(row["updated_at"] or ""))

    def save(
        self, conn: sqlite3.Connection, user_id: str, payload: UserProfilePayload
    ) -> UserProfileResponse:
        values = {field: getattr(payload, field, "") or "" for field in FIELDS}
        # Trim what the user typed; email clients and phone keyboards love stray spaces.
        values = {field: value.strip() for field, value in values.items()}
        existing = conn.execute(
            "SELECT 1 FROM user_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        if existing:
            assignments = ", ".join(f"{field} = ?" for field in FIELDS)
            conn.execute(
                f"UPDATE user_profiles SET {assignments},"
                " updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                [*(values[field] for field in FIELDS), user_id],
            )
        else:
            columns = ", ".join(("user_id", *FIELDS))
            marks = ", ".join("?" for _ in range(len(FIELDS) + 1))
            conn.execute(
                f"INSERT INTO user_profiles ({columns}) VALUES ({marks})",
                [user_id, *(values[field] for field in FIELDS)],
            )
        conn.commit()
        return self.get(conn, user_id)

    def prompt_facts(self, profile: UserProfileResponse) -> dict[str, str]:
        """Only the facts the user actually filled in, keyed for the prompt."""
        facts = {}
        for field, key in PROMPT_FIELDS.items():
            value = str(getattr(profile, field, "") or "").strip()
            if value:
                facts[key] = value[:200]
        return facts
