CREATE TABLE IF NOT EXISTS model_references (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    reference_type TEXT NOT NULL CHECK (reference_type IN ('document', 'skill')),
    original_filename TEXT,
    mime_type TEXT,
    description TEXT,
    content TEXT NOT NULL,
    enabled_by_default INTEGER NOT NULL DEFAULT 1 CHECK (enabled_by_default IN (0, 1)),
    priority INTEGER NOT NULL DEFAULT 100,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_model_references_user_priority
    ON model_references(user_id, enabled_by_default, priority, created_at, id);

CREATE TABLE IF NOT EXISTS conversation_model_reference_overrides (
    user_id TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    reference_id TEXT NOT NULL,
    enabled INTEGER NOT NULL CHECK (enabled IN (0, 1)),
    priority INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (conversation_id, reference_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (reference_id) REFERENCES model_references(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_conversation_model_reference_overrides_user
    ON conversation_model_reference_overrides(user_id, conversation_id, enabled, priority, reference_id);
