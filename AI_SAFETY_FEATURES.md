# 🛡️ AI Safety Features Available in T2T2

Your project now has powerful safety features through the ai-agent-handoff MCP package!

## Quick Commands

### 🏥 Check Project Health
```bash
npx mcp health
```
Shows a visual dashboard of your project's status - no technical knowledge needed!

### 🔍 Check Code Quality
```bash
npx mcp check            # Check all files
npx mcp check backend/   # Check specific folder
```

### 🔧 Auto-Fix Issues
```bash
npx mcp fix-all         # Fix linting issues
npx mcp fix-common      # Fix common AI mistakes
```

### 💾 Safety Snapshots
```bash
npx mcp snapshot "before big change"   # Create backup
npx mcp rollback-last                  # Undo recent changes
```

### 🚨 Recovery After Problems
```bash
npx mcp recovery        # Show all recovery options
```

## Pre-Commit Safety

Add this to your `.git/hooks/pre-commit`:
```bash
#!/bin/bash
npx mcp pre-commit
```

Now bad code can't be committed!

## For AI Agents

Tell your AI agent:
- "Run `npx mcp health` before starting work"
- "Run `npx mcp check` after making changes"
- "Create a snapshot with `npx mcp snapshot` before risky operations"

## Common Scenarios

### Scenario 1: AI Broke Something
```bash
# Don't panic!
npx mcp rollback-last
# Everything is back to how it was
```

### Scenario 2: Code Won't Run
```bash
npx mcp fix-common      # Fixes most issues
npx mcp health          # See what's still wrong
```

### Scenario 3: AI Made Messy Code
```bash
npx mcp fix-all         # Auto-formats and fixes
npx mcp check           # See remaining issues
```

## Remember

- **These tools work automatically** - you don't need to understand how
- **Always create snapshots** before big changes
- **Report issues** instead of trying to fix the tools
- **Trust the safety features** - they're designed for non-coders!

## Getting Help

```bash
npx mcp help            # See all commands
npx mcp-report-issue    # Report a problem with the tools
```