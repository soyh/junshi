import sqlite3
import uuid


class LLMProviderConfigRepository:
    # Legacy TEST-175/176 single-config storage. Keep these methods intact as
    # the compatibility facade used by existing API/tests and older databases.
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

    # TEST-178 multi-profile storage.
    def get_active_profile(
        self,
        conn: sqlite3.Connection,
        user_id: str,
    ) -> sqlite3.Row | None:
        return conn.execute(
            """
            SELECT *
            FROM user_llm_profiles
            WHERE user_id = ? AND is_active = 1
            ORDER BY updated_at DESC, created_at DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

    def list_profiles(
        self,
        conn: sqlite3.Connection,
        user_id: str,
    ) -> list[sqlite3.Row]:
        return conn.execute(
            """
            SELECT *
            FROM user_llm_profiles
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
            FROM user_llm_profiles
            WHERE id = ? AND user_id = ?
            """,
            (profile_id, user_id),
        ).fetchone()

    def create_profile(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        name: str,
        provider: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
        api_key_encrypted: str,
        activate: bool,
    ) -> sqlite3.Row:
        profile_id = str(uuid.uuid4())
        if activate:
            conn.execute(
                "UPDATE user_llm_profiles SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,),
            )
        conn.execute(
            """
            INSERT INTO user_llm_profiles (
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
        user_id: str,
        profile_id: str,
        values: dict[str, object],
    ) -> sqlite3.Row | None:
        if not values:
            return self.get_profile(conn, user_id, profile_id)
        allowed = {
            "name",
            "provider",
            "base_url",
            "model",
            "timeout_seconds",
            "api_key_encrypted",
        }
        updates = [(key, value) for key, value in values.items() if key in allowed]
        if not updates:
            return self.get_profile(conn, user_id, profile_id)
        assignments = ", ".join(f"{key} = ?" for key, _ in updates)
        params = [value for _, value in updates]
        params.extend([profile_id, user_id])
        cursor = conn.execute(
            f"""
            UPDATE user_llm_profiles
            SET {assignments}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            params,
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
        row = self.get_profile(conn, user_id, profile_id)
        if row is None:
            return None
        conn.execute(
            "UPDATE user_llm_profiles SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,),
        )
        conn.execute(
            """
            UPDATE user_llm_profiles
            SET is_active = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (profile_id, user_id),
        )
        return self.get_profile(conn, user_id, profile_id)

    def delete_profile(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        profile_id: str,
    ) -> bool:
        cursor = conn.execute(
            "DELETE FROM user_llm_profiles WHERE id = ? AND user_id = ?",
            (profile_id, user_id),
        )
        return cursor.rowcount > 0

    def delete_all_profiles(self, conn: sqlite3.Connection, user_id: str) -> None:
        conn.execute("DELETE FROM user_llm_profiles WHERE user_id = ?", (user_id,))

    def upsert_legacy_profile(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        provider: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
        api_key_encrypted: str,
    ) -> None:
        profile_id = f"legacy:{user_id}"
        conn.execute(
            "UPDATE user_llm_profiles SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,),
        )
        conn.execute(
            """
            INSERT INTO user_llm_profiles (
                id, user_id, name, provider, base_url, model,
                timeout_seconds, api_key_encrypted, is_active
            ) VALUES (?, ?, 'Default', ?, ?, ?, ?, ?, 1)
            ON CONFLICT(id) DO UPDATE SET
                provider = excluded.provider,
                base_url = excluded.base_url,
                model = excluded.model,
                timeout_seconds = excluded.timeout_seconds,
                api_key_encrypted = excluded.api_key_encrypted,
                is_active = 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                profile_id,
                user_id,
                provider,
                base_url,
                model,
                timeout_seconds,
                api_key_encrypted,
            ),
        )
