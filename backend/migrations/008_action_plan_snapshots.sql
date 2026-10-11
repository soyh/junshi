CREATE TABLE IF NOT EXISTS action_plan_snapshots (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    person_id TEXT NOT NULL,
    recommendation_id TEXT NOT NULL,
    recommendation_json TEXT NOT NULL,
    action_plan_json TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, person_id, recommendation_id)
);

CREATE INDEX IF NOT EXISTS idx_action_plan_snapshots_user_person
    ON action_plan_snapshots(user_id, person_id, created_at DESC);
