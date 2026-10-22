CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT PRIMARY KEY,
    nickname TEXT NOT NULL DEFAULT '',
    gender TEXT NOT NULL DEFAULT '',
    birth_year TEXT NOT NULL DEFAULT '',
    city TEXT NOT NULL DEFAULT '',
    job TEXT NOT NULL DEFAULT '',
    hobbies TEXT NOT NULL DEFAULT '',
    relationship_status TEXT NOT NULL DEFAULT '',
    about TEXT NOT NULL DEFAULT '',
    reply_rules TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);
