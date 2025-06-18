# Critical Code Paths & Architecture

**IMPORTANT**: These are the most critical components. Changes here require extra care and testing.

## 🔴 Critical Path 1: Authentication Flow

```
User → Telegram Mini App → backend/api/routes/auth.py → JWT Token
                                    ↓
                         verify_telegram_auth()
                                    ↓
                         Database User Creation
```

**Critical Files**:
- `backend/api/routes/auth.py:28-45` - HMAC verification
- `backend/models/models.py:14-28` - User model with RLS

**Why Critical**: Security boundary. Errors here expose user data.

## 🔴 Critical Path 2: Message Embedding Pipeline

```
Telegram Messages → TelegramService → RAGService → Database
                         ↓               ↓
                   Telethon QR      OpenAI API
                         ↓               ↓
                   Message Fetch    Embeddings
                                        ↓
                                   pgvector storage
```

**Critical Files**:
- `backend/services/telegram_service.py:45-89` - Message fetching
- `backend/services/rag_service.py:32-67` - Embedding generation
- `backend/models/models.py:76-84` - MessageEmbedding with Vector

**Why Critical**: Core functionality. Errors break the entire app purpose.

## 🔴 Critical Path 3: Vector Search

```
User Query → RAGService → pgvector similarity → Results
                ↓
          Embedding
                ↓
          <=> operator
```

**Critical Files**:
- `backend/services/rag_service.py:108-145` - Search implementation
- `backend/db/database.py:18-25` - pgvector extension check

**Why Critical**: User-facing search. Must be fast and accurate.

## 🟡 Important Path 4: Image Processing

```
Telegram Images → ImageService → S3 Storage
                       ↓
                  OCR + CLIP
                       ↓
                  Embeddings
```

**Critical Files**:
- `backend/services/image_service.py:78-112` - OCR pipeline
- `backend/services/image_service.py:45-67` - S3 upload

**Why Important**: Enhances search but not core functionality.

## 🟡 Important Path 5: Rate Limiting & Caching

```
API Request → Redis Check → Continue or 429
                 ↓
            Cache Check → Hit or Generate
```

**Critical Files**:
- `backend/api/middleware/rate_limit.py` (TODO)
- `backend/utils/cache.py` (TODO)

**Why Important**: Prevents abuse and improves performance.

## Architecture Invariants

1. **Multi-tenancy**: Every query MUST filter by user_id
2. **Async everywhere**: No blocking I/O in request handlers
3. **Embedding dimension**: Always 3072 for text-embedding-3-large
4. **Error handling**: All services must log errors before raising
5. **Resource cleanup**: Telegram clients must be properly closed

## Testing Critical Paths

```bash
# Test auth flow
pytest backend/tests/test_auth.py::test_telegram_verification -v

# Test embedding pipeline
pytest backend/tests/test_services.py::test_embedding_generation -v

# Test vector search
pytest backend/tests/test_services.py::test_vector_search -v
```

## Monitoring Checklist

When modifying critical paths:
1. ✓ Add logging before and after
2. ✓ Add timing metrics
3. ✓ Test error cases
4. ✓ Check memory usage
5. ✓ Verify multi-tenant isolation