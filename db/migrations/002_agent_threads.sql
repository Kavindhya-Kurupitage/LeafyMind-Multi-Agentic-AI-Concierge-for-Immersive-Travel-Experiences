-- Agent Hub: per-agent conversation threads and messages

DO $body$ BEGIN
    CREATE TYPE agent_thread_status AS ENUM ('active', 'completed', 'archived');
EXCEPTION WHEN duplicate_object THEN NULL;
END $body$;

CREATE TABLE IF NOT EXISTS agent_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    agent_id VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL DEFAULT 'New conversation',
    status agent_thread_status NOT NULL DEFAULT 'active',
    context JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_threads_user_id ON agent_threads (user_id);
CREATE INDEX IF NOT EXISTS idx_agent_threads_agent_id ON agent_threads (agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_threads_user_agent ON agent_threads (user_id, agent_id);

CREATE TABLE IF NOT EXISTS agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID NOT NULL REFERENCES agent_threads (id) ON DELETE CASCADE,
    role VARCHAR(32) NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    agent_id VARCHAR(64),
    tool_events JSONB NOT NULL DEFAULT '[]'::jsonb,
    artifacts JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_messages_thread_id ON agent_messages (thread_id);
CREATE INDEX IF NOT EXISTS idx_agent_messages_created_at ON agent_messages (thread_id, created_at);
