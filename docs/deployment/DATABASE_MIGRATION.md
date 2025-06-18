# Database Migration Guide

## Run chunk_metadata Migration on Supabase

### Option 1: Using Supabase Dashboard (Recommended)

1. **Login to Supabase**
   - Go to https://supabase.com/dashboard
   - Select your project

2. **Open SQL Editor**
   - Click on **SQL Editor** in the left sidebar
   - Click **New query**

3. **Run Migration**
   - Copy and paste this SQL:
   ```sql
   -- Add chunk_metadata column to message_embeddings table
   ALTER TABLE message_embeddings
   ADD COLUMN IF NOT EXISTS chunk_metadata JSONB;
   
   -- Create index for better query performance
   CREATE INDEX IF NOT EXISTS idx_message_embeddings_chunk_metadata 
   ON message_embeddings USING GIN (chunk_metadata);
   ```

4. **Execute**
   - Click **Run** or press `Cmd/Ctrl + Enter`
   - Should see "Success" message

### Option 2: Using psql CLI

```bash
# Connect to database
psql "postgresql://postgres.tzsfkbwpgklwvsyypacc:4a408f14ffbb759f67ab105763b426c35d714075d20cf95137e4ba92ae355ff0@aws-0-us-east-2.pooler.supabase.com:6543/postgres"

# Run migration
\i backend/db/add_chunk_metadata.sql
```

### Verify Migration

Run this query to verify:
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'message_embeddings' 
AND column_name = 'chunk_metadata';
```

Should return one row showing the column exists.

## What This Migration Does

- Adds `chunk_metadata` JSONB column to store:
  - Original message timestamps
  - Reply context
  - Sender information
  - Message relationships
- Enables the smart chunking feature for better timeline generation
- No existing data is affected (column allows NULL)