CREATE TABLE IF NOT EXISTS memory_updates (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    person_id TEXT NOT NULL,
    source_candidate_id TEXT NOT NULL UNIQUE,
    source_decision_id TEXT NOT NULL,
    source_outcome_id TEXT NOT NULL,
    category TEXT NOT NULL,
    memory_json TEXT NOT NULL,
    created_at TEXT NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    FOREIGN KEY (source_decision_id) REFERENCES action_decisions(id) ON DELETE CASCADE,
    FOREIGN KEY (source_outcome_id) REFERENCES action_outcomes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_memory_updates_user_person_created
    ON memory_updates(user_id, person_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_updates_source_outcome
    ON memory_updates(source_outcome_id);
