# Railway Deployment Guide for T2T2

## Prerequisites

- Railway account (token stored securely)
- GitHub repository connected to Railway
- All environment variables ready

## Deployment Steps

### 1. Push to GitHub

```bash
git add .
git commit -m "Add Railway deployment configuration"
git push origin main
```

### 2. Create Railway Project

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Create New Project → Deploy from GitHub repo
3. Select your T2T2 repository

### 3. Configure Services

#### Backend Service (Web)

1. Railway should auto-detect the backend service
2. Set start command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

#### Bot Service (Worker)

1. Add New Service → Empty Service
2. Set start command: `python bot.py`
3. Name it "telegram-bot"

### 4. Environment Variables

Add these variables to BOTH services in Railway:

#### Required Variables

```
DATABASE_URL=postgresql+asyncpg://postgres.tzsfkbwpgklwvsyypacc:4a408f14ffbb759f67ab105763b426c35d714075d20cf95137e4ba92ae355ff0@aws-0-us-east-2.pooler.supabase.com:6543/postgres
JWT_SECRET_KEY=[GENERATE A SECURE KEY]
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=7
TELEGRAM_API_ID=[GET FROM https://my.telegram.org]
TELEGRAM_API_HASH=[GET FROM https://my.telegram.org]
TELEGRAM_BOT_TOKEN=8165476295:AAFyLp4vqtHwFngH5MYDn5eOd2DdibHFGLo
OPENAI_API_KEY=[YOUR OPENAI API KEY]
LOG_LEVEL=INFO
ENVIRONMENT=production
```

#### Optional Variables (if using)

```
AWS_ACCESS_KEY_ID=[If using S3 for images]
AWS_SECRET_ACCESS_KEY=[If using S3 for images]
AWS_REGION=us-east-1
S3_BUCKET_NAME=t2t2-images
UPSTASH_REDIS_REST_URL=[If using Redis cache]
UPSTASH_REDIS_REST_TOKEN=[If using Redis cache]
```

#### Backend-Specific Variables

```
BACKEND_URL=https://[your-railway-backend-url].railway.app
CORS_ORIGINS=["https://your-frontend-url.vercel.app"]
RATE_LIMIT_PER_MINUTE=100
```

### 5. Database Setup

Run the SQL migration after deployment:

```sql
-- Connect to your Supabase database and run:
-- From backend/db/add_chunk_metadata.sql
ALTER TABLE message_embeddings
ADD COLUMN IF NOT EXISTS chunk_metadata JSONB;
```

### 6. Verify Deployment

1. Check Railway logs for both services
2. Test bot at @talk2telegrambot
3. Try `/start` command - should show Mini App button
4. Only @colin_10NetZero and @Joel_10NetZero can access

### 7. Update Frontend

Update the frontend API URL in Vercel:

- Set `VITE_API_URL` to your Railway backend URL

## Troubleshooting

### Bot not responding

- Check worker service logs
- Verify TELEGRAM_BOT_TOKEN is correct
- Ensure bot service is running

### Database connection issues

- Verify DATABASE_URL is correct
- Check if Supabase allows Railway IPs
- Run database migrations

### Authentication failures

- Verify JWT_SECRET_KEY is set
- Check authorized_users.py includes your Telegram handle
- Ensure username starts with @

## Post-Deployment

1. Monitor logs for errors
2. Test full flow: Bot → Mini App → Chat selection → Indexing
3. Set up Railway deployment webhooks for auto-deploy on git push
