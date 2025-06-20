# MCP-Related Environment Variables by Project

This document contains all MCP-related environment variables found in `/Users/colinaulds/Desktop/projects/`, organized by project.

**Variable Patterns Included:**
- `OLLAMA*`
- `CLAUDE*`
- `ANTHROPIC*`
- `OPENAI*`
- `*_MCP_URL`
- `*_MCP_TOKEN`
- `*_MCP_AUTH_TOKEN`
- `GITHUB_TOKEN`
- `GITHUB_PAT`
- `N8N_*`
- `AI_RAILS_*`

---

## 10NZ_FLRTS

### backend/.env
- **OPENAI_API_KEY** = `***` (masked)

---

## ai-rails

### .env
- **AI_RAILS_SECRETS_MCP_AUTH_TOKEN** = `test...oken` (masked)
- **CODEBASE_SUMMARY_MCP_URL** = `http://10.0.0.2:8003`
- **OLLAMA_BASE_URL** = `http://10.0.0.2:11434`
- **SECRETS_MCP_URL** = `http...8004` (masked)

### .ai-rails/.env
- **AI_RAILS_SECRETS_MCP_AUTH_TOKEN** = `temp...e-me` (masked)
- **BRAVE_SEARCH_MCP_URL** = `http://10.0.0.2:8005`
- **CODEBASE_SUMMARY_MCP_URL** = `http://10.0.0.2:8003`
- **N8N_WEBHOOK_BASE_URL** = `http://10.0.0.2:5678/webhook/`
- **OLLAMA_BASE_URL** = `http://10.0.0.2:11434`
- **SECRETS_MCP_URL** = `http...8004` (masked)

---

## Daniel-reece-website

### .env
- **N8N_API_KEY** = `757c...2d75` (masked)
- **N8N_BASIC_AUTH_PASSWORD** = `e2a3...90e5` (masked)
- **N8N_BASIC_AUTH_USER** = `***` (masked)
- **N8N_BOOKING_WEBHOOK** = `https://executive-speech-coaching-n8n.up.railway.app/webhook/booking-created`
- **N8N_CALENDAR_WEBHOOK** = `https://executive-speech-coaching-n8n.up.railway.app/webhook/calendar-sync`
- **N8N_CONTACT_WEBHOOK** = `https://executive-speech-coaching-n8n.up.railway.app/webhook/contact-form`
- **N8N_ENCRYPTION_KEY** = `f518...0875` (masked)
- **N8N_ERROR_WEBHOOK** = `https://executive-speech-coaching-n8n.up.railway.app/webhook/error-notification`
- **N8N_HOST** = `https://executive-speech-coaching-n8n.up.railway.app`
- **N8N_PAYMENT_WEBHOOK** = `https://executive-speech-coaching-n8n.up.railway.app/webhook/payment-received`
- **N8N_WEBHOOK_TOKEN** = `26dd...2791` (masked)
- **N8N_WEBHOOK_URL** = `https://executive-speech-coaching-n8n.up.railway.app/webhook/`

---

## T2T2

### .env
- **OPENAI_API_KEY** = `sk-s...VuoA` (masked)

### backend/.env
- **OPENAI_API_KEY** = `sk-s...VuoA` (masked)

---

## raycast_mcp_config

### .mcp/.env
- **GITHUB_TOKEN** = `ghp_...7r2R` (masked)

---

## Deprecated Projects

### DR-Designs
#### .mcp/.env
- **GITHUB_TOKEN** = `ghp_...7r2R` (masked)

---

## Summary Statistics

- **Total Projects Scanned**: 27 .env files across multiple projects
- **Active Projects with MCP Variables**: 5
- **Most Common Variables**:
  - OPENAI_API_KEY (3 occurrences)
  - GITHUB_TOKEN (2 occurrences)
  - OLLAMA_BASE_URL (2 occurrences)
  - Various N8N_* variables (11 unique)
  - Various MCP_URL endpoints (5 unique)

## Notable Observations

1. **AI-Rails Project** has the most comprehensive MCP configuration with multiple service endpoints
2. **Daniel-reece-website** has extensive N8N webhook integration
3. **T2T2** and **10NZ_FLRTS** primarily use OpenAI integration
4. Several projects have dedicated `.mcp` directories for MCP-specific configuration
5. Most sensitive values (tokens, keys) are properly configured and in use