CREATE TABLE IF NOT EXISTS person_platform_accounts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    person_id TEXT NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    account_handle TEXT NOT NULL,
    display_name TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    UNIQUE(user_id, platform, account_handle)
);
CREATE INDEX IF NOT EXISTS idx_platform_person ON person_platform_accounts(user_id, person_id);
CREATE TABLE IF NOT EXISTS conversation_platform_sources (
    conversation_id TEXT PRIMARY KEY REFERENCES conversations(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id TEXT NOT NULL REFERENCES person_platform_accounts(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS pc_ingest_receipts (
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    operation_id TEXT NOT NULL,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    fingerprint TEXT NOT NULL,
    result_json TEXT NOT NULL,
    PRIMARY KEY(user_id, operation_id)
);
