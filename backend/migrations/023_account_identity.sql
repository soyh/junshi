CREATE TABLE IF NOT EXISTS account_identities (
    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    email TEXT UNIQUE,
    email_verified_at TEXT,
    disabled INTEGER NOT NULL DEFAULT 0 CHECK(disabled IN (0,1)),
    administrator INTEGER NOT NULL DEFAULT 0 CHECK(administrator IN (0,1))
);

CREATE TABLE IF NOT EXISTS email_challenges (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    purpose TEXT NOT NULL CHECK(purpose IN ('register','bind','reset','delete')),
    requester_hash TEXT NOT NULL,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    code_hash TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    consumed INTEGER NOT NULL DEFAULT 0 CHECK(consumed IN (0,1))
);
CREATE INDEX IF NOT EXISTS idx_email_challenge_rate ON email_challenges(email,created_at);

-- Preserve management audit after deletion without retaining chat or credentials.
CREATE TABLE IF NOT EXISTS account_management_audit (
    id TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
