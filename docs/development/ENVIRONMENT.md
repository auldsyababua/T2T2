# Environment & Configuration Reference

**Last Updated**: 2025-06-11
**Auto-Check**: Run `./scripts/verify_environment.sh` to validate your setup

## Required System Dependencies

```bash
# Python
python --version  # Required: 3.11+

# Node.js
node --version   # Required: 18.0+
npm --version    # Required: 9.0+

# PostgreSQL Client
psql --version   # Required: 14+ (for local testing)

# Tesseract OCR
tesseract --version  # Required: 5.0+

# Redis CLI (optional, for debugging)
redis-cli --version  # Optional: 7.0+
```

## Python Dependencies

```txt
# Core (see backend/requirements.txt for versions)
fastapi==0.104.1
sqlalchemy==2.0.23
asyncpg==0.29.0
python-telegram-bot==20.7
telethon==1.33.1
langchain==0.1.0
openai==1.6.1
pgvector==0.2.4
redis==5.0.1
boto3==1.34.11
pytesseract==0.3.10
transformers==4.36.2  # For CLIP
Pillow==10.1.0
```

## Environment Variables

All stored in `backend/.env`:

```bash
# Database (Supabase)
DATABASE_URL=postgresql+asyncpg://...  # Direct connection, port 5432

# Redis (Upstash)
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=...  # Same as password

# OpenAI
OPENAI_API_KEY=sk-...

# AWS S3 (us-west-1 region)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_BUCKET_NAME=t2t2-images
AWS_REGION=us-west-1  # NOT us-east-2

# Telegram
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
TELEGRAM_BOT_TOKEN=...

# Auth
JWT_SECRET=...
```

## Critical Service URLs

- **Supabase Dashboard**: https://app.supabase.com/project/tzsfkbwpgklwvsyypacc
- **Upstash Console**: https://console.upstash.com/
- **AWS S3 Console**: https://s3.console.aws.amazon.com/s3/buckets/t2t2-images
- **GitHub Repo**: https://github.com/auldsyababua/T2T2

## Docker Services

```yaml
# Local development only (production uses cloud services)
postgres:
  image: pgvector/pgvector:pg16
  ports: 5432:5432
  
redis:
  image: redis:7-alpine
  ports: 6379:6379
```

## Validation Script

Create `scripts/verify_environment.sh`:
```bash
#!/bin/bash
echo "Checking environment..."

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python: $python_version"

# Check Node version
node_version=$(node -v)
echo "Node: $node_version"

# Check required files
files=("backend/.env" "backend/requirements.txt" "UI/package.json")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file missing"
    fi
done

# Check environment variables
source backend/.env
vars=("DATABASE_URL" "UPSTASH_REDIS_REST_URL" "OPENAI_API_KEY" "AWS_ACCESS_KEY_ID")
for var in "${vars[@]}"; do
    if [ -n "${!var}" ]; then
        echo "✓ $var is set"
    else
        echo "✗ $var is missing"
    fi
done
```

## Common Environment Issues

1. **pgvector extension**: Must run `CREATE EXTENSION vector;` in Supabase
2. **Supabase pooler**: Use direct connection (5432), not transaction pooler
3. **AWS region**: Bucket is in us-west-1, not us-east-2
4. **Redis token**: UPSTASH_REDIS_REST_TOKEN is the password
5. **Python path**: Ensure `backend/` is in PYTHONPATH for imports