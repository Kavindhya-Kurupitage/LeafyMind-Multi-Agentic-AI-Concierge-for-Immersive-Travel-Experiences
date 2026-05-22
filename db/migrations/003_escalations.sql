-- Escalations table for orchestrator human handoff

CREATE TABLE IF NOT EXISTS escalations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions (id) ON DELETE CASCADE,
    reason VARCHAR(64) NOT NULL,
    user_message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_escalations_session_id ON escalations (session_id);
CREATE INDEX IF NOT EXISTS idx_escalations_created_at ON escalations (created_at DESC);
