-- Contact exchange: the user's own WeChat id, the counterpart's WeChat id on
-- the person record, and the opt-in that lets a draft hand the id over.
--
-- Cross-channel identity itself already lives in `person_platform_accounts`
-- (migration 021): one row per (user, platform, handle) pointing at a person,
-- so the same human keeps ONE conversation no matter which app she writes from.

ALTER TABLE user_profiles ADD COLUMN wechat_id TEXT NOT NULL DEFAULT '';

ALTER TABLE user_profiles ADD COLUMN contact_handoff_enabled INTEGER NOT NULL DEFAULT 0;

ALTER TABLE persons ADD COLUMN wechat_id TEXT NOT NULL DEFAULT '';
