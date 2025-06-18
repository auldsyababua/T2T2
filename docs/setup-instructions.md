# Setup Instructions for T2T2 Bot

## Step 1: Create Supabase Tables (DO THIS FIRST)

1. Go to your Supabase Dashboard
2. Click "SQL Editor" in the left sidebar
3. Copy ALL contents from `supabase_setup.sql` file
4. Paste into the SQL editor
5. Click "Run" button
6. You should see success messages for:
   - Creating pgvector extension
   - Creating documents table
   - Creating indexes
   - Creating functions
   - Creating user_actions table

## Step 2: Configure S3 Wrapper

To add the S3 wrapper in Supabase:

1. Click "Add new wrapper" button
2. Fill in these details:

**Wrapper Configuration:**
- Name: `s3_wrapper`
- Schema: `storage` (or `public` if you prefer)

**S3 Credentials:**
- AWS Access Key ID: (from your AWS account)
- AWS Secret Access Key: (from your AWS account)
- Region: `us-east-1` (or your bucket's region)
- Bucket Name: (your S3 bucket name)

**Table Mappings:**
You'll want to create tables for:
- `s3_images` - to list images stored in S3
- `s3_documents` - for other document types

3. Test the connection
4. Save the wrapper

## Step 3: Update Bot Configuration

Add to `.env.supabase_bot`:
```
# S3 Configuration
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
```

Let me know when you've completed Step 1 (SQL setup) and I'll help with the S3 wrapper configuration!