BEGIN;

ALTER TABLE todo
    ADD COLUMN IF NOT EXISTS due_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS remind_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS priority SMALLINT DEFAULT 2,
    ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending';

UPDATE todo SET priority = COALESCE(priority, 2);
UPDATE todo SET status = COALESCE(NULLIF(status, ''), 'pending');

CREATE TABLE IF NOT EXISTS todo_preferences (
    user_id BIGINT PRIMARY KEY,
    quiet_start_minutes SMALLINT,
    quiet_end_minutes SMALLINT,
    notify_channel_id BIGINT
);

COMMIT;
