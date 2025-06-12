# T2T2 Setup Checklist

## Cloud Services Setup

### ✅ Already Have:
- [x] Telegram Bot Token
- [x] Telegram API ID & Hash
- [x] OpenAI API Key
- [x] JWT Secret Key

### ✅ Need to Set Up:

#### 1. Supabase (Database)
- [x] Create account at https://supabase.com
- [x] Create new project "t2t2"
- [x] Enable pgvector extension (SQL Editor → `CREATE EXTENSION vector;`)
- [x] Copy connection string from Settings → Database
- [x] Update `DATABASE_URL` in backend/.env

#### 2. Upstash (Redis)
- [x] Create account at https://upstash.com
- [x] Create Redis database
- [x] Copy REST URL and Token
- [x] Update `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` in backend/.env

#### 3. AWS S3 (Image Storage)
- [x] Create S3 bucket named "t2t2-images"
- [x] Create IAM user with S3 access
- [x] Generate Access Key ID and Secret
- [x] Update `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in backend/.env

## After Setup:
1. Run `cd backend && pip install -r requirements.txt`
2. Test database connection: `python -c "from db.database import init_db; import asyncio; asyncio.run(init_db())"`
3. Start backend: `python main.py`
- [x] Test new task
