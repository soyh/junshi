-- 本人照片库：对方要照片时，桥接可以挑一张直接发，而不是现编。
CREATE TABLE IF NOT EXISTS user_photos (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    caption TEXT NOT NULL DEFAULT '',
    mime TEXT NOT NULL DEFAULT 'image/jpeg',
    filename TEXT NOT NULL DEFAULT 'photo.jpg',
    content BLOB NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_photos_user ON user_photos(user_id, created_at);
