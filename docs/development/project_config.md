# Project Configuration

## Project Overview
- **Name**: T2T2 (Text-to-Text-to-Telegram)
- **Type**: Full-stack web application with Telegram bot integration
- **Purpose**: AI-powered chat application that processes user messages through various AI models and returns responses via Telegram

## Architecture
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **Bot**: Python Telegram Bot
- **Deployment**: Vercel (Frontend), Local/Docker (Backend)

## Key Components
1. **UI** - React frontend for chat interface and QR login
2. **Backend** - FastAPI server handling authentication, RAG, and database operations
3. **Bot** - Telegram bot for message relay and user interaction
4. **Database** - Supabase for user data, messages, and authentication

## Development Rules
1. **Code Style**
   - Follow existing patterns in codebase
   - Use TypeScript for frontend, Python for backend
   - Maintain consistent naming conventions
   - No comments unless explicitly requested

2. **File Operations**
   - Always prefer editing existing files over creating new ones
   - Never create documentation files unless explicitly requested
   - Read before editing to understand conventions
   - Use exact file paths (absolute, not relative)

3. **Testing**
   - Run lint/typecheck after changes: `npm run lint`, `npm run typecheck`
   - Test backend with existing test suite
   - Verify changes don't break existing functionality

4. **Security**
   - Never expose API keys or secrets
   - Follow existing security patterns
   - Use environment variables for sensitive data

## Workflow Automation Rules
1. **State Management**
   - Use `workflow_state.md` for dynamic task tracking
   - Maintain clear phase transitions: ANALYZE → BLUEPRINT → CONSTRUCT → VALIDATE
   - Update state after each significant action

2. **Parallel Tasks**
   - Create separate state files for concurrent work: `workflow_state_[taskname].md`
   - Avoid conflicts by isolating task contexts

3. **Persistence**
   - Always verify file writes actually occur
   - Check logs for confirmation of updates
   - Maintain changelog in workflow state

## Environment Setup
- Python 3.8+ for backend and bot
- Node.js 18+ for frontend
- Supabase project with proper RLS policies
- Telegram Bot Token and credentials
- MCP (Model Context Protocol) integration available

## Critical Paths
- Authentication flow: QR code → Telegram → Backend → Frontend
- Message processing: User → Frontend → Backend → AI → Telegram → User
- Database operations: Always through Supabase client with RLS

## Prohibited Actions
- Creating files without explicit request
- Adding comments to code
- Creating README or documentation files proactively
- Committing changes without explicit request
- Exposing secrets or API keys