CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    person_id TEXT NOT NULL,
    relationship_id TEXT,
    title TEXT,
    status TEXT NOT NULL DEFAULT 'active',
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
        status IN (
            'active',
            'archived'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id
    ON conversations(user_id);

CREATE INDEX IF NOT EXISTS idx_conversations_person_id
    ON conversations(person_id);

CREATE INDEX IF NOT EXISTS idx_conversations_relationship_id
    ON conversations(relationship_id);

CREATE INDEX IF NOT EXISTS idx_conversations_user_person
    ON conversations(user_id, person_id);

CREATE INDEX IF NOT EXISTS idx_conversations_user_updated_at
    ON conversations(user_id, updated_at DESC);


CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    sender_type TEXT NOT NULL,
    content TEXT NOT NULL,
    sent_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (conversation_id)
        REFERENCES conversations(id)
        ON DELETE CASCADE,

    CHECK (
        sender_type IN (
            'user',
            'person',
            'system',
            'assistant'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_messages_user_id
    ON messages(user_id);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
    ON messages(conversation_id);

CREATE INDEX IF NOT EXISTS idx_messages_sent_at
    ON messages(sent_at);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_sent_at
    ON messages(conversation_id, sent_at ASC);

CREATE INDEX IF NOT EXISTS idx_messages_user_conversation_sent_at
    ON messages(user_id, conversation_id, sent_at ASC);
