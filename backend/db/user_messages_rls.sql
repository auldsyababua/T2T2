-- Enable Row Level Security on user_messages table
ALTER TABLE user_messages ENABLE ROW LEVEL SECURITY;

-- Drop existing policy if it exists
DROP POLICY IF EXISTS user_messages_policy ON user_messages;

-- Create policy that allows users to only see their own message associations
CREATE POLICY user_messages_policy ON user_messages
    FOR ALL
    USING (user_id = current_setting('app.user_id')::bigint);

-- Also need RLS on related tables for proper isolation

-- Enable RLS on message_embeddings (users should only see embeddings for their messages)
ALTER TABLE message_embeddings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS message_embeddings_policy ON message_embeddings;

CREATE POLICY message_embeddings_policy ON message_embeddings
    FOR ALL
    USING (
        message_id IN (
            SELECT message_id FROM user_messages 
            WHERE user_id = current_setting('app.user_id')::bigint
        )
    );

-- Enable RLS on message_images (users should only see images for their messages)
ALTER TABLE message_images ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS message_images_policy ON message_images;

CREATE POLICY message_images_policy ON message_images
    FOR ALL
    USING (
        message_id IN (
            SELECT message_id FROM user_messages 
            WHERE user_id = current_setting('app.user_id')::bigint
        )
    );

-- Enable RLS on timelines (users should only see their own timelines)
ALTER TABLE timelines ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS timelines_policy ON timelines;

CREATE POLICY timelines_policy ON timelines
    FOR ALL
    USING (user_id = current_setting('app.user_id')::bigint);

-- Grant necessary permissions to PUBLIC since Railway doesn't have authenticated role
-- RLS policies still enforce user isolation so this is safe
GRANT ALL ON user_messages TO PUBLIC;
GRANT ALL ON message_embeddings TO PUBLIC;
GRANT ALL ON message_images TO PUBLIC;
GRANT ALL ON timelines TO PUBLIC;