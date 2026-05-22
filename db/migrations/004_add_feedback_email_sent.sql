-- Track post-stay feedback request emails sent via Gmail SMTP

ALTER TABLE sessions ADD COLUMN IF NOT EXISTS feedback_email_sent BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS feedback_email_sent_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_sessions_feedback_email_pending
    ON sessions (status, feedback_email_sent)
    WHERE feedback_email_sent = FALSE;
