CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS persons (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    nickname TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_persons_user_id
    ON persons(user_id);

CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    person_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'unknown',
    stage TEXT NOT NULL DEFAULT 'unknown',
    long_term_goal TEXT,
    current_goal TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (person_id)
        REFERENCES persons(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_relationships_user_id
    ON relationships(user_id);

CREATE INDEX IF NOT EXISTS idx_relationships_person_id
    ON relationships(person_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_relationship_user_person
    ON relationships(user_id, person_id);
