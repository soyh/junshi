CREATE TABLE IF NOT EXISTS action_outcomes (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    person_id TEXT NOT NULL,
    decision_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    FOREIGN KEY (decision_id) REFERENCES action_decisions(id) ON DELETE CASCADE,

    CHECK (outcome IN ('completed', 'skipped', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_action_outcomes_user_person_created
    ON action_outcomes(user_id, person_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_action_outcomes_decision
    ON action_outcomes(decision_id);
