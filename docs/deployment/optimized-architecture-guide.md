# Optimized T2T2 Bot Deployment Guide

## Architecture Overview

The optimized T2T2 bot uses a scalable, event-driven architecture:

```
Telegram → Bot → S3 → Edge Functions → Processing → Vector DB
                          ↓                ↓
                       Redis Cache    Metadata Tables
```

## Setup Steps

### 1. Database Setup

Run in Supabase SQL Editor:
```sql
-- Run optimal_schema.sql
```

This creates:
- `telegram_files` - Main file tracking
- Metadata tables for each file type
- Processing queue
- Cache tracking
- User statistics

### 2. Edge Functions Deployment

Deploy the Edge Functions to Supabase:

```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Link your project
supabase link --project-ref tzsfkbwpgklwvsyypacc

# Deploy functions
supabase functions deploy process-file
supabase functions deploy process-image

# Set environment variables
supabase secrets set OPENAI_API_KEY=your_key
supabase secrets set AWS_ACCESS_KEY_ID=your_key
supabase secrets set AWS_SECRET_ACCESS_KEY=your_secret
supabase secrets set AWS_REGION=us-east-1
```

### 3. Redis Setup (Optional)

If using Supabase's Redis integration:
1. Go to Database → Extensions
2. Enable Redis extension
3. Configure connection in bot

Or use external Redis:
- Update `REDIS_HOST`, `REDIS_PORT` in `.env`

### 4. S3 Configuration

Your S3 bucket (`t2t2-images`) should have folders:
```
t2t2-images/
├── images/
├── videos/
├── audio/
├── documents/
├── voice/
├── animations/
├── stickers/
└── other/
```

### 5. Bot Deployment

#### Local Testing:
```bash
python optimized_t2t2_bot.py
```

#### Production Deployment:

**Option 1: Railway**
```bash
railway up
```

**Option 2: Docker**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "optimized_t2t2_bot.py"]
```

**Option 3: Systemd Service**
```ini
[Unit]
Description=T2T2 Telegram Bot
After=network.target

[Service]
Type=simple
User=t2t2bot
WorkingDirectory=/opt/t2t2bot
Environment="PATH=/opt/t2t2bot/venv/bin"
ExecStart=/opt/t2t2bot/venv/bin/python optimized_t2t2_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Environment Variables

Complete `.env.supabase_bot`:
```bash
# Telegram
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_BOT_TOKEN=

# OpenAI
OPENAI_API_KEY=

# Supabase
SUPABASE_URL=
SUPABASE_SERVICE_KEY=

# AWS S3
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET_NAME=t2t2-images

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Admin
ADMIN_TELEGRAM_ID=
```

## Processing Pipeline

### File Upload Flow:
1. User sends file to bot
2. Bot downloads and uploads to S3
3. Metadata stored in `telegram_files` table
4. Edge Function triggered for processing
5. Processing extracts text/features
6. Embeddings generated and stored
7. Cache updated for frequent files

### Search Flow:
1. User sends search query
2. Check Redis cache for recent searches
3. Generate query embedding
4. Vector similarity search in pgvector
5. Return results with S3 URLs
6. Update cache and statistics

## Monitoring

### Database Queries:
```sql
-- Processing queue status
SELECT status, COUNT(*) 
FROM processing_queue 
GROUP BY status;

-- User activity
SELECT 
  user_id, 
  username, 
  total_files, 
  total_size_bytes / 1048576 as mb
FROM user_statistics 
ORDER BY total_files DESC;

-- File type distribution
SELECT file_type, COUNT(*) 
FROM telegram_files 
GROUP BY file_type;
```

### Bot Health Checks:
- Monitor processing queue length
- Check failed processing rate
- Track cache hit rate
- Monitor Edge Function execution time

## Performance Optimization

1. **Caching Strategy**:
   - Hot embeddings in Redis
   - Recent search results cached
   - User statistics cached

2. **Processing Optimization**:
   - Batch similar file types
   - Priority queue for active users
   - Skip processing for duplicates

3. **Search Optimization**:
   - Pre-filter by file type
   - Use minimum similarity threshold
   - Limit result count

## Scaling Considerations

1. **Database**:
   - Enable connection pooling
   - Consider read replicas for search
   - Archive old files periodically

2. **Edge Functions**:
   - Auto-scales with Supabase
   - Monitor execution limits
   - Consider batch processing

3. **S3 Storage**:
   - Enable lifecycle rules
   - Use intelligent tiering
   - Consider CDN for serving

## Security

1. **Access Control**:
   - RLS policies on all tables
   - User isolation in searches
   - Admin-only statistics

2. **Data Protection**:
   - S3 bucket private
   - Signed URLs for access
   - Encryption at rest

3. **Rate Limiting**:
   - Per-user file limits
   - Search rate limiting
   - Processing queue limits

## Troubleshooting

### Common Issues:

1. **Processing Stuck**:
   ```sql
   UPDATE processing_queue 
   SET status = 'pending', attempts = 0 
   WHERE status = 'processing' 
   AND started_at < NOW() - INTERVAL '1 hour';
   ```

2. **Cache Out of Sync**:
   ```python
   # Clear Redis cache
   redis_client.flushdb()
   ```

3. **S3 Access Issues**:
   - Verify IAM permissions
   - Check bucket policy
   - Confirm credentials

## Future Enhancements

1. **Advanced Processing**:
   - Video scene detection
   - Multi-language OCR
   - Audio fingerprinting

2. **Search Features**:
   - Temporal search ("files from last week")
   - Faceted search by metadata
   - Similar image search

3. **Integrations**:
   - Webhook notifications
   - Export to cloud storage
   - API for external access