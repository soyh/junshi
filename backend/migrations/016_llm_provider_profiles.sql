CREATE TABLE IF NOT EXISTS user_llm_provider_profiles (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    base_url TEXT NOT NULL,
    model TEXT NOT NULL,
    timeout_seconds REAL NOT NULL DEFAULT 60.0,
    api_key_encrypted TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 0 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

CREATE INDEX IF NOT EXISTS idx_llm_provider_profiles_user
ON user_llm_provider_profiles(user_id, updated_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_llm_provider_profiles_one_active
ON user_llm_provider_profiles(user_id)
WHERE is_active = 1;

INSERT OR IGNORE INTO user_llm_provider_profiles (
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
FROM user_llm_provider_configs
WHERE NOT EXISTS (
    SELECT 1
    FROM user_llm_provider_profiles profile
    WHERE profile.user_id = user_llm_provider_configs.user_id
);
