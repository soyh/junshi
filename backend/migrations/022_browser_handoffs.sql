CREATE TABLE IF NOT EXISTS browser_handoffs (
    ticket_hash TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE REFERENCES auth_sessions(id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL
);
