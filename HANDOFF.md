# Agent Handoff Document - START HERE

**This is the master handoff document for AI agents working on the T2T2 project.**

## Required Reading Order

Before starting ANY work, read these documents in order:

1. **README.md** - Project overview and quick start
2. **PRD.md** - Product requirements and technical decisions
3. **AGENT_GUIDELINES.md** - Git checkpointing and development practices
4. **dev_log.md** - Recent development history and current state
5. **SETUP_CHECKLIST.md** - Cloud services setup status

## Quick Context

- **Project**: T2T2 (Talk2Telegram 2) - Telegram chat history semantic search
- **Stack**: FastAPI backend, React frontend, PostgreSQL + pgvector, Redis, S3
- **Current Working Directory**: Should be `/Users/colinaulds/Desktop/projects/T2T2/backend`

## Critical Files to Check

```bash
# Check environment configuration
cat backend/.env

# Check todo list immediately
# Use TodoRead tool - DO NOT skip this step

# Check recent git history
git log --oneline -10
```

## Before You Start Coding

1. **Read the todo list** using the TodoRead tool
2. **Check git status**: `git status`
3. **Review recent commits**: `git log --oneline -10`
4. **Identify where we left off** from dev_log.md

## Development Workflow

1. **Start with a git checkpoint**:
   ```bash
   git add .
   git commit -m "checkpoint: starting session - <your task>"
   ```

2. **After EVERY commit**, update dev_log.md with:
   - Timestamp
   - Commit hash
   - What was done
   - Why it was done
   - Any issues encountered

3. **Use the TodoWrite tool** to track your progress

## Common Issues & Solutions

### Database Connection
- Using Supabase with direct connection (port 5432, not pooler)
- pgvector extension must be enabled
- Check `backend/.env` for DATABASE_URL

### Service Credentials
- All in `backend/.env`
- AWS S3 is in us-west-1 (not us-east-2)
- Upstash token = password

### Testing
```bash
cd backend
./run_tests.sh
```

## Emergency Recovery

If things go wrong:
1. Check this handoff document
2. Review recent commits: `git log --oneline -20`
3. Find last stable commit in dev_log.md
4. Consider reverting: `git reset --hard <commit>`

## Remember

- **Commit every 15-20 minutes**
- **Update dev_log.md after each commit**
- **Use descriptive commit messages**
- **Check todos frequently**
- **When in doubt, create a checkpoint**

---

**Your first command should be to use the TodoRead tool to see current tasks.**