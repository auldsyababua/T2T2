For each new session, please leave a time and date as well as notes from that session, including what was changed and why. Optimize it for use by an LLM to continue working where the last session left off.

---

## 2025-06-11 17:30 PST - Initial Project Setup & Architecture

### What Was Done:
1. **Git Setup**: Initialized repo with remote origin `git@github.com:auldsyababua/T2T2.git`
2. **Project Structure**: Created backend (FastAPI) and existing frontend (React) structure
3. **Database Models**: Set up SQLAlchemy models with pgvector support for embeddings
4. **API Routes**: Created auth, telegram, query, and timeline endpoints
5. **Docker**: Added docker-compose.yml for local development

### Architecture Decisions:
- **Cloud-First Approach**: All services in cloud for easier user onboarding
  - Database: Supabase (pgvector support, free tier)
  - Cache: Upstash Redis (serverless)
  - Embeddings: OpenAI text-embedding-3-large
  - Storage: AWS S3 for images
- **Security**: JWT auth with Telegram Mini App HMAC verification
- **Multi-tenant**: One bot serves all users with RLS data isolation

### Current State:
- Backend structure complete but missing service implementations
- Need cloud credentials for: Supabase, Upstash, AWS S3
- Frontend exists but needs connection to backend

### Next Steps:
1. User needs to set up cloud services (see SETUP_CHECKLIST.md)
2. Implement TelegramService for Telethon QR auth
3. Implement RAGService for embeddings and search
4. Connect frontend to backend API 