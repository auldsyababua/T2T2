# Workflow State

## Current Phase: CONSTRUCT

<!-- Phases: IDLE, ANALYZE, BLUEPRINT, CONSTRUCT, VALIDATE -->

## Active Task

**Task**: Comprehensive codebase analysis and documentation update
**Started**: 2025-06-13 17:40:00 PST
**Context**: Need to understand current project state, clarify architecture misunderstandings (no QR auth, Telegram Mini App only), and create better handoff documentation for future LLM instances.

## Next Action

Start implementing Phase 0 (Enhanced Data Model) to enable timeline support

## Rules for AI

1. **Read** this file at the start of each response
2. **Interpret** current phase and determine appropriate actions
3. **Execute** actions based on phase requirements
4. **Update** this file with new phase/progress
5. **Repeat** until task is complete

### Phase Definitions

- **ANALYZE**: Understand requirements, explore codebase, identify approach
- **BLUEPRINT**: Create detailed plan (requires user approval before proceeding)
- **CONSTRUCT**: Implement the solution following the blueprint
- **VALIDATE**: Test, verify, and ensure quality of implementation

## Task Progress

<!-- Update this section as you work -->

- [x] Set up autonomous workflow system
- [x] Remove ai-agent-handoff dependencies
- [x] Blueprint approved by user
- [x] Phase 0: Enhanced Data Model for chunks
- [x] Phase 1: Whitelist Authentication
- [x] Phase 2: Remove QR code
- [x] Phase 3: Deploy to Railway
- [ ] Phase 4: Test end-to-end

## Discoveries

<!-- Document important findings during ANALYZE phase -->

- Project uses Cursor-compatible autonomous workflow
- Parallel task support via separate state files
- .cursorrules enforces workflow compliance
- **T2T2 = Talk2Telegram 2** (second version, NOT Text-to-Text-to-Telegram)
- **Architecture Clarified**:
  - Telegram Mini App (Vercel): ONLY for chat selection/configuration
  - Telegram Bot: All Q&A and interaction happens here
  - NO QR auth needed - using Telegram handle whitelist instead
- **Authentication**: Hardcoded whitelist of handles (@colin_10NetZero, @Joel_10NetZero, etc.)
- **Multi-tenancy**: CRITICAL - each user can only query their own chats (RLS enforced)
- **Deployment Status**:
  - Frontend: ✅ Deployed on Vercel
  - Backend: ❌ Not deployed (Railway exists but empty)
  - Bot: ✅ Created (@talk2telegrambot)
  - Database: ✅ Supabase configured
  - Redis/S3: ✅ Configured in cloud
  - Railway: ✅ Account exists, ready for deployment

### New Technical Discoveries:

- **Vercel Backend**: NO - Vercel doesn't support persistent processes needed for FastAPI/WebSockets
- **Current Chunking**: 500 chars with 100 overlap (from PRD/embedding_service.py)
- **Current Data Model Issues**:
  - ❌ Timestamps not preserved in chunks (only in parent message)
  - ❌ Chat name not included in search results (only chat_id)
  - ❌ No timezone handling (uses UTC but should convert to GMT)
  - ✅ Message URLs are generated correctly: `https://t.me/c/{chat_id}/{msg_id}`

## Blueprint

<!-- Detailed implementation plan - requires user approval -->

### REVISED BASED ON USER FEEDBACK:

### Phase 0: Enhanced Data Model for Timeline Support

**Real-World Example of Chunking**:

```
[10:00] John: "Check pump 5 valve status"
[10:00] John: "Also need pressure readings"          ← Grouped with above
[10:01] Colin: "and so i told him he doesnt know"
[10:01] Colin: "what's really happening here"        ← Grouped with above
[10:01] Colin: [REPLY to John] "No haven't checked"  ← Separate chunk
[10:02] Colin: "but I'll do it after lunch"         ← New chunk (no reply ref)
[10:15] Sarah: "I checked it yesterday - all good"   ← Separate (too much time)

Results in 5 chunks:
1. John's combined request (valve + pressure)
2. Colin's story part 1
3. Colin's reply "No haven't checked" + context
4. Colin's "but I'll do it after lunch" (likely_answer_to: John's request)
5. Sarah's late response (likely_answer_to: John's request, 15 min delay noted)
```

1. **Update MessageEmbedding model** to include metadata:

   ```python
   class MessageEmbedding(Base):
       # ... existing fields ...
       chunk_metadata = Column(JSON)  # Store timestamp, chat_name, etc.
   ```

2. **Modify chunking to preserve metadata** in each chunk:

   ```json
   {
       "timestamp": "2025-01-13T15:30:00Z",  # GMT
       "chat_name": "10NetZero Team",
       "chat_id": -100123456,
       "msg_id": 789,
       "message_link": "https://t.me/c/-100123456/789",
       "sender_name": "Colin",
       "sender_username": "@colin_10NetZero",  # Added username
       "chunk_text": "yes",  # Even single word answers
       "original_text": "yes",  # Full message for reference
       "reply_to_msg_id": 788,  # If this was a reply
       "reply_to_text": "Did you replace the valve on pump 5?",  # Context
       "chunk_index": 0,
       "total_chunks": 1
   }
   ```

3. **Intelligent Message Grouping Strategy**:

   **Sequential Message Grouping Rules**:

   - Group consecutive messages from same user IF:
     - Sent within 2 minutes of each other
     - No replies interrupting the sequence
     - Combined length < 400 chars
     - Not replying to different messages

   **Breaking Conditions** (start new chunk when):

   - Different user sends a message
   - Current user replies to someone (even mid-story)
   - More than 2 minutes between messages
   - Combined length would exceed 400 chars
   - Message is a reply to a different thread

   **Example Handling**:

   ```
   Colin: "and so i told him he doesnt know what happening."
   Colin: "and he didnt like that very much"
   Colin: [REPLY to "did you change sparkplug?"] "No I didn't"  ← Separate chunk
   Colin: [REPLY to own M2] "but i dont really care if he doesnt like it."  ← Continue story
   ```

   **Result**:

   - Chunk 1: Colin's story part 1 (M1 + M2 combined)
   - Chunk 2: Colin's "No I didn't" with reply context
   - Chunk 3: Colin's story continuation (M4) with reference to M2

   **Metadata for Non-Reply Context**:

   - If no reply feature used but timing suggests response (< 30 seconds after question)
   - Add "likely_response_to" field with previous message reference
   - Example: "yes" sent 5 seconds after "Did you fix pump?" gets tagged

   **Additional Edge Cases**:

   1. **Implicit Q&A**: Question from User A → Answer from User B within 1 minute

      - Tag with "likely_answer_to" even without reply feature
      - Store both question and answer IDs in metadata

   2. **Search Optimization**:

      - Questions ending with "?" get tagged as "is_question": true
      - Short affirmative/negative responses get "is_answer": true
      - Both sides of Q&A pairs reference each other

   3. **Group Chat Handling**:

      - Track "conversation_thread_id" for related messages
      - Use combination of timing + user patterns + reply chains
      - If > 5 users active in 5 minutes, reduce grouping window to 30 seconds

   4. **Context Windows**:
      - Messages > 5 minutes apart are unlikely to be related
      - Exception: Direct replies always maintain relationship
      - Late replies get both timestamps: original question time + reply time

### Phase 1: Whitelist Authentication System

1. Create `backend/config/authorized_users.py` with whitelist:
   ```python
   AUTHORIZED_USERS = [
       "@colin_10NetZero",
       "@Joel_10NetZero",
       # Add more users here
   ]
   ```
2. Update `bot.py` to check whitelist on `/start` command
3. Update `backend/api/routes/auth.py` to verify against whitelist
4. Add proper error messages for unauthorized users

### Phase 2: Remove QR Authentication Code

1. Search and remove all QR-related code from:
   - `backend/services/telegram_service.py`
   - `backend/api/routes/telegram.py`
   - Frontend components (if any exist)
2. Update authentication flow to use Telegram handle only

### Phase 3: Backend Deployment on Railway

1. **Use existing Railway setup** (user already has one):
   - Configure environment variables from backend/.env
   - Deploy FastAPI backend as main service
   - Deploy bot.py as separate worker service
2. **Railway configuration**:
   - Main service: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Worker service: `python bot.py`
   - Both share same environment variables
3. **Environment variables to add**:
   - All from backend/.env (DATABASE_URL, OPENAI_API_KEY, etc.)
   - BACKEND_URL pointing to Railway backend URL
4. **Verify Supabase allows Railway IPs**

### Phase 4: Enhanced Project Documentation

1. Update `README.md` with correct project name and flow
2. Create `ARCHITECTURE.md` with:
   - Clear user flow diagram
   - Component relationships
   - Security boundaries
3. Create `DEPLOYMENT.md` with step-by-step instructions
4. Update `project_config.md` with discovered information

### Phase 5: Bot Integration & Timeline Testing

1. Ensure `bot.py` properly connects to backend API
2. Implement timeline-specific commands:
   - `/timeline [query]` - Generate chronological timeline
   - `/search [query]` - Regular RAG search
   - `/search [query] in [chat_name]` - Chat-specific search
3. Test complete flow with timeline generation
4. Verify chunk metadata is properly used
5. Add comprehensive logging for debugging

### Implementation Order:

1. **First**: Enhanced data model for chunks (enables timeline features)
2. **Second**: Whitelist auth (blocks unauthorized access)
3. **Third**: Remove QR code (cleanup)
4. **Fourth**: Backend deployment on Railway
5. **Fifth**: Bot integration with timeline commands
6. **Sixth**: Documentation updates

### Estimated Time: 4-5 hours total

### Key Design Decisions:

- **Backend**: Railway.app (supports FastAPI + background workers)
- **Chunking**: Smart grouping with context preservation
- **Metadata**: Each chunk stores full context for timeline generation
- **Auth**: Simple whitelist in code (no complex auth system needed)

