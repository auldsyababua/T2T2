-- Optimal T2T2 Bot Schema with Redis Integration Support
-- Designed for all Telegram file types with efficient caching

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_cron; -- For scheduled tasks

-- Main files table for ALL content from Telegram
CREATE TABLE IF NOT EXISTS telegram_files (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- S3 Storage
    s3_key text NOT NULL UNIQUE,
    s3_bucket text NOT NULL DEFAULT 't2t2-images',
    s3_region text DEFAULT 'us-east-1',
    file_size bigint,
    mime_type text,
    
    -- Telegram Identifiers
    telegram_file_id text UNIQUE,
    telegram_file_unique_id text,
    telegram_chat_id text NOT NULL,
    telegram_chat_name text,
    telegram_message_id text NOT NULL,
    telegram_user_id text NOT NULL,
    telegram_username text,
    
    -- File Classification
    file_type text CHECK (file_type IN (
        'photo', 'video', 'audio', 'voice', 'document', 
        'animation', 'sticker', 'video_note', 'poll',
        'location', 'contact', 'unknown'
    )) NOT NULL,
    file_extension text,
    original_filename text,
    
    -- Processing Status
    processing_status text DEFAULT 'pending' CHECK (processing_status IN (
        'pending', 'processing', 'completed', 'failed', 'skipped'
    )),
    processing_started_at timestamp with time zone,
    processing_completed_at timestamp with time zone,
    processing_error text,
    retry_count integer DEFAULT 0,
    
    -- Content & Embeddings
    extracted_text text,
    extracted_text_language text,
    content_summary text,
    content_embedding vector(1536),
    embedding_model text DEFAULT 'text-embedding-ada-002',
    
    -- Message Context
    message_text text,
    message_entities jsonb, -- Mentions, hashtags, etc
    reply_to_message_id text,
    forward_from_chat_id text,
    forward_from_user_id text,
    
    -- Metadata
    metadata jsonb DEFAULT '{}'::jsonb,
    tags text[] DEFAULT '{}',
    is_deleted boolean DEFAULT false,
    
    -- Cache Control (for Redis)
    cache_key text GENERATED ALWAYS AS (
        'tf:' || id::text
    ) STORED,
    last_accessed_at timestamp with time zone DEFAULT now(),
    access_count integer DEFAULT 0,
    
    -- Timestamps
    telegram_date timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

-- Image-specific metadata
CREATE TABLE IF NOT EXISTS image_metadata (
    file_id uuid PRIMARY KEY REFERENCES telegram_files(id) ON DELETE CASCADE,
    width integer,
    height integer,
    format text,
    color_mode text, -- RGB, CMYK, etc
    has_transparency boolean,
    
    -- AI Analysis
    ocr_text text,
    ocr_confidence float,
    detected_objects jsonb, -- [{label, confidence, bbox}]
    detected_faces integer DEFAULT 0,
    detected_text_regions jsonb,
    scene_description text,
    
    -- Visual Features
    dominant_colors jsonb, -- [{color, percentage}]
    brightness float,
    contrast float,
    sharpness float,
    
    -- Flags
    is_screenshot boolean,
    is_meme boolean,
    contains_qr_code boolean,
    nsfw_score float
);

-- Video-specific metadata
CREATE TABLE IF NOT EXISTS video_metadata (
    file_id uuid PRIMARY KEY REFERENCES telegram_files(id) ON DELETE CASCADE,
    duration_seconds numeric,
    width integer,
    height integer,
    fps numeric,
    bitrate integer,
    codec text,
    
    -- Audio Track
    has_audio boolean,
    audio_codec text,
    audio_bitrate integer,
    
    -- AI Analysis
    transcription text,
    transcription_language text,
    key_frames_extracted integer,
    scene_changes integer,
    motion_intensity float,
    
    -- Thumbnails
    thumbnail_s3_key text,
    preview_gif_s3_key text
);

-- Audio-specific metadata
CREATE TABLE IF NOT EXISTS audio_metadata (
    file_id uuid PRIMARY KEY REFERENCES telegram_files(id) ON DELETE CASCADE,
    duration_seconds numeric,
    bitrate integer,
    sample_rate integer,
    channels integer,
    codec text,
    
    -- Transcription
    transcription text,
    transcription_confidence float,
    detected_language text,
    detected_speakers integer,
    
    -- Music Metadata
    artist text,
    title text,
    album text,
    genre text,
    year integer,
    
    -- Audio Features
    average_loudness float,
    peak_loudness float,
    dynamic_range float,
    tempo_bpm float
);

-- Document-specific metadata
CREATE TABLE IF NOT EXISTS document_metadata (
    file_id uuid PRIMARY KEY REFERENCES telegram_files(id) ON DELETE CASCADE,
    document_type text, -- pdf, docx, xlsx, txt, etc
    page_count integer,
    word_count integer,
    char_count integer,
    
    -- Content Structure
    detected_language text,
    table_count integer,
    image_count integer,
    link_count integer,
    
    -- Document Features
    has_toc boolean,
    has_forms boolean,
    is_encrypted boolean,
    is_signed boolean,
    
    -- Extracted Structure
    table_of_contents jsonb,
    extracted_tables jsonb,
    extracted_links jsonb
);

-- Processing queue (backs to Redis but persisted here)
CREATE TABLE IF NOT EXISTS processing_queue (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    file_id uuid REFERENCES telegram_files(id) ON DELETE CASCADE,
    queue_name text DEFAULT 'default',
    priority integer DEFAULT 5,
    status text DEFAULT 'pending',
    attempts integer DEFAULT 0,
    max_attempts integer DEFAULT 3,
    scheduled_at timestamp with time zone DEFAULT now(),
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    error_message text,
    worker_id text,
    metadata jsonb DEFAULT '{}'::jsonb
);

-- Cache tracking (for Redis sync)
CREATE TABLE IF NOT EXISTS cache_entries (
    cache_key text PRIMARY KEY,
    cache_type text CHECK (cache_type IN ('embedding', 'metadata', 'search_result')),
    file_id uuid REFERENCES telegram_files(id) ON DELETE CASCADE,
    expires_at timestamp with time zone,
    hit_count integer DEFAULT 0,
    last_hit_at timestamp with time zone,
    size_bytes integer
);

-- User statistics (cached in Redis)
CREATE TABLE IF NOT EXISTS user_statistics (
    user_id text PRIMARY KEY,
    username text,
    total_files integer DEFAULT 0,
    total_size_bytes bigint DEFAULT 0,
    files_by_type jsonb DEFAULT '{}'::jsonb,
    first_file_date timestamp with time zone,
    last_file_date timestamp with time zone,
    last_active_at timestamp with time zone DEFAULT now(),
    search_count integer DEFAULT 0,
    cache_hit_rate float DEFAULT 0
);

-- Indexes for performance
CREATE INDEX idx_telegram_files_chat_user ON telegram_files(telegram_chat_id, telegram_user_id);
CREATE INDEX idx_telegram_files_file_type ON telegram_files(file_type);
CREATE INDEX idx_telegram_files_processing_status ON telegram_files(processing_status) 
    WHERE processing_status IN ('pending', 'failed');
CREATE INDEX idx_telegram_files_telegram_date ON telegram_files(telegram_date DESC);
CREATE INDEX idx_telegram_files_embedding ON telegram_files 
    USING ivfflat (content_embedding vector_cosine_ops) 
    WITH (lists = 100)
    WHERE content_embedding IS NOT NULL;
CREATE INDEX idx_telegram_files_cache_key ON telegram_files(cache_key);
CREATE INDEX idx_telegram_files_tags ON telegram_files USING gin(tags);

CREATE INDEX idx_processing_queue_status ON processing_queue(status, priority DESC, scheduled_at)
    WHERE status IN ('pending', 'retry');
CREATE INDEX idx_cache_entries_expires ON cache_entries(expires_at)
    WHERE expires_at IS NOT NULL;

-- Full-text search indexes
CREATE INDEX idx_telegram_files_text_search ON telegram_files 
    USING gin(to_tsvector('english', 
        coalesce(extracted_text, '') || ' ' || 
        coalesce(message_text, '') || ' ' || 
        coalesce(original_filename, '')
    ));

-- Functions

-- Enhanced similarity search with caching hints
CREATE OR REPLACE FUNCTION search_files_similarity(
    query_embedding vector(1536),
    match_count int DEFAULT 10,
    user_id text DEFAULT NULL,
    chat_id text DEFAULT NULL,
    file_types text[] DEFAULT NULL,
    min_similarity float DEFAULT 0.0
) RETURNS TABLE (
    id uuid,
    s3_key text,
    file_type text,
    original_filename text,
    extracted_text text,
    content_summary text,
    message_text text,
    similarity float,
    cache_key text,
    metadata jsonb
) AS $$
BEGIN
    -- Update access stats for returned results
    UPDATE telegram_files tf
    SET 
        last_accessed_at = now(),
        access_count = access_count + 1
    FROM (
        SELECT f.id
        FROM telegram_files f
        WHERE 
            (user_id IS NULL OR f.telegram_user_id = user_id)
            AND (chat_id IS NULL OR f.telegram_chat_id = chat_id)
            AND (file_types IS NULL OR f.file_type = ANY(file_types))
            AND f.content_embedding IS NOT NULL
            AND f.is_deleted = false
            AND (1 - (f.content_embedding <=> query_embedding)) >= min_similarity
        ORDER BY f.content_embedding <=> query_embedding
        LIMIT match_count
    ) matched
    WHERE tf.id = matched.id;
    
    -- Return results
    RETURN QUERY
    SELECT
        f.id,
        f.s3_key,
        f.file_type,
        f.original_filename,
        f.extracted_text,
        f.content_summary,
        f.message_text,
        (1 - (f.content_embedding <=> query_embedding))::float as similarity,
        f.cache_key,
        f.metadata
    FROM telegram_files f
    WHERE 
        (user_id IS NULL OR f.telegram_user_id = user_id)
        AND (chat_id IS NULL OR f.telegram_chat_id = chat_id)
        AND (file_types IS NULL OR f.file_type = ANY(file_types))
        AND f.content_embedding IS NOT NULL
        AND f.is_deleted = false
        AND (1 - (f.content_embedding <=> query_embedding)) >= min_similarity
    ORDER BY f.content_embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Get processing queue items
CREATE OR REPLACE FUNCTION get_next_processing_items(
    worker_id text,
    batch_size int DEFAULT 10
) RETURNS SETOF processing_queue AS $$
BEGIN
    RETURN QUERY
    UPDATE processing_queue
    SET 
        status = 'processing',
        started_at = now(),
        worker_id = worker_id,
        attempts = attempts + 1
    WHERE id IN (
        SELECT id
        FROM processing_queue
        WHERE status IN ('pending', 'retry')
            AND scheduled_at <= now()
            AND attempts < max_attempts
        ORDER BY priority DESC, scheduled_at
        LIMIT batch_size
        FOR UPDATE SKIP LOCKED
    )
    RETURNING *;
END;
$$ LANGUAGE plpgsql;

-- Update user statistics
CREATE OR REPLACE FUNCTION update_user_statistics()
RETURNS trigger AS $$
BEGIN
    INSERT INTO user_statistics (
        user_id,
        username,
        total_files,
        total_size_bytes,
        files_by_type,
        first_file_date,
        last_file_date
    )
    VALUES (
        NEW.telegram_user_id,
        NEW.telegram_username,
        1,
        COALESCE(NEW.file_size, 0),
        jsonb_build_object(NEW.file_type, 1),
        NEW.created_at,
        NEW.created_at
    )
    ON CONFLICT (user_id) DO UPDATE
    SET
        username = COALESCE(EXCLUDED.username, user_statistics.username),
        total_files = user_statistics.total_files + 1,
        total_size_bytes = user_statistics.total_size_bytes + COALESCE(NEW.file_size, 0),
        files_by_type = user_statistics.files_by_type || 
            jsonb_build_object(
                NEW.file_type, 
                COALESCE((user_statistics.files_by_type->>NEW.file_type)::int, 0) + 1
            ),
        last_file_date = NEW.created_at,
        last_active_at = now();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers
CREATE TRIGGER update_user_stats_on_file_insert
    AFTER INSERT ON telegram_files
    FOR EACH ROW
    EXECUTE FUNCTION update_user_statistics();

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_telegram_files_updated_at
    BEFORE UPDATE ON telegram_files
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Policies
ALTER TABLE telegram_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE image_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE audio_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE cache_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_statistics ENABLE ROW LEVEL SECURITY;

-- Grant access to service role
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
CREATE POLICY "Service role full access" ON processing_queue
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON cache_entries
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON user_statistics
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Grant execute permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO service_role;