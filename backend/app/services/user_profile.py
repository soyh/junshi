import sqlite3

from app.schemas.user_profile import UserProfilePayload, UserProfileResponse

FIELDS = (
    "nickname",
    "gender",
    "birth_year",
    "city",
    "hometown",
    "current_location",
    "work_address",
    "job",
    "hobbies",
    "relationship_status",
    "about",
    "reply_rules",
    "wechat_id",
    "wechat_aliases",
)

#: Names the draft prompt understands; `relationship_status` is stored as
#: `relationship` so it lines up with the prompt's profile field list.
PROMPT_FIELDS = {
    "nickname": "nickname",
    "gender": "gender",
    "birth_year": "birth_year",
    "city": "city",
    "hometown": "hometown (ancestral home / where they grew up)",
    "current_location": "current_location (where they are right now)",
    "work_address": "work_address (where they work)",
    "job": "job",
    "hobbies": "hobbies",
    "relationship_status": "relationship",
    "about": "about",
}


def _columns(conn: sqlite3.Connection) -> set[str]:
    """Which profile columns this database actually has.

    Databases created before a migration shipped are missing the newer columns;
    writing only what exists keeps the form usable instead of raising.
    """
    try:
        rows = conn.execute("PRAGMA table_info(user_profiles)").fetchall()
    except sqlite3.OperationalError:
        return set(FIELDS)
    names = set()
    for row in rows:
        try:
            names.add(str(row["name"]))
        except (IndexError, KeyError, TypeError):
            names.add(str(row[1]))
    return names


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
            # No row yet still means "planner on": it is the recommended default.
            return UserProfileResponse(strategic_plan_enabled=True)
        names = set(row.keys())

        def text(field: str, default: str = "") -> str:
            return str(row[field] or default) if field in names else default

        data = {field: text(field) for field in FIELDS}
        data["wechat_display_alias"] = text("wechat_display_alias", "微信") or "微信"
        data["auto_send_authorized"] = bool(text("auto_send_authorized")) if "auto_send_authorized" in names else False
        data["contact_handoff_enabled"] = bool(text("contact_handoff_enabled")) if "contact_handoff_enabled" in names else False
        # No column means "never turned it off", and the planner ships on.
        data["strategic_plan_enabled"] = (
            bool(text("strategic_plan_enabled")) if "strategic_plan_enabled" in names else True
        )
        return UserProfileResponse(**data, updated_at=text("updated_at"))

    def save(
        self, conn: sqlite3.Connection, user_id: str, payload: UserProfilePayload
    ) -> UserProfileResponse:
        values = {field: getattr(payload, field, "") or "" for field in FIELDS}
        # Trim what the user typed; email clients and phone keyboards love stray spaces.
        values = {field: value.strip() for field, value in values.items()}
        display_alias = (payload.wechat_display_alias or "").strip() or "微信"
        authorized = int(bool(payload.auto_send_authorized))
        current = conn.execute(
            "SELECT strategic_plan_enabled, contact_handoff_enabled"
            " FROM user_profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        def carried(flag, stored_column, default):
            """None means the caller did not touch the switch (the PC form)."""
            if flag is None:
                return int(current[stored_column]) if current else default
            return int(bool(flag))

        plan_enabled = carried(payload.strategic_plan_enabled, "strategic_plan_enabled", 1)
        handoff = carried(payload.contact_handoff_enabled, "contact_handoff_enabled", 0)
        columns = _columns(conn)
        pairs = [(field, values[field]) for field in FIELDS if field in columns]
        extra = [
            ("auto_send_authorized", authorized),
            ("wechat_display_alias", display_alias),
            ("strategic_plan_enabled", plan_enabled),
            ("contact_handoff_enabled", handoff),
        ]
        pairs.extend((name, value) for name, value in extra if name in columns)
        existing = conn.execute(
            "SELECT 1 FROM user_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        if existing:
            assignments = ", ".join(f"{name} = ?" for name, _ in pairs)
            conn.execute(
                f"UPDATE user_profiles SET {assignments}, updated_at = CURRENT_TIMESTAMP"
                " WHERE user_id = ?",
                [*(value for _, value in pairs), user_id],
            )
        else:
            names = ", ".join(("user_id", *(name for name, _ in pairs)))
            marks = ", ".join("?" for _ in range(len(pairs) + 1))
            conn.execute(
                f"INSERT INTO user_profiles ({names}) VALUES ({marks})",
                [user_id, *(value for _, value in pairs)],
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
