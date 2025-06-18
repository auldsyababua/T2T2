# Setting up Supabase Tables

## What you need to do:

1. Go to your Supabase Dashboard
2. Click on "SQL Editor" in the left sidebar
3. Copy the entire contents of `supabase_setup.sql`
4. Paste it into the SQL editor
5. Click "Run" to execute

This will create:
- The `documents` table for vector storage
- The `user_actions` audit table
- Required indexes and functions
- The pgvector extension

## Do NOT enable:
- GitHub integration (not needed for bot)
- Vercel integration (not needed for bot)
- S3 wrapper (bot uses vector DB, not file storage)

The bot only needs:
- The documents table with pgvector
- The service_role API key (which we already fixed)