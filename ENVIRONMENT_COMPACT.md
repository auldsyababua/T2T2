# Environment

## System Deps
```
python≥3.11 | node≥18 | psql≥14 | tesseract≥5 | redis-cli≥7(opt)
```

## Python Core
```
fastapi==0.104.1        sqlalchemy==2.0.23      asyncpg==0.29.0
telegram-bot==20.7      telethon==1.33.1        langchain==0.1.0
openai==1.6.1          pgvector==0.2.4         redis==5.0.1
boto3==1.34.11         pytesseract==0.3.10     transformers==4.36.2
```

## Env Vars (backend/.env)
```
DATABASE_URL=postgresql+asyncpg://...@:5432  # Direct, NOT pooler
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=...               # =password
OPENAI_API_KEY=sk-...
AWS_ACCESS_KEY_ID=... | AWS_SECRET_ACCESS_KEY=...
AWS_BUCKET_NAME=t2t2-images | AWS_REGION=us-west-1
TELEGRAM_API_ID=... | TELEGRAM_API_HASH=... | TELEGRAM_BOT_TOKEN=...
JWT_SECRET=...
```

## Services
- Supabase: https://app.supabase.com/project/tzsfkbwpgklwvsyypacc
- Upstash: https://console.upstash.com/
- S3: https://s3.console.aws.amazon.com/s3/buckets/t2t2-images
- GitHub: https://github.com/auldsyababua/T2T2

## Validate
```bash
./scripts/verify_environment.sh
```

## Common Issues
1. pgvector: Run `CREATE EXTENSION vector;` in Supabase
2. Pooler: Use direct:5432, not transaction pooler
3. AWS: Bucket in us-west-1, NOT us-east-2
4. Redis: token=password
5. Python: Ensure backend/ in PYTHONPATH