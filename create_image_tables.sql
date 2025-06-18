-- Create tables for T2T2 Bot image storage and embeddings
-- This doesn't require S3 foreign tables - we'll access S3 directly from Python

-- Table to track image metadata and embeddings
CREATE TABLE IF NOT EXISTS image_embeddings (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    s3_key text NOT NULL UNIQUE,
    s3_bucket text NOT NULL DEFAULT 't2t2-images',
    s3_url text,
    telegram_file_id text,
    telegram_chat_id text,
    telegram_message_id text,
    telegram_user_id text,
    file_size bigint,
    mime_type text,
    extracted_text text,
    image_description text,
    embedding vector(1536),
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
    updated_at timestamp with time zone DEFAULT timezone('utc'::text, now())
);

-- Create indexes for image embeddings
CREATE INDEX IF NOT EXISTS image_embeddings_embedding_idx 
ON image_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS image_embeddings_s3_key_idx ON image_embeddings(s3_key);
CREATE INDEX IF NOT EXISTS image_embeddings_telegram_chat_idx ON image_embeddings(telegram_chat_id);
CREATE INDEX IF NOT EXISTS image_embeddings_telegram_user_idx ON image_embeddings(telegram_user_id);
CREATE INDEX IF NOT EXISTS image_embeddings_created_idx ON image_embeddings(created_at DESC);

-- Function to search images by similarity
CREATE OR REPLACE FUNCTION search_similar_images(
    query_embedding vector(1536),
    match_count int DEFAULT 5,
    user_id text DEFAULT NULL,
    chat_id text DEFAULT NULL
) RETURNS TABLE (
    id uuid,
    s3_key text,
    s3_url text,
    telegram_file_id text,
    extracted_text text,
    image_description text,
    metadata jsonb,
    similarity float
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ie.id,
        ie.s3_key,
        ie.s3_url,
        ie.telegram_file_id,
        ie.extracted_text,
        ie.image_description,
        ie.metadata,
        1 - (ie.embedding <=> query_embedding) as similarity
    FROM image_embeddings ie
    WHERE 
        (user_id IS NULL OR ie.telegram_user_id = user_id)
        AND (chat_id IS NULL OR ie.telegram_chat_id = chat_id)
        AND ie.embedding IS NOT NULL
    ORDER BY ie.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to get user's image stats
CREATE OR REPLACE FUNCTION get_user_image_stats(user_id text)
RETURNS TABLE (
    total_images bigint,
    total_size bigint,
    earliest_image timestamp with time zone,
    latest_image timestamp with time zone
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::bigint as total_images,
        COALESCE(SUM(file_size), 0)::bigint as total_size,
        MIN(created_at) as earliest_image,
        MAX(created_at) as latest_image
    FROM image_embeddings
    WHERE telegram_user_id = user_id;
END;
$$;

-- Enable RLS on image_embeddings
ALTER TABLE image_embeddings ENABLE ROW LEVEL SECURITY;

-- Policy: Service role has full access
CREATE POLICY "Service role full access to image_embeddings" ON image_embeddings
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Grant permissions
GRANT ALL ON image_embeddings TO service_role;
GRANT EXECUTE ON FUNCTION search_similar_images TO service_role;
GRANT EXECUTE ON FUNCTION get_user_image_stats TO service_role;