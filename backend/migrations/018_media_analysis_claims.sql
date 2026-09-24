ALTER TABLE media_attachments
    ADD COLUMN analysis_claim_token TEXT;

ALTER TABLE media_attachments
    ADD COLUMN analysis_claimed_at TEXT;

CREATE INDEX IF NOT EXISTS idx_media_attachments_analysis_claim
    ON media_attachments(user_id, analysis_claim_token, analysis_claimed_at);
