CREATE TABLE IF NOT EXISTS user_llm_vision_profile_selection (
    user_id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(profile_id)
        REFERENCES user_llm_provider_profiles(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_llm_vision_profile_selection_profile
ON user_llm_vision_profile_selection(profile_id);
