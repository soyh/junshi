-- One primary conversation per person; platform provenance per message.

ALTER TABLE conversations ADD COLUMN is_primary INTEGER NOT NULL DEFAULT 0;

UPDATE conversations
SET is_primary = 1
WHERE id = (
    SELECT c2.id
    FROM conversations c2
    WHERE c2.user_id = conversations.user_id
      AND c2.person_id = conversations.person_id
    ORDER BY c2.created_at, c2.id
    LIMIT 1
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_conversations_primary
    ON conversations(user_id, person_id)
    WHERE is_primary = 1;

CREATE TABLE IF NOT EXISTS message_platform_sources (
    message_id TEXT PRIMARY KEY REFERENCES messages(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    account_id TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_message_platform_sources_user
    ON message_platform_sources(user_id, platform);
