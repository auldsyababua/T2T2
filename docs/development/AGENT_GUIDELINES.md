# AI Agent Development Guidelines

## Git Checkpointing Requirements

**IMPORTANT**: All AI agents working on this codebase MUST follow these git checkpointing practices to maintain a clear history of changes and enable easy rollback if needed.

### Commit Frequency

1. **Commit after each logical unit of work**:
   - After creating/modifying a model or schema
   - After implementing a new API endpoint
   - After adding a new service or utility function
   - After fixing a bug or error
   - After updating configuration files
   - After adding tests

2. **Maximum time between commits**: 15-20 minutes of active development

3. **Before switching tasks**: Always commit current work with a clear message

### Commit Message Format

Use clear, descriptive commit messages following this pattern:

```
<type>: <description>

[optional body explaining why the change was made]
```

Types:
- `feat`: New feature implementation
- `fix`: Bug fix
- `refactor`: Code refactoring without changing functionality
- `test`: Adding or updating tests
- `docs`: Documentation updates
- `config`: Configuration changes
- `chore`: Maintenance tasks

Examples:
```bash
git commit -m "feat: implement telegram authentication service"
git commit -m "fix: resolve database connection timeout with direct connection"
git commit -m "test: add unit tests for RAG service embeddings"
```

### Essential Git Commands

```bash
# Check current status
git status

# Stage specific files
git add <file_path>

# Stage all changes
git add .

# Commit with message
git commit -m "type: description"

# Get the commit hash of the last commit
git rev-parse HEAD

# View recent commits
git log --oneline -10

# Create a checkpoint before major changes
git commit -m "checkpoint: before implementing <feature>"

# If something goes wrong, check the log
git log --oneline -20

# Revert to a previous commit if needed
git reset --hard <commit_hash>
```

### MANDATORY: Update Dev Log After Each Commit

**After EVERY commit, you MUST update dev_log.md with:**

1. Get the commit hash:
   ```bash
   COMMIT_HASH=$(git rev-parse HEAD)
   ```

2. Update dev_log.md with:
   - Current timestamp
   - Commit hash (first 7 characters)
   - What was changed
   - Why it was changed
   - Any issues or blockers

Example dev log entry:
```markdown
### 2025-06-11 19:30 PST - Commit: a1b2c3d
- Added validation to telegram authentication endpoint
- Fixed issue where expired tokens were causing 500 errors
- Next: Need to implement rate limiting
```

### When to Create Checkpoints

1. **Before major refactoring**: Create a checkpoint commit
2. **Before updating dependencies**: Commit current stable state
3. **Before modifying database schemas**: Ensure migrations are committed
4. **Before changing cloud service configurations**: Document current working state
5. **After getting something working**: Immediately commit the working state

### Working with Errors

When encountering errors:

1. **Don't panic**: Check `git status` to see what changed
2. **Review recent commits**: Use `git log --oneline -10` 
3. **Identify the breaking change**: Use `git diff` to see uncommitted changes
4. **Consider reverting**: If the error is complex, revert to last known good state
5. **Document the issue**: Commit with a message explaining what went wrong

### Collaboration Guidelines

1. **Pull before starting work**: Always start with the latest code
2. **Commit before switching agents**: Ensure clean handoff
3. **Document blockers**: If stuck, commit with a "WIP:" message explaining the issue
4. **Use descriptive branch names**: If creating branches, use `feature/description` format

### Example Workflow

```bash
# Start of session
git status
git pull origin main

# After creating a new service
git add services/telegram_service.py
git commit -m "feat: create telegram service with QR authentication"

# After fixing an error
git add db/database.py
git commit -m "fix: add pgvector extension check on startup"

# Before ending session
git status
git add .
git commit -m "checkpoint: end of session - <brief status>"
git push origin main
```

### Recovery Process

If development goes "off the rails":

1. Stop and assess:
   ```bash
   git status
   git diff
   git log --oneline -20
   ```

2. Find the last known good commit:
   ```bash
   git log --oneline --grep="checkpoint\|working\|stable"
   ```

3. Create a backup branch:
   ```bash
   git branch backup-<date>
   ```

4. Reset to good state:
   ```bash
   git reset --hard <good_commit_hash>
   ```

5. Document what went wrong in dev_log.md

## Integration with Todo System

- After completing a todo item, commit the changes before marking it complete
- Use todo item descriptions in commit messages for traceability
- Example: `git commit -m "feat: implement OCR for screenshots (todo #6)"`

## Documentation Refresh Protocol

Every 10 commits or at session end, run a documentation refresh:

1. **Update HANDOFF.md** if project structure changed
2. **Update ENVIRONMENT.md** if dependencies changed
3. **Update CRITICAL_PATHS.md** if architecture evolved
4. **Run dev log rotation** if dev_log.md > 500 lines:
   ```bash
   python scripts/rotate_dev_log.py
   ```

5. **Verify documentation accuracy**:
   ```bash
   # Check if all referenced files exist
   grep -oh '"[^"]*\.py:[0-9]*' CRITICAL_PATHS.md | while read f; do
     file=$(echo $f | tr -d '"' | cut -d: -f1)
     [ -f "backend/$file" ] && echo "✓ $file" || echo "✗ $file MISSING"
   done
   ```

## Remember

**Your commits are the project's safety net. Commit early, commit often, and commit with clear messages. This discipline will save hours of debugging and enable smooth collaboration between agents.**