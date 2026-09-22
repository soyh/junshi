CREATE TABLE IF NOT EXISTS media_attachments (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    person_id TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    message_id TEXT,
    media_type TEXT NOT NULL CHECK (media_type IN ('image', 'video')),
    mime_type TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
    sent_at TEXT,
    analysis_status TEXT NOT NULL DEFAULT 'pending' CHECK (analysis_status IN ('pending', 'completed', 'failed')),
    analysis_text TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_media_attachments_conversation
    ON media_attachments(user_id, conversation_id, created_at);

CREATE UNIQUE INDEX IF NOT EXISTS idx_media_attachments_user_sha256
    ON media_attachments(user_id, sha256, conversation_id);
