-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create custom types if needed
DO $$ BEGIN
    CREATE TYPE chat_type AS ENUM ('private', 'group', 'channel', 'supergroup');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(date DESC);
CREATE INDEX IF NOT EXISTS idx_messages_chat_msg ON messages(chat_id, msg_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_message ON message_embeddings(message_id);

-- Create vector similarity search indexes (IVFFlat)
-- These will be created after data is inserted
-- CREATE INDEX ON message_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX ON message_images USING ivfflat (img_embedding vector_cosine_ops) WITH (lists = 100);