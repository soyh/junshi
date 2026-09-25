CREATE TABLE IF NOT EXISTS model_reference_assets (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    asset_type TEXT NOT NULL CHECK (asset_type IN ('document', 'skill')),
    title TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
    content_sha256 TEXT NOT NULL,
    extracted_text TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_model_reference_assets_user_enabled
    ON model_reference_assets(user_id, enabled, asset_type, created_at);
