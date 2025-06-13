# Backend Troubleshooting Guide

Quick reference for common issues and their solutions.

## 🚨 CI/CD Failures

### Missing Dependencies

**Error**: `ModuleNotFoundError: No module named 'xxx'`

**Solution**:
1. Add to `requirements.txt`
2. Note special import names:
   - `PyJWT` → `import jwt`
   - `python-dotenv` → `from dotenv import load_dotenv`
   - `python-telegram-bot` → `import telegram`
3. Run `python scripts/check_imports.py` locally

### Database Compatibility

**Error**: `NOT NULL constraint failed: table.id`

**Solution**: 
- SQLite needs special handling for autoincrement
- Use `BigInteger().with_variant(Integer, "sqlite")` for primary keys
- Already fixed in models.py

**Error**: `CREATE EXTENSION vector` fails

**Solution**:
- pgvector is PostgreSQL-only
- Code already handles this conditionally
- SQLite uses JSON columns instead

### Environment Variables

**Error**: `TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'`

**Solution**:
- Add default values: `os.getenv("VAR", "default")`
- For required vars, check at startup
- Run `python scripts/check_env_defaults.py`

### Linting Failures

**Error**: `black --check .` fails

**Solution**:
```bash
black .
git add -u
git commit -m "style: apply black formatting"
```

**Error**: `ruff` E731 lambda assignment

**Solution**:
- Change `var = lambda x: ...` to `def var(x): return ...`

## 🔧 Local Development Issues

### Import Errors

**Problem**: Import works in IDE but fails when running

**Check**:
1. Virtual environment activated?
2. All dependencies installed? `pip install -r requirements.txt`
3. Running from correct directory? Should be in `backend/`
4. PYTHONPATH issues? Run from backend: `python main.py`

### Database Connection

**PostgreSQL Error**: `role "root" does not exist`

**Solution**:
- Check DATABASE_URL has correct username
- For Docker tests, we use SQLite (already configured)

**SQLite Error**: `no such table: users`

**Solution**:
```python
from db.database import init_db
import asyncio
asyncio.run(init_db())
```

### Telegram Integration

**Error**: `AuthKeyUnregisteredError`

**Solution**:
- Don't test Telegram endpoints without proper mocking
- Use `/api/timeline/saved` for auth testing instead
- Real Telegram testing needs valid session file

## 🐳 Docker Issues

### Build Failures

**Error**: Missing system dependencies

**Solution**: Dockerfile must include:
```dockerfile
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    postgresql-client \
    build-essential \
    python3-dev
```

### Runtime Errors

**Error**: Can't connect to database

**Solution**:
- Use docker-compose for networking
- Or use SQLite for simple tests: `DATABASE_URL=sqlite+aiosqlite:///:memory:`

## 🧪 Test Failures

### Async Test Issues

**Problem**: `RuntimeError: This event loop is already running`

**Solution**:
- Use `pytest-asyncio`
- Mark async tests: `@pytest.mark.asyncio`
- Don't mix sync and async in same test

### Database Test Isolation

**Problem**: Tests affect each other

**Solution**:
- Each test uses transaction rollback
- Don't use `test_db.commit()` in tests unless needed
- Use fixtures from conftest.py

## 📝 Pre-commit Hook Failures

### Setup

```bash
pip install pre-commit
pre-commit install
```

### Common Failures

1. **Import checker fails**
   - Update requirements.txt
   - Check import name mappings

2. **Env checker fails**
   - Add defaults to os.getenv() calls
   - Document required vars

3. **Tests fail**
   - Run tests locally first
   - Check test database setup

## 🚀 Production Issues

### Performance

**Slow Queries**:
- Add database indexes
- Use connection pooling
- Enable query logging: `echo=True` in development only

**High Memory Usage**:
- Batch large operations
- Use async generators for large datasets
- Configure connection pool limits

### Monitoring

**Add Logging**:
```python
from utils.logging import setup_logger
logger = setup_logger(__name__)
logger.info("Operation started", extra={"user_id": user.id})
```

**Health Checks**:
- Add `/health` endpoint
- Check database connectivity
- Verify external services

## 🔒 Security

### Prompt Injection Protection

**For AI Response Generation (Future)**:

The codebase includes comprehensive prompt injection protections in `utils/security.py`:

1. **Query Sanitization**:
   - Length limits (500 chars)
   - Control character removal
   - Unicode normalization

2. **Injection Detection**:
   - Common injection patterns
   - Exfiltration attempts
   - Suspicious character patterns

3. **Safe Prompt Structure**:
   - System message isolation
   - Context limiting (20 messages max)
   - Response length limits

4. **Security Logging**:
   - All injection attempts are logged
   - Monitoring for abuse patterns

**Example Usage**:
```python
from utils.security import sanitize_query, detect_injection_attempt

query = sanitize_query(user_input)
if detect_injection_attempt(query):
    # Log and handle suspicious query
    pass
```

## 🆘 Getting Help

1. **Check Logs**: Set `LOG_LEVEL=DEBUG`
2. **Run Checks**: 
   ```bash
   python scripts/check_imports.py
   python scripts/check_env_defaults.py
   pytest tests/test_database_compatibility.py -v
   pytest tests/test_security.py -v
   ```
3. **Search Issues**: GitHub issues may have solutions
4. **Documentation**: 
   - [README.md](./README.md)
   - [DEPENDENCIES.md](./DEPENDENCIES.md)
   - [../HANDOFF.md](../HANDOFF.md)