CREATE TABLE IF NOT EXISTS action_plan_proposals (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    person_id TEXT NOT NULL,
    recommendation_id TEXT NOT NULL,
    action TEXT NOT NULL,
    evidence_source_ids TEXT NOT NULL,
    priority TEXT,
    time_horizon TEXT,
    status TEXT NOT NULL DEFAULT 'proposed',
    requires_user_confirmation INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,

    CHECK (status = 'proposed'),
    CHECK (requires_user_confirmation = 1)
);

CREATE INDEX IF NOT EXISTS idx_action_plan_proposals_user_person_created
    ON action_plan_proposals(user_id, person_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_action_plan_proposals_user_person_recommendation
    ON action_plan_proposals(user_id, person_id, recommendation_id);

ALTER TABLE action_decisions
    ADD COLUMN action_plan_proposal_id TEXT
    REFERENCES action_plan_proposals(id)
    ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_action_decisions_proposal
    ON action_decisions(action_plan_proposal_id);
