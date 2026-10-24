-- Manual takeover: while the user handles one conversation by hand the bridge
-- must stay quiet there and keep serving every other conversation.
--
-- `auto_reply_paused` is a 0/1 flag rather than a timestamp: the takeover has no
-- natural expiry, and a stale timestamp would silently resume replies.
ALTER TABLE conversations ADD COLUMN auto_reply_paused INTEGER NOT NULL DEFAULT 0;

-- When it was switched on, so the UI can say "since 14:05".
ALTER TABLE conversations ADD COLUMN takeover_at TEXT;
