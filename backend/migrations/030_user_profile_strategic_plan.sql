-- The planner stage in front of the reply draft: read the situation (and the
-- uploaded references in full) before wording anything. On by default, because
-- it only adds a read step; set it off to fall back to the classic chain.
ALTER TABLE user_profiles ADD COLUMN strategic_plan_enabled INTEGER NOT NULL DEFAULT 1;
