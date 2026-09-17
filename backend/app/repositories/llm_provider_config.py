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
