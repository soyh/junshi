-- Bridge plugin heartbeat (external channel status).
-- One row per (user, channel); the bridge upserts every minute.

CREATE TABLE IF NOT EXISTS bridge_heartbeats (
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'online',
    replies_today INTEGER NOT NULL DEFAULT 0,
    detail TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (user_id, channel)
);
