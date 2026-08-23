CREATE TABLE IF NOT EXISTS action_decisions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    person_id TEXT NOT NULL,
    recommendation_id TEXT,
    decision TEXT NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,

    CHECK (decision IN ('confirmed', 'rejected'))
);

CREATE INDEX IF NOT EXISTS idx_action_decisions_user_person_created
    ON action_decisions(user_id, person_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_action_decisions_user_person_recommendation
    ON action_decisions(user_id, person_id, recommendation_id);
