-- The signed-in user's explicit permission for the companion client to send
-- drafts on their behalf. Off by default: the product rule stays
-- "a human sends the message" until the user opts in.
ALTER TABLE user_profiles ADD COLUMN auto_send_authorized INTEGER NOT NULL DEFAULT 0;
