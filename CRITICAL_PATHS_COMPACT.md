# Critical Paths

## 🔴 Auth Flow
User→TelegramMiniApp→`auth.py:28-45`→JWT
- HMAC verify→User creation
- **CRITICAL**: Security boundary

## 🔴 Embedding Pipeline  
Messages→`telegram_service.py:45-89`→`rag_service.py:32-67`→pgvector
- Telethon QR→OpenAI→Vector(3072)
- **CRITICAL**: Core functionality

## 🔴 Vector Search
Query→`rag_service.py:108-145`→pgvector <=>→Results
- **CRITICAL**: User-facing, must be fast

## 🟡 Image Processing
Images→`image_service.py:78-112`→OCR+CLIP→S3
- **IMPORTANT**: Enhances search

## 🟡 Rate Limiting
Request→Redis→Continue|429
- **TODO**: middleware/rate_limit.py

## Invariants ⚡
- EVERY query filters by user_id
- NO blocking I/O in handlers
- Embedding dim=3072 always
- Log errors before raising
- Close Telegram clients

## Test Critical
```bash
pytest backend/tests/test_auth.py::test_telegram_verification -v
pytest backend/tests/test_services.py::test_embedding_generation -v
pytest backend/tests/test_services.py::test_vector_search -v
```

## Modify Checklist ✓
1. Add logging before+after
2. Add timing metrics
3. Test error cases
4. Check memory usage
5. Verify multi-tenant isolation