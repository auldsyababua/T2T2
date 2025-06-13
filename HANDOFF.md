# T2T2 Project Handoff Document

## 🤖 AI Agent: START HERE

1. **Read `workflow_state.md`** - This drives your autonomous workflow
2. **Read `project_config.md`** - Project rules and configuration
3. **Check current phase** in workflow_state.md and act accordingly

## Project Overview
T2T2 (Text-to-Text-to-Telegram) is an AI-powered chat application that processes user messages through various AI models and returns responses via Telegram.

## Current Architecture
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI (Python) with Supabase, RAG, embeddings
- **Bot**: Python Telegram Bot for message relay
- **Database**: Supabase (PostgreSQL with pgvector)

## Workflow System
This project uses an autonomous workflow system:
- `project_config.md` - Stable configuration and rules
- `workflow_state.md` - Dynamic task tracking and loop control
- For parallel tasks: Create `workflow_state_[taskname].md`

## Current State
- ✅ Backend connected to Supabase at http://localhost:8000
- ✅ Frontend restored and running at http://localhost:5173
- ✅ Core RAG implementation complete
- ✅ QR authentication ready
- 📋 Ready for end-to-end testing

## Active Development
Check `workflow_state.md` for current task and phase.

## Key Commands
- Backend: `cd backend && uvicorn main:app --reload`
- Frontend: `cd UI && npm run dev`
- Tests: `cd backend && python -m pytest`
- Linting: `cd backend && black . && ruff check .`

## Git Practices
- Commit after each logical unit of work
- Use descriptive commit messages with prefixes (feat:, fix:, etc.)
- Update `workflow_state.md` after significant progress
- Check `dev_log.md` for detailed session history