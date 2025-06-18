-- Add pending_authentications table for admin-assisted authentication
-- This table tracks authentication requests that need admin intervention

CREATE TABLE IF NOT EXISTS pending_authentications (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id text NOT NULL,
    phone_number text,
    status text DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
    error text,
    created_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone
);

-- Indexes for efficient lookups
CREATE INDEX idx_pending_auth_status ON pending_authentications(status);
CREATE INDEX idx_pending_auth_user ON pending_authentications(user_id);
CREATE INDEX idx_pending_auth_created ON pending_authentications(created_at DESC);

-- Enable RLS
ALTER TABLE pending_authentications ENABLE ROW LEVEL SECURITY;

-- Grant access to service role
CREATE POLICY "Service role full access" ON pending_authentications
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Grant permissions
GRANT ALL ON pending_authentications TO service_role;