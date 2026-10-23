CREATE TABLE IF NOT EXISTS strategic_reply_plans (
    conversation_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    target_message_id TEXT,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_strategic_reply_plans_user
    ON strategic_reply_plans(user_id, created_at);
