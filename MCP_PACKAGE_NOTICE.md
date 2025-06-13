# ⚠️ IMPORTANT: MCP Package Notice

## DO NOT MODIFY ai-agent-handoff LOCALLY

The `@modelcontextprotocol/mcp` package is **npm linked** from the main ai-agent-handoff repository.

### If You Find Issues:

1. **Report them upstream:**
   ```bash
   npx mcp-report-issue
   ```

2. **Describe the problem** in HANDOFF.md or dev_log.md

3. **Tag it for human review:**
   ```markdown
   ## MCP Issue Found
   - Script: [script name]
   - Problem: [description]
   - Suggested fix: [your suggestion]
   ```

### Why This Matters

- This package is shared across multiple projects
- Local changes will be lost
- Fixes should benefit all projects, not just T2T2

### For Urgent Issues

If you absolutely must proceed:
1. Document the issue clearly
2. Work around it if possible
3. Alert the human maintainer ASAP

Remember: Good agents report issues, they don't create local divergence! 🤖