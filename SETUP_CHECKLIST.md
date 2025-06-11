# T2T2 Setup Checklist

## Cloud Services Setup

### ✅ Already Have:
- [x] Telegram Bot Token
- [x] Telegram API ID & Hash
- [x] OpenAI API Key
- [x] JWT Secret Key

### ❌ Need to Set Up:

#### 1. Supabase (Database)
- [ ] Create account at https://supabase.com
- [ ] Create new project "t2t2"
- [ ] Enable pgvector extension (SQL Editor → `CREATE EXTENSION vector;`)
- [ ] Copy connection string from Settings → Database
- [ ] Update `DATABASE_URL` in backend/.env

#### 2. Upstash (Redis)
- [ ] Create account at https://upstash.com
- [ ] Create Redis database
- [ ] Copy REST URL and Token
- [ ] Update `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` in backend/.env

#### 3. AWS S3 (Image Storage)
- [ ] Create S3 bucket named "t2t2-images"
- [ ] Create IAM user with S3 access
- [ ] Generate Access Key ID and Secret
- [ ] Update `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in backend/.env

## After Setup:
1. Run `cd backend && pip install -r requirements.txt`
2. Test database connection: `python -c "from db.database import init_db; import asyncio; asyncio.run(init_db())"`
3. Start backend: `python main.py`