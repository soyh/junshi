-- WeChat wording: platforms censor "微信"/"VX", so the user can teach the
-- assistant which words mean WeChat (recognition) and which word to use when
-- handing the id over (output), per channel.
--
-- `wechat_aliases`       recognition aliases, comma separated (global).
-- `wechat_display_alias` the word a reply may use instead of 微信 (global).
-- The per-channel override travels in the bridge config and is passed to the
-- context endpoint as `wechat_alias`, so no per-channel table is needed here.
ALTER TABLE user_profiles ADD COLUMN wechat_aliases TEXT NOT NULL DEFAULT '';

ALTER TABLE user_profiles ADD COLUMN wechat_display_alias TEXT NOT NULL DEFAULT '微信';

-- What the user actually wants from this relationship. Free text goals alone
-- never changed the tactics; this enum does (pacing, escalation, promises).
ALTER TABLE relationships ADD COLUMN intent TEXT NOT NULL DEFAULT 'unsure';
