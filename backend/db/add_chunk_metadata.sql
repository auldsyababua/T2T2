-- Migration to add chunk_metadata column to message_embeddings table
ALTER TABLE message_embeddings 
ADD COLUMN IF NOT EXISTS chunk_metadata JSONB;