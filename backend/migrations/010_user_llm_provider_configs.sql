CREATE TABLE IF NOT EXISTS user_llm_provider_configs (
    user_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    base_url TEXT NOT NULL,
    model TEXT NOT NULL,
    timeout_seconds REAL NOT NULL DEFAULT 60.0,
    api_key_encrypted TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
