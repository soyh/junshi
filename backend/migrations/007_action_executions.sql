CREATE TABLE IF NOT EXISTS action_executions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    person_id TEXT NOT NULL,
    decision_id TEXT NOT NULL,
    executed_at TEXT NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    FOREIGN KEY (decision_id) REFERENCES action_decisions(id) ON DELETE CASCADE,

    UNIQUE (decision_id)
);

CREATE INDEX IF NOT EXISTS idx_action_executions_user_person_created
    ON action_executions(user_id, person_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_action_executions_decision
    ON action_executions(decision_id);
