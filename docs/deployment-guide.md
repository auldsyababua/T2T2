# T2T2 Deployment Guide

This guide covers deploying T2T2 to production using various platforms.

## Prerequisites

- Domain name (for HTTPS)
- Telegram API credentials from [my.telegram.org](https://my.telegram.org/apps)
- OpenAI API key
- Database (PostgreSQL with pgvector extension)
- Redis instance (for caching)
- S3-compatible storage (for images)

## Environment Variables

Create a `.env` file with all required variables:

```bash
# Telegram API
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Security
SESSION_ENCRYPTION_KEY=generate_with_openssl_rand_base64_32
SECRET_KEY=generate_with_openssl_rand_hex_32

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# AI
OPENAI_API_KEY=your_openai_key

# Storage
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket

# Cache
UPSTASH_REDIS_REST_URL=your_redis_url
UPSTASH_REDIS_REST_TOKEN=your_redis_token
```

## Deployment Options

### 1. Docker Compose (Recommended for VPS)

Perfect for DigitalOcean, AWS EC2, or any VPS with Docker.

```bash
# Clone repository
git clone https://github.com/yourusername/T2T2.git
cd T2T2

# Copy and configure environment
cp .env.example .env
# Edit .env with your values

# Build and start services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# View logs
docker-compose logs -f
```

#### SSL/HTTPS Setup with Caddy

Add Caddy as reverse proxy:

```yaml
# docker-compose.override.yml
services:
  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - backend
      - frontend

volumes:
  caddy_data:
  caddy_config:
```

```Caddyfile
# Caddyfile
yourdomain.com {
    reverse_proxy /api/* backend:8000
    reverse_proxy /* frontend:80
}
```

### 2. Railway (Managed Platform)

Railway provides easy deployment with automatic SSL and scaling.

#### Backend Service

1. Create new Railway project
2. Add PostgreSQL plugin
3. Add Redis plugin
4. Create new service from GitHub
5. Set root directory: `/`
6. Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
7. Add all environment variables
8. Deploy

#### Frontend Service

1. Add another service in same project
2. Set root directory: `UI`
3. Set build command: `npm run build`
4. Set start command: `npm run preview -- --port $PORT`
5. Add environment variable: `VITE_API_URL=https://your-backend.railway.app`
6. Deploy

### 3. Vercel + Railway (Hybrid)

Use Vercel for frontend (free tier) and Railway for backend.

#### Backend on Railway
Same as above Railway backend steps.

#### Frontend on Vercel

1. Connect GitHub repository
2. Set root directory: `UI`
3. Add environment variable: `VITE_API_URL=https://your-backend.railway.app`
4. Deploy

### 4. Kubernetes (Enterprise)

For production-grade deployment with auto-scaling.

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: t2t2-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: t2t2-backend
  template:
    metadata:
      labels:
        app: t2t2-backend
    spec:
      containers:
      - name: backend
        image: your-registry/t2t2-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: t2t2-secrets
              key: database-url
        # Add other env vars
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

## Post-Deployment Steps

### 1. Database Setup

Run migrations:
```bash
# Docker
docker-compose exec backend alembic upgrade head

# Railway/Heroku
railway run alembic upgrade head
```

### 2. Health Checks

Verify services are running:
- Backend health: `https://your-domain.com/health`
- API docs: `https://your-domain.com/docs`
- Frontend: `https://your-domain.com`

### 3. Monitoring

Set up monitoring with:
- **Uptime**: UptimeRobot or Pingdom
- **Logs**: LogDNA or Papertrail
- **Errors**: Sentry
- **Metrics**: Prometheus + Grafana

### 4. Backups

Configure automated backups:
```bash
# PostgreSQL backup script
#!/bin/bash
pg_dump $DATABASE_URL | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
aws s3 cp backup_*.sql.gz s3://your-backup-bucket/
```

## Security Checklist

- [ ] HTTPS enabled on all endpoints
- [ ] Environment variables properly secured
- [ ] Database connections use SSL
- [ ] Redis password protected
- [ ] S3 bucket policies configured
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Session encryption key rotated monthly

## Scaling Considerations

### Backend Scaling
- Use connection pooling for database
- Implement Redis caching aggressively
- Consider read replicas for database
- Use CDN for static assets

### Frontend Scaling
- Enable CDN (Cloudflare, CloudFront)
- Implement proper caching headers
- Use image optimization
- Enable gzip compression

## Troubleshooting

### Common Issues

1. **"Cannot connect to database"**
   - Check DATABASE_URL format
   - Verify pgvector extension installed
   - Check firewall rules

2. **"Session encryption error"**
   - Regenerate SESSION_ENCRYPTION_KEY
   - Clear Redis cache
   - Check key format (base64)

3. **"Rate limit exceeded"**
   - Implement request queuing
   - Add delays in indexing
   - Use multiple Telegram sessions

### Debug Mode

Enable detailed logging:
```bash
# Add to environment
LOG_LEVEL=DEBUG
PYTHONUNBUFFERED=1
```

## Maintenance

### Regular Tasks
- Monitor disk usage (especially for logs)
- Update dependencies monthly
- Rotate encryption keys quarterly
- Review and archive old sessions

### Updates
```bash
# Update backend
docker-compose build backend
docker-compose up -d backend

# Update frontend
docker-compose build frontend
docker-compose up -d frontend

# Run migrations if needed
docker-compose exec backend alembic upgrade head
```