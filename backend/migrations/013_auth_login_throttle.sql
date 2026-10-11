CREATE TABLE IF NOT EXISTS auth_login_throttle (
    subject_hash TEXT PRIMARY KEY,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    window_started_at TEXT NOT NULL,
    locked_until TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (failed_attempts >= 0)
);

CREATE INDEX IF NOT EXISTS idx_auth_login_throttle_locked_until
    ON auth_login_throttle(locked_until);
