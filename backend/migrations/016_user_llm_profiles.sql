CREATE TABLE IF NOT EXISTS user_llm_profiles (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    base_url TEXT NOT NULL,
    model TEXT NOT NULL,
    timeout_seconds REAL NOT NULL DEFAULT 60.0,
    api_key_encrypted TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    UNIQUE (user_id, name),
    CHECK (is_active IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_user_llm_profiles_user
    ON user_llm_profiles(user_id);

CREATE INDEX IF NOT EXISTS idx_user_llm_profiles_user_active
    ON user_llm_profiles(user_id, is_active);

-- Preserve every TEST-175/176 single-provider configuration as the initial
-- active profile. Historical migration 010 remains untouched.
INSERT OR IGNORE INTO user_llm_profiles (
    id,
    user_id,
    name,
    provider,
    base_url,
    model,
    timeout_seconds,
    api_key_encrypted,
    is_active,
    created_at,
    updated_at
)
SELECT
    'legacy:' || user_id,
    user_id,
    'Default',
    provider,
    base_url,
    model,
    timeout_seconds,
    api_key_encrypted,
    1,
    created_at,
    updated_at
FROM user_llm_provider_configs;
