ALTER TABLE model_references ADD COLUMN is_guide INTEGER NOT NULL DEFAULT 0 CHECK (is_guide IN (0, 1));
