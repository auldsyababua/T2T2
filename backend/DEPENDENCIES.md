# Backend Dependencies Documentation

This document explains all Python dependencies used in the T2T2 backend, their purpose, and any special configuration requirements.

## Core Framework Dependencies

### FastAPI (0.109.0)
- **Purpose**: Modern web framework for building the REST API
- **Why this version**: Stable release with all features we need
- **Includes**: Starlette (ASGI framework) and Pydantic (data validation)

### Uvicorn (0.27.0)
- **Purpose**: ASGI server to run FastAPI applications
- **Configuration**: Uses `[standard]` extras for better performance
- **Note**: Required for production deployment

### Pydantic (2.5.3) & Pydantic-settings (2.1.0)
- **Purpose**: Data validation and settings management
- **Usage**: Request/response models and environment variable validation

## Database Dependencies

### SQLAlchemy (2.0.25)
- **Purpose**: SQL toolkit and ORM
- **Why v2**: Modern async support and better type hints

### asyncpg (0.29.0)
- **Purpose**: PostgreSQL driver for async operations
- **Note**: Only used in production with PostgreSQL

### aiosqlite (0.19.0)
- **Purpose**: SQLite driver for async operations
- **Note**: Used for testing and local development
- **Special handling**: Models use `with_variant` for compatibility

### pgvector (0.2.4)
- **Purpose**: PostgreSQL extension for vector similarity search
- **Note**: Used for embedding storage and semantic search
- **Fallback**: Uses JSON columns when running with SQLite

### alembic (1.13.1)
- **Purpose**: Database migration tool
- **Usage**: Managing schema changes across environments

## Authentication & Security

### PyJWT (2.8.0)
- **Purpose**: JSON Web Token implementation for API authentication
- **Import name**: `import jwt` (not `pyjwt`)
- **Configuration**: Uses HS256 algorithm by default

### cryptography (41.0.7)
- **Purpose**: Cryptographic primitives
- **Usage**: Telegram authentication hash verification

## Telegram Integration

### python-telegram-bot (21.0)
- **Purpose**: Official Telegram Bot API wrapper
- **Usage**: Bot interactions and updates

### Telethon (1.34.0)
- **Purpose**: Telegram client API for user accounts
- **Usage**: Fetching user's chat history
- **Note**: Requires TELEGRAM_API_ID and TELEGRAM_API_HASH

## AI/ML Dependencies

### openai (1.10.0)
- **Purpose**: Official OpenAI API client
- **Usage**: GPT models for chat analysis and embeddings

### langchain (0.1.0) & langchain-openai (0.0.3)
- **Purpose**: LLM application framework
- **Usage**: RAG pipeline and prompt management

### langchain-community (0.0.10)
- **Purpose**: Community integrations for LangChain
- **Usage**: Additional vector stores and utilities

### open-clip-torch (2.24.0)
- **Purpose**: OpenAI's CLIP model implementation
- **Usage**: Image embeddings for visual search
- **Note**: Includes PyTorch as dependency

## Image Processing

### Pillow (10.2.0)
- **Purpose**: Python Imaging Library
- **Usage**: Image manipulation and preprocessing

### pytesseract (0.3.10)
- **Purpose**: Python wrapper for Tesseract OCR
- **System requirement**: Requires `tesseract-ocr` system package
- **Installation**: `sudo apt-get install tesseract-ocr`

### qrcode[pil] (7.4.2)
- **Purpose**: QR code generation
- **Usage**: Telegram authentication QR codes
- **Note**: Uses `[pil]` extra for image generation

## Utilities

### python-dotenv (1.0.0)
- **Purpose**: Load environment variables from .env files
- **Import name**: `from dotenv import load_dotenv`

### httpx (0.27.0)
- **Purpose**: Async HTTP client
- **Usage**: External API calls and webhook handling

### upstash-redis (1.1.0)
- **Purpose**: Redis client for Upstash (serverless Redis)
- **Usage**: Caching layer for embeddings and API responses
- **Optional**: Falls back to in-memory cache if not configured

### boto3 (1.34.0)
- **Purpose**: AWS SDK for Python
- **Usage**: S3 for image storage
- **Configuration**: Requires AWS credentials

## Development Dependencies

### pytest (7.4.4) & pytest-asyncio (0.23.3)
- **Purpose**: Testing framework with async support
- **Usage**: Unit and integration tests

### pytest-cov (via pip install)
- **Purpose**: Coverage reporting for pytest
- **Note**: Not in requirements.txt but needed for CI

### black (23.12.1)
- **Purpose**: Code formatter
- **Configuration**: Line length 88 (default)

### ruff (0.1.11)
- **Purpose**: Fast Python linter
- **Configuration**: See pyproject.toml for rules

## Environment Variables Required

### Essential (must be set)
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET_KEY`: Secret for JWT signing

### Telegram (required for Telegram features)
- `TELEGRAM_API_ID`: From https://my.telegram.org
- `TELEGRAM_API_HASH`: From https://my.telegram.org
- `TELEGRAM_BOT_TOKEN`: From @BotFather

### Optional Services
- `OPENAI_API_KEY`: For embeddings and chat completion
- `AWS_ACCESS_KEY_ID`: For S3 image storage
- `AWS_SECRET_ACCESS_KEY`: For S3 image storage
- `AWS_REGION`: For S3 image storage
- `S3_BUCKET_NAME`: For S3 image storage
- `UPSTASH_REDIS_REST_URL`: For Redis caching
- `UPSTASH_REDIS_REST_TOKEN`: For Redis caching

## System Dependencies

The following system packages must be installed:

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y \
    tesseract-ocr \
    postgresql-client \
    build-essential \
    python3-dev
```

### macOS
```bash
brew install tesseract postgresql
```

## Docker Considerations

When building Docker images, ensure:
1. Multi-stage builds to minimize image size
2. System dependencies are installed in the build stage
3. Only production dependencies are included (no pytest, black, etc.)

## Dependency Management

### Adding New Dependencies
1. Add to `requirements.txt` with pinned version
2. Update this document with:
   - Purpose and usage
   - Any special import names
   - Required environment variables
   - System dependencies
3. Run `python scripts/check_imports.py` to verify
4. Test with both PostgreSQL and SQLite

### Updating Dependencies
1. Check for breaking changes in release notes
2. Run full test suite after updates
3. Update version pins in requirements.txt
4. Test in staging environment first

### Security Monitoring
- Weekly automated checks via `.github/workflows/dependency-check.yml`
- Uses `pip-audit` for vulnerability scanning
- Creates GitHub issues for problems