CREATE TABLE IF NOT EXISTS interactions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    person_id TEXT NOT NULL,
    relationship_id TEXT,
    type TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    content TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (person_id)
        REFERENCES persons(id)
        ON DELETE CASCADE,

    FOREIGN KEY (relationship_id)
        REFERENCES relationships(id)
        ON DELETE SET NULL,

    CHECK (
        type IN (
            'message',
            'call',
            'meeting',
            'date',
            'gift',
            'other'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_interactions_user_id
    ON interactions(user_id);

CREATE INDEX IF NOT EXISTS idx_interactions_person_id
    ON interactions(person_id);

CREATE INDEX IF NOT EXISTS idx_interactions_relationship_id
    ON interactions(relationship_id);

CREATE INDEX IF NOT EXISTS idx_interactions_occurred_at
    ON interactions(occurred_at);

CREATE INDEX IF NOT EXISTS idx_interactions_person_occurred_at
    ON interactions(person_id, occurred_at DESC);