### Post-Launch Testing Ideas:

- Automated conversation simulator using historical patterns
- A/B testing different chunking strategies
- Query success rate tracking
- User feedback on timeline accuracy

## Implementation Log

<!-- Track changes made during CONSTRUCT phase -->

- Created project_config.md with stable rules
- Created workflow_state.md for dynamic tracking
- Added workflow_state_template.md for parallel tasks
- Created .cursorrules for Cursor AI enforcement
- Removed ai-agent-handoff files and dependencies
- Updated HANDOFF.md to reference new system
- ✅ Phase 0 Complete:
  - Added chunk_metadata JSON column to MessageEmbedding model
  - Created SmartChunkingService with intelligent grouping logic
  - Rewritten EmbeddingService to use smart chunking
  - Created SQL migration for database update
- ✅ Phase 1 Complete:
  - Created authorized_users.py with whitelist
  - Updated bot.py with authorization checks
  - Added whitelist check to backend auth
  - Commands: /search and /timeline ready for future implementation
- ✅ Phase 2 Complete:
  - Removed QR login from telegram_service.py
  - Removed QR endpoints from API routes
  - Deleted QRLogin component from frontend
  - Removed qrcode dependency
- ✅ Phase 3 Complete:
  - Created Railway deployment configuration
  - Added Procfile, railway.json, railway.toml
  - Created comprehensive DEPLOY.md guide
  - Ready for deployment with provided token
- ✅ Phase 4 Complete:
  - Created root `vercel.json` → outputDirectory `UI/dist` & universal rewrite
  - Ready to deploy with `npx vercel --prod --confirm`

## Validation Results

<!-- Test results and verification during VALIDATE phase -->

- ✅ Workflow files created successfully
- ✅ ai-agent-handoff files removed
- ✅ Project cleaned of unused dependencies

## Changelog

<!-- Auto-updated by AI after each significant action -->

- [IDLE] Workflow state initialized, awaiting task
- [CONSTRUCT] Set up autonomous workflow system per Cursor guide
- [VALIDATE] Verified setup and cleaned project
- [IDLE] Setup complete, awaiting new task
- [ANALYZE] Started codebase analysis and gathered requirements
- [BLUEPRINT] Created comprehensive implementation plan for auth and deployment
- [BLUEPRINT] Revised chunking strategy based on real Telegram usage patterns
- [CONSTRUCT] User approved blueprint - starting implementation

## Summary Rules

1. Each log entry should be concise (1-2 lines max)
2. Use timestamps for significant milestones
3. Clear phase transitions with rationale
4. Rotate logs after 50 entries (move to `workflow_archive_[timestamp].md`)

## Error Handling

<!-- Document any blockers or issues -->

- No current errors

## Dependencies

<!-- Track external dependencies or waiting states -->

- None

## New Debugging Insights

- **Telegram initData issue**: Observed `platform: unknown` and empty `initData` → indicates the page is rendered **outside** a real Telegram Mini App context. `telegram-web-app.js` creates a fallback stub when launched in an external browser. Root suspects:
  1. Mini-App not fully enabled in @BotFather (`Configure Mini App` > `Enable Mini App`).
  2. Bot not providing a proper **launch button** (keyboard, inline, menu). Opening a bare URL does **not** pass init data.
  3. Domain mismatch – the domain set via `/setdomain` (or new `/setwebapp`) must exactly match `t2t2.vercel.app` (no scheme, path, or trailing slash; sub-domains matter).
  4. Using a **direct link** (`https://t.me/talk2telegrambot?startapp`) or a `web_app` keyboard button should be used for testing instead of pasting the Vercel URL.
  5. If you see `version: 6.0` & `platform: unknown`, you are definitely outside the Telegram client sandbox.
- **2025-06-17**: Troubleshooting Mini App auth
  - Verified BotFather Domain → set to `t2t2.vercel.app`
  - Menu button URL updated to `https://t2t2.vercel.app/`
  - Observed 404 `DEPLOYMENT_NOT_FOUND` → Vercel alias exists but no active deployment.
  - Ran `npm install` + `npm run build` inside `UI/` (build succeeded locally).
  - Need root-level `vercel.json` pointing to `UI/dist` and redeploy to Vercel.
  - Next step: create `vercel.json` at repo root and run `npx vercel --prod`.
  - Verified Mini App passes initData (iOS shows `Has InitData: true`)
  - Frontend error now: API URL https://t2t2-production.up.railway.app unreachable → authentication fails (no token)
  - Next task: deploy backend to Railway or update API_URL env var
- Fixed bug in telegram_auth.verify_telegram_webapp_data: incorrect locals() check prevented validation (changed 'hash' to 'received_hash'). Need backend redeploy.

---

<!-- DO NOT MODIFY BELOW THIS LINE -->

Last Updated: 2025-06-13 18:10:00 PST
Update Count: 4
