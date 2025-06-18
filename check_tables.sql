-- Check which tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'telegram_files',
    'image_metadata',
    'video_metadata',
    'audio_metadata',
    'document_metadata',
    'processing_queue',
    'cache_entries',
    'user_statistics'
)
ORDER BY table_name;