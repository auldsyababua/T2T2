-- Add user_sessions table for T2T2 Chat Indexer
-- This table stores Telethon session strings for users who authenticate

CREATE TABLE IF NOT EXISTS user_sessions (
    user_id text PRIMARY KEY,
    session_string text NOT NULL,
    monitored_chats text[] DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

-- Index for efficient lookups
CREATE INDEX idx_user_sessions_updated ON user_sessions(updated_at);

-- Enable RLS
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- Grant access to service role
CREATE POLICY "Service role full access" ON user_sessions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Grant permissions
GRANT ALL ON user_sessions TO service_role;

-- Add update trigger
CREATE TRIGGER update_user_sessions_updated_at
    BEFORE UPDATE ON user_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();