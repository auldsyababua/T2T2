-- S3 Integration Tables for T2T2 Bot
-- Run this AFTER setting up the S3 wrapper in Supabase

-- Create foreign table for S3 objects (images)
CREATE FOREIGN TABLE IF NOT EXISTS s3_images (
    name text,
    bucket text,
    owner_id text,
    size bigint,
    last_modified timestamp,
    etag text,
    content_type text,
    content_length bigint,
    content_encoding text,
    content_disposition text,
    cache_control text,
    expires timestamp
)
SERVER s3_wrapper
OPTIONS (
    table_name 'images/',  -- S3 prefix for images
    fetch_size '1000'
);

-- Create a table to track image metadata and embeddings
CREATE TABLE IF NOT EXISTS image_embeddings (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    s3_key text NOT NULL UNIQUE,
    s3_bucket text NOT NULL,
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

-- Function to search images by similarity
CREATE OR REPLACE FUNCTION search_similar_images(
    query_embedding vector(1536),
    match_count int DEFAULT 5,
    user_id text DEFAULT NULL
) RETURNS TABLE (
    id uuid,
    s3_key text,
    s3_bucket text,
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
        ie.s3_bucket,
        ie.extracted_text,
        ie.image_description,
        ie.metadata,
        1 - (ie.embedding <=> query_embedding) as similarity
    FROM image_embeddings ie
    WHERE 
        (user_id IS NULL OR ie.telegram_user_id = user_id)
        AND ie.embedding IS NOT NULL
    ORDER BY ie.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Grant permissions
GRANT ALL ON s3_images TO service_role;
GRANT ALL ON image_embeddings TO service_role;

-- Enable RLS on image_embeddings
ALTER TABLE image_embeddings ENABLE ROW LEVEL SECURITY;

-- Policy: Service role has full access
CREATE POLICY "Service role full access to image_embeddings" ON image_embeddings
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);