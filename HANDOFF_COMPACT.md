# Agent Handoff - START HERE

## Read Order 📚
1. README.md → overview
2. PRD.md → requirements
3. AGENT_GUIDELINES.md → git rules
4. ENVIRONMENT.md → deps/config
5. CRITICAL_PATHS.md → architecture
6. dev_log.md → recent history
7. SETUP_CHECKLIST.md → cloud status

## Context 📋
T2T2: Telegram→pgvector→RAG | FastAPI+React+PostgreSQL+Redis+S3
CWD: `/Users/colinaulds/Desktop/projects/T2T2/backend`

## Pre-flight ⚠️
```bash
cat backend/.env         # config
# TodoRead tool NOW!     # MANDATORY
git log --oneline -10    # history
```

## Workflow 🔄
1. Checkpoint: `git add . && git commit -m "checkpoint: starting <task>"`
2. After commit → dev_log.md: time+hash+what+why
3. TodoWrite → track progress

## Issues 🛠️
DB: Supabase:5432 | AWS: us-west-1 | Redis: token=password
Test: `cd backend && ./run_tests.sh`

## Recovery 🔴
`git log --oneline -20` → find stable → `git reset --hard <hash>`

## Rules ⭐
Commit q15min | Update dev_log per commit | Check todos | Uncertain→checkpoint

**FIRST: TodoRead tool**