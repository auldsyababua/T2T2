# Agent Guidelines

## Git Rules 🔄

### Commit When
- Model/schema change
- New endpoint/service/function
- Bug fix | Config update | Tests
- **MAX**: 15-20min | **ALWAYS**: Before task switch

### Format
```
<type>: <description>
```
Types: feat|fix|refactor|test|docs|config|chore

### Commands
```bash
git add . && git commit -m "type: desc"
git rev-parse HEAD      # get hash
git log --oneline -10   # history
git reset --hard <hash> # revert
```

### MANDATORY: Dev Log Update Per Commit
```bash
COMMIT_HASH=$(git rev-parse HEAD)
# Update dev_log.md with:
# - Time + hash[0:7] + what + why + issues
```

### Checkpoints
Before: refactoring|deps|schema|cloud config|errors

### Doc Refresh (q10 commits)
1. Update: HANDOFF|ENVIRONMENT|CRITICAL_PATHS if changed
2. Rotate: `python scripts/rotate_dev_log.py` if >500 lines
3. Verify: Check file refs exist

### Recovery
```bash
git status && git diff
git log --oneline -20
git branch backup-$(date +%Y%m%d)
git reset --hard <good_hash>
```

### Integration
- Commit before marking todo complete
- Use: `git commit -m "feat: implement X (todo #N)"`

**Remember: Commit early, commit often, commit with clear messages**