# T2T2 Product Requirements Document

## Overview
Talk2Telegram 2 (T2T2) is a Telegram bot that enables semantic search and timeline generation over users' Telegram chat history using RAG (Retrieval-Augmented Generation).

## Core Features

### 1. Authentication
- Telegram Mini App with HMAC verification
- Desktop-only QR code authentication via Telethon
- JWT tokens for API access
- Multi-tenant: one bot serves all users privately

### 2. Chat Indexing
- User selects chats to index via Mini App
- Messages deduplicated by (chat_id, msg_id)
- Text chunked (500 chars, 100 overlap)
- Embeddings via OpenAI text-embedding-3-large
- Images: OCR with Tesseract, CLIP embeddings
- Progress tracking with real-time updates

### 3. Search & Query
- Natural language queries
- Returns AI-generated answers with citations
- Each citation links to original Telegram message
- Combines text and image search results

### 4. Timeline Generation
- Creates chronological event timelines from queries
- Returns JSON array sorted by timestamp
- Saves timelines for future reference
- Each item links to source message

## Technical Stack

### Backend
- FastAPI + Python 3.11
- PostgreSQL + pgvector (Supabase)
- Redis cache (Upstash)
- OpenAI embeddings
- AWS S3 for images
- Telethon for Telegram API

### Frontend
- React + TypeScript + Vite
- Shadcn UI components
- Tailwind CSS
- Telegram Mini App SDK

## API Endpoints

### Auth
- `POST /api/auth/telegram-auth` - Verify Telegram initData

### Telegram
- `POST /api/telegram/qr-login` - Generate QR for desktop auth
- `GET /api/telegram/chats` - List user's chats
- `POST /api/telegram/index-chats` - Start indexing selected chats
- `GET /api/telegram/indexing-status` - Check progress

### Query
- `POST /api/query/` - RAG query with AI answer
- `POST /api/query/similar` - Find similar messages

### Timeline
- `POST /api/timeline/` - Generate timeline from query
- `GET /api/timeline/saved` - List saved timelines
- `GET /api/timeline/{id}` - Get specific timeline

## Security
- Row-level security via PostgreSQL RLS
- User data isolated by tg_user_id
- HMAC verification for Telegram auth
- JWT tokens expire after 7 days
- All credentials in environment variables

## Cost Optimization
- Messages deduplicated across users
- Embeddings created once, shared by all
- Estimated: $0.26 per 50k messages (one-time)

## Success Metrics
- User can index 10k messages < 5 minutes
- Query response time < 2 seconds
- 95% accuracy in timeline generation
- Zero data leakage between users