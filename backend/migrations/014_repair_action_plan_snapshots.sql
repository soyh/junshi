-- Repair historical migration-version collision for action_plan_snapshots.
--
-- Some deployed databases recorded migration version 008 before the current
-- 008_action_plan_snapshots.sql existed. Because the migration runner keys only
-- on the numeric prefix, those databases skip the current 008 file forever.
-- Keep historical migrations immutable and repair the required schema
-- additively under a new version. These statements are idempotent for databases
-- where the original 008 migration was applied correctly.

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
