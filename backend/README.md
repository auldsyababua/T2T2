# T2T2 Backend

FastAPI backend for Talk2Telegram 2 - A multi-tenant Telegram chat analysis system with RAG capabilities.

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+**
2. **PostgreSQL 16+** with pgvector extension (or use SQLite for development)
3. **System dependencies**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr postgresql-client build-essential python3-dev

   # macOS
   brew install tesseract postgresql
   ```

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/auldsyababua/T2T2.git
   cd T2T2/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Required Environment Variables

See [DEPENDENCIES.md](./DEPENDENCIES.md#environment-variables-required) for complete list.

Essential variables:
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET_KEY`: Secret for JWT token signing
- `TELEGRAM_API_ID`: From https://my.telegram.org
- `TELEGRAM_API_HASH`: From https://my.telegram.org

### Database Setup

1. **PostgreSQL (Production)**
   ```bash
   # Create database with pgvector
   createdb t2t2
   psql t2t2 -c "CREATE EXTENSION vector;"
   
   # Run migrations
   alembic upgrade head
   ```

2. **SQLite (Development/Testing)**
   ```bash
   # Set DATABASE_URL for SQLite
   export DATABASE_URL="sqlite+aiosqlite:///./t2t2.db"
   
   # Tables are created automatically
   ```

### Running the Application

```bash
# Development server with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📁 Project Structure

```
backend/
├── api/
│   ├── middleware/      # Rate limiting, CORS, etc.
│   └── routes/          # API endpoints
│       ├── auth.py      # Telegram authentication
│       ├── telegram.py  # Chat fetching & indexing
│       ├── query.py     # RAG queries
│       └── timeline.py  # Timeline generation
├── db/
│   ├── database.py      # Database connection & setup
│   └── init.sql         # Initial schema
├── models/
│   └── models.py        # SQLAlchemy ORM models
├── services/
│   ├── telegram_service.py  # Telethon integration
│   ├── rag_service.py       # LangChain RAG pipeline
│   └── image_service.py     # Image processing & OCR
├── scripts/
│   ├── check_imports.py     # Verify dependencies
│   └── check_env_defaults.py # Check env var handling
├── tests/
│   └── test_*.py        # Test files
├── utils/
│   ├── logging.py       # Structured logging
│   └── cache.py         # Redis/in-memory caching
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
└── DEPENDENCIES.md      # Detailed dependency docs
```

## 🧪 Testing

### Run Tests

```bash
# All tests with coverage
pytest -v --cov=. --cov-report=html

# Specific test file
pytest tests/test_auth.py -v

# Database compatibility tests
pytest tests/test_database_compatibility.py -v
```

### Pre-commit Hooks

Install pre-commit hooks to catch issues before committing:

```bash
pip install pre-commit
pre-commit install
```

This runs:
- Black (code formatting)
- Ruff (linting)
- Import checking
- Environment variable checking
- Quick tests

### CI/CD

GitHub Actions runs on every push:
1. Linting (black, ruff)
2. Import verification
3. Unit tests with PostgreSQL
4. Docker build test
5. Security vulnerability scan (weekly)

## 🔧 Development

### Adding Dependencies

1. Add to `requirements.txt` with pinned version
2. Update [DEPENDENCIES.md](./DEPENDENCIES.md) with:
   - Purpose and usage
   - Import name if different
   - Required environment variables
   - System dependencies
3. Run `python scripts/check_imports.py`
4. Test with both PostgreSQL and SQLite

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback one revision
alembic downgrade -1
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type checking (optional)
mypy . --ignore-missing-imports
```

## 🚀 Deployment

### Docker

```bash
# Build image
docker build -t t2t2-backend .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e JWT_SECRET_KEY="..." \
  t2t2-backend
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
```

### Production Checklist

- [ ] Set strong `JWT_SECRET_KEY`
- [ ] Configure PostgreSQL with pgvector
- [ ] Set up Redis for caching (optional)
- [ ] Configure S3 for image storage
- [ ] Set up SSL/TLS termination
- [ ] Configure rate limiting
- [ ] Set up monitoring/logging
- [ ] Configure backups

## 🔍 API Documentation

When running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

- `POST /api/auth/telegram-auth` - Authenticate with Telegram
- `GET /api/telegram/chats` - List user's chats
- `POST /api/telegram/index-chats` - Start indexing selected chats
- `POST /api/query` - RAG query endpoint
- `POST /api/timeline` - Generate timeline from query

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   python scripts/check_imports.py
   # Ensure all dependencies are in requirements.txt
   ```

2. **Database Connection**
   - Check DATABASE_URL format
   - Ensure PostgreSQL is running
   - For SQLite, ensure directory exists

3. **Telegram Auth Errors**
   - Verify TELEGRAM_API_ID and TELEGRAM_API_HASH
   - Check network connectivity
   - Ensure session files have correct permissions

4. **OCR Not Working**
   - Install tesseract: `sudo apt-get install tesseract-ocr`
   - Check Pillow installation

### Debug Mode

Set environment variable:
```bash
export LOG_LEVEL=DEBUG
```

## 📚 Additional Documentation

- [DEPENDENCIES.md](./DEPENDENCIES.md) - Detailed dependency documentation
- [../ENVIRONMENT.md](../ENVIRONMENT.md) - Environment setup guide
- [../HANDOFF.md](../HANDOFF.md) - Project handoff documentation
- [../dev_log.md](../dev_log.md) - Development history and decisions

## 🤝 Contributing

1. Create feature branch from `main`
2. Write tests for new features
3. Ensure all tests pass
4. Run pre-commit hooks
5. Update documentation
6. Submit pull request

## 📄 License

MIT License - see [LICENSE](../LICENSE) file