import sqlite3


class LLMProviderConfigRepository:
    def get(self, conn: sqlite3.Connection, user_id: str) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT *
            FROM user_llm_provider_configs
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    def upsert(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        provider: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
        api_key_encrypted: str,
    ) -> None:
        conn.execute(
            """
            INSERT INTO user_llm_provider_configs (
                user_id, provider, base_url, model, timeout_seconds,
                api_key_encrypted
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                provider = excluded.provider,
                base_url = excluded.base_url,
                model = excluded.model,
                timeout_seconds = excluded.timeout_seconds,
                api_key_encrypted = excluded.api_key_encrypted,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                provider,
                base_url,
                model,
                timeout_seconds,
                api_key_encrypted,
            ),
        )

    def delete(self, conn: sqlite3.Connection, user_id: str) -> bool:
        cursor = conn.execute(
            "DELETE FROM user_llm_provider_configs WHERE user_id = ?",
            (user_id,),
        )
        return cursor.rowcount > 0

    def list_profiles(self, conn: sqlite3.Connection, user_id: str) -> list[sqlite3.Row]:
        return conn.execute(
            """
            SELECT *
            FROM user_llm_provider_profiles
            WHERE user_id = ?
            ORDER BY is_active DESC, updated_at DESC, name ASC
            """,
            (user_id,),
        ).fetchall()

    def get_profile(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        profile_id: str,
    ) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT *
            FROM user_llm_provider_profiles
            WHERE user_id = ? AND id = ?
            """,
            (user_id, profile_id),
        ).fetchone()

    def get_active_profile(
        self,
        conn: sqlite3.Connection,
        user_id: str,
    ) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT *
            FROM user_llm_provider_profiles
            WHERE user_id = ? AND is_active = 1
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

    def create_profile(
        self,
        conn: sqlite3.Connection,
        *,
        profile_id: str,
        user_id: str,
        name: str,
        provider: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
        api_key_encrypted: str,
        activate: bool,
    ) -> sqlite3.Row:
        if activate:
            conn.execute(
                "UPDATE user_llm_provider_profiles SET is_active = 0 WHERE user_id = ?",
                (user_id,),
            )
        conn.execute(
            """
            INSERT INTO user_llm_provider_profiles (
                id, user_id, name, provider, base_url, model,
                timeout_seconds, api_key_encrypted, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                user_id,
                name,
                provider,
                base_url,
                model,
                timeout_seconds,
                api_key_encrypted,
                1 if activate else 0,
            ),
        )
        return self.get_profile(conn, user_id, profile_id)  # type: ignore[return-value]

    def update_profile(
        self,
        conn: sqlite3.Connection,
        *,
        user_id: str,
        profile_id: str,
        name: str,
        provider: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
        api_key_encrypted: str,
    ) -> sqlite3.Row | None:
        cursor = conn.execute(
            """
            UPDATE user_llm_provider_profiles
            SET name = ?, provider = ?, base_url = ?, model = ?,
                timeout_seconds = ?, api_key_encrypted = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND id = ?
            """,
            (
                name,
                provider,
                base_url,
                model,
                timeout_seconds,
                api_key_encrypted,
                user_id,
                profile_id,
            ),
        )
        if cursor.rowcount == 0:
            return None
        return self.get_profile(conn, user_id, profile_id)

    def activate_profile(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        profile_id: str,
    ) -> sqlite3.Row | None:
        target = self.get_profile(conn, user_id, profile_id)
        if target is None:
            return None
        conn.execute(
            "UPDATE user_llm_provider_profiles SET is_active = 0 WHERE user_id = ?",
            (user_id,),
        )
        conn.execute(
            """
            UPDATE user_llm_provider_profiles
            SET is_active = 1, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND id = ?
            """,
            (user_id, profile_id),
        )
        return self.get_profile(conn, user_id, profile_id)

    def delete_profile(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        profile_id: str,
    ) -> bool:
        row = self.get_profile(conn, user_id, profile_id)
        if row is None:
            return False
        was_active = bool(row["is_active"])
        conn.execute(
            "DELETE FROM user_llm_provider_profiles WHERE user_id = ? AND id = ?",
            (user_id, profile_id),
        )
        if was_active:
            replacement = conn.execute(
                """
                SELECT id
                FROM user_llm_provider_profiles
                WHERE user_id = ?
                ORDER BY updated_at DESC, name ASC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            if replacement is not None:
                self.activate_profile(conn, user_id, replacement["id"])
        return True
