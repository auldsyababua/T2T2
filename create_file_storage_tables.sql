-- Create tables for T2T2 Bot - Store ALL file types from Telegram
-- Supports images, videos, documents, audio, voice notes, stickers, etc.

-- Main table for ALL files
CREATE TABLE IF NOT EXISTS telegram_files (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- S3 Storage Info
    s3_key text NOT NULL UNIQUE,
    s3_bucket text NOT NULL DEFAULT 't2t2-images',
    s3_url text,
    file_size bigint,
    mime_type text,
    
    -- Telegram Info
    telegram_file_id text,
    telegram_file_unique_id text,
    telegram_chat_id text,
    telegram_chat_name text,
    telegram_message_id text,
    telegram_user_id text,
    telegram_username text,
    
    -- File Type Classification
    file_type text CHECK (file_type IN (
        'photo', 'video', 'audio', 'voice', 'document', 
        'animation', 'sticker', 'video_note', 'unknown'
    )),
    file_extension text,
    original_filename text,
    
    -- Content Extraction (where applicable)
    extracted_text text,  -- From images (OCR), documents (PDF text), etc.
    transcription text,   -- From audio/voice messages
    description text,     -- AI-generated description
    language text,        -- Detected language
    
    -- Embeddings for semantic search
    content_embedding vector(1536),  -- Main embedding for search
    
    -- Metadata
    metadata jsonb DEFAULT '{}'::jsonb,
    message_text text,  -- The text that accompanied the file
    reply_to_message_id text,
    forward_from_chat_id text,
    
    -- Timestamps
    telegram_date timestamp with time zone,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
    updated_at timestamp with time zone DEFAULT timezone('utc'::text, now())
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS telegram_files_embedding_idx 
ON telegram_files USING ivfflat (content_embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS telegram_files_s3_key_idx ON telegram_files(s3_key);
CREATE INDEX IF NOT EXISTS telegram_files_telegram_file_id_idx ON telegram_files(telegram_file_id);
CREATE INDEX IF NOT EXISTS telegram_files_telegram_chat_idx ON telegram_files(telegram_chat_id);
CREATE INDEX IF NOT EXISTS telegram_files_telegram_user_idx ON telegram_files(telegram_user_id);
CREATE INDEX IF NOT EXISTS telegram_files_file_type_idx ON telegram_files(file_type);
CREATE INDEX IF NOT EXISTS telegram_files_created_idx ON telegram_files(created_at DESC);
CREATE INDEX IF NOT EXISTS telegram_files_mime_type_idx ON telegram_files(mime_type);

-- Separate table for image-specific metadata
CREATE TABLE IF NOT EXISTS image_metadata (
    file_id uuid PRIMARY KEY REFERENCES telegram_files(id) ON DELETE CASCADE,
    width integer,
    height integer,
    format text,
    has_transparency boolean,
    dominant_colors jsonb,  -- Array of dominant colors
    ocr_text text,
    detected_objects jsonb, -- Array of detected objects with confidence scores
    is_screenshot boolean,
    contains_faces boolean,
    face_count integer
);

-- Separate table for video-specific metadata
CREATE TABLE IF NOT EXISTS video_metadata (
    file_id uuid PRIMARY KEY REFERENCES telegram_files(id) ON DELETE CASCADE,
    duration_seconds numeric,
    width integer,
    height integer,
    fps numeric,
    codec text,
    has_audio boolean,
    thumbnail_s3_key text,
    transcription text
);

-- Separate table for audio-specific metadata
CREATE TABLE IF NOT EXISTS audio_metadata (
    file_id uuid PRIMARY KEY REFERENCES telegram_files(id) ON DELETE CASCADE,
    duration_seconds numeric,
    bitrate integer,
    sample_rate integer,
    channels integer,
    artist text,
    title text,
    album text,
    transcription text,
    language text
);

-- Separate table for document-specific metadata
CREATE TABLE IF NOT EXISTS document_metadata (
    file_id uuid PRIMARY KEY REFERENCES telegram_files(id) ON DELETE CASCADE,
    page_count integer,
    word_count integer,
    language text,
    document_type text, -- pdf, docx, txt, etc.
    is_encrypted boolean,
    extracted_images_count integer,
    table_of_contents jsonb
);

-- Function to search files by similarity
CREATE OR REPLACE FUNCTION search_similar_files(
    query_embedding vector(1536),
    match_count int DEFAULT 10,
    user_id text DEFAULT NULL,
    chat_id text DEFAULT NULL,
    file_types text[] DEFAULT NULL
) RETURNS TABLE (
    id uuid,
    s3_key text,
    s3_url text,
    file_type text,
    original_filename text,
    extracted_text text,
    description text,
    message_text text,
    metadata jsonb,
    similarity float,
    created_at timestamp with time zone
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        tf.id,
        tf.s3_key,
        tf.s3_url,
        tf.file_type,
        tf.original_filename,
        tf.extracted_text,
        tf.description,
        tf.message_text,
        tf.metadata,
        1 - (tf.content_embedding <=> query_embedding) as similarity,
        tf.created_at
    FROM telegram_files tf
    WHERE 
        (user_id IS NULL OR tf.telegram_user_id = user_id)
        AND (chat_id IS NULL OR tf.telegram_chat_id = chat_id)
        AND (file_types IS NULL OR tf.file_type = ANY(file_types))
        AND tf.content_embedding IS NOT NULL
    ORDER BY tf.content_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to get storage statistics
CREATE OR REPLACE FUNCTION get_storage_stats(
    user_id text DEFAULT NULL,
    chat_id text DEFAULT NULL
) RETURNS TABLE (
    total_files bigint,
    total_size bigint,
    file_type text,
    count bigint,
    size bigint
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH base_stats AS (
        SELECT 
            tf.file_type,
            COUNT(*)::bigint as count,
            COALESCE(SUM(tf.file_size), 0)::bigint as size
        FROM telegram_files tf
        WHERE 
            (user_id IS NULL OR tf.telegram_user_id = user_id)
            AND (chat_id IS NULL OR tf.telegram_chat_id = chat_id)
        GROUP BY tf.file_type
    ),
    totals AS (
        SELECT 
            SUM(count)::bigint as total_files,
            SUM(size)::bigint as total_size
        FROM base_stats
    )
    SELECT 
        t.total_files,
        t.total_size,
        bs.file_type,
        bs.count,
        bs.size
    FROM base_stats bs
    CROSS JOIN totals t
    ORDER BY bs.size DESC;
END;
$$;

-- Enable RLS
ALTER TABLE telegram_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE image_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE audio_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_metadata ENABLE ROW LEVEL SECURITY;

-- Policies: Service role has full access
CREATE POLICY "Service role full access" ON telegram_files
    FOR ALL TO service_role USING (true) WITH CHECK (true);
    
CREATE POLICY "Service role full access" ON image_metadata
    FOR ALL TO service_role USING (true) WITH CHECK (true);
    
CREATE POLICY "Service role full access" ON video_metadata
    FOR ALL TO service_role USING (true) WITH CHECK (true);
    
CREATE POLICY "Service role full access" ON audio_metadata
    FOR ALL TO service_role USING (true) WITH CHECK (true);
    
CREATE POLICY "Service role full access" ON document_metadata
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO service_role;