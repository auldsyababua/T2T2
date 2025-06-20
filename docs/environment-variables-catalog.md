# Environment Variables Catalog

This document catalogs all unique environment variables found across all projects in `/Users/colinaulds/Desktop/projects/`. Variables are grouped by service/purpose.

## API Keys & Authentication

### AI/LLM Services
- `ANTHROPIC_API_KEY` - Anthropic Claude API key
- `CLAUDE_API_KEY` - Claude API key (legacy naming)
- `OPENAI_API_KEY` - OpenAI API key
- `LANGCHAIN_API_KEY` - LangChain API key

### Search Services
- `BRAVE_API_KEY` - Brave Search API key
- `TAVILY_API_KEY` - Tavily Search API key

### Communication Services
- `TELEGRAM_API_HASH` - Telegram API hash
- `TELEGRAM_API_ID` - Telegram API ID
- `TELEGRAM_BOT_TOKEN` - Telegram bot token
- `TELEGRAM_BOT_NAME` - Telegram bot name
- `TELEGRAM_BOT_USERNAME` - Telegram bot username
- `TELEGRAM_SESSION_NAME` - Telegram session name

### Productivity Services
- `TODOIST_API_KEY` - Todoist API key
- `TODOIST_API_TOKEN` - Todoist API token (alternate naming)
- `CALCOM_API_KEY` - Cal.com API key
- `CAL_COM_API_KEY` - Cal.com API key (alternate naming)

### Google Services
- `GOOGLE_API_KEY` - Google API key
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `GOOGLE_REFRESH_TOKEN` - Google OAuth refresh token
- `GOOGLE_DRIVE_CLIENT_ID` - Google Drive specific client ID
- `GOOGLE_DRIVE_CLIENT_SECRET` - Google Drive specific client secret
- `GOOGLE_CALENDAR_ID` - Google Calendar ID
- `GOOGLE_SERVICE_ACCOUNT_JSON` - Google service account JSON
- `GOOGLE_ANALYTICS_ID` - Google Analytics ID
- `GOOGLE_TAG_MANAGER_ID` - Google Tag Manager ID
- `GOOGLE_BUSINESS_PROFILE_ID` - Google Business Profile ID
- `GOOGLE_SITE_VERIFICATION` - Google site verification code

### Database Services
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_PROJECT_URL` - Supabase project URL (alternate naming)
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_KEY` - Supabase service key
- `SUPABASE_ACCESS_TOKEN` - Supabase access token
- `SUPABASE_PROJECT_ID` - Supabase project ID
- `SUPABASE_READ_ONLY` - Supabase read-only flag

### Payment Services
- `STRIPE_PUBLISHABLE_KEY` - Stripe publishable key
- `STRIPE_SECRET_KEY` - Stripe secret key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret
- `STRIPE_PRICE_ENTERPRISE` - Stripe price ID for enterprise tier
- `STRIPE_PRICE_LAUNCH` - Stripe price ID for launch tier
- `STRIPE_PRICE_SCALE` - Stripe price ID for scale tier
- `STRIPE_PRICE_SESSION` - Stripe price ID for session
- `STRIPE_PRICE_STARTUP` - Stripe price ID for startup tier
- `STRIPE_PRICE_VENTURE` - Stripe price ID for venture tier
- `STRIPE_TAX_RATE_ID` - Stripe tax rate ID
- `STRIPE_INVOICE_PREFIX` - Stripe invoice prefix
- `STRIPE_PAYMENT_CAPTURE_DELAY_DAYS` - Stripe payment capture delay
- `STRIPE_CANCEL_URL` - Stripe cancel URL
- `STRIPE_SUCCESS_URL` - Stripe success URL

### SaaS Services
- `AIRTABLE_API_KEY` - Airtable API key
- `AIRTABLE_API_TOKEN` - Airtable API token (alternate naming)
- `AIRTABLE_BASE_ID` - Airtable base ID
- `NOLOCO_API_KEY` - Noloco API key
- `NOLOCO_API_URL` - Noloco API URL
- `VIMEO_API_KEY` - Vimeo API key
- `YOUTUBE_API_KEY` - YouTube API key

### AWS Services
- `AWS_ACCESS_KEY_ID` - AWS access key ID
- `AWS_SECRET_ACCESS_KEY` - AWS secret access key
- `AWS_REGION` - AWS region

### Development Services
- `GITHUB_TOKEN` - GitHub personal access token

## Database Configuration

### PostgreSQL
- `DATABASE_URL` - Database connection URL
- `POSTGRES_HOST` - PostgreSQL host
- `POSTGRES_PORT` - PostgreSQL port
- `POSTGRES_USER` - PostgreSQL username
- `POSTGRES_PASSWORD` - PostgreSQL password
- `POSTGRES_DB` - PostgreSQL database name
- `POSTGRES_URL` - PostgreSQL connection URL
- `DB_HOST` - Generic database host
- `DB_PORT` - Generic database port
- `DB_USER` - Generic database user
- `DB_PASSWORD` - Generic database password
- `DB_NAME` - Generic database name
- `DB_TYPE` - Database type
- `DB_POSTGRESDB_HOST` - PostgreSQL specific host
- `DB_POSTGRESDB_PORT` - PostgreSQL specific port
- `DB_POSTGRESDB_USER` - PostgreSQL specific user
- `DB_POSTGRESDB_PASSWORD` - PostgreSQL specific password
- `DB_POSTGRESDB_DATABASE` - PostgreSQL specific database

### Redis/Cache
- `REDIS_URL` - Redis connection URL
- `UPSTASH_REDIS_REST_URL` - Upstash Redis REST URL
- `UPSTASH_REDIS_REST_TOKEN` - Upstash Redis REST token
- `UPSTASH_REDIS_REST_PASSWORD` - Upstash Redis REST password

### Project-Specific Databases
- `SHELBY_DB_HOST` - Shelby project database host
- `SHELBY_DB_PORT` - Shelby project database port
- `SHELBY_DB_USER` - Shelby project database user
- `SHELBY_DB_PASSWORD` - Shelby project database password
- `SHELBY_DB_NAME` - Shelby project database name

## Application Configuration

### Environment & Debug
- `NODE_ENV` - Node.js environment (development/production)
- `ENVIRONMENT` - Generic environment variable
- `FLASK_ENV` - Flask environment
- `DEBUG` - Debug mode flag
- `LOG_LEVEL` - Logging level
- `LOG_FILE` - Log file path

### Security & Authentication
- `SECRET_KEY` - Application secret key
- `JWT_SECRET_KEY` - JWT secret key
- `JWT_ALGORITHM` - JWT algorithm
- `JWT_EXPIRE_DAYS` - JWT expiration in days
- `SESSION_SECRET` - Session secret
- `SESSION_ENCRYPTION_KEY` - Session encryption key
- `CSRF_TOKEN` - CSRF token
- `API_SECRET_KEY` - Generic API secret key
- `API_RATE_LIMIT_KEY` - API rate limiting key

### Server Configuration
- `CORS_ORIGINS` - CORS allowed origins
- `RATE_LIMIT_PER_MINUTE` - Rate limit per minute

### Email Configuration
- `SMTP_HOST` - SMTP server host
- `SMTP_PORT` - SMTP server port
- `SMTP_USER` - SMTP username
- `SMTP_PASS` - SMTP password
- `EMAIL_FROM` - From email address
- `ADMIN_EMAIL` - Admin email address
- `ADMIN_SMS` - Admin SMS number

## MCP (Model Context Protocol) Configuration

### MCP Server URLs
- `CODEBASE_SUMMARY_MCP_URL` - Codebase summary MCP URL
- `SECRETS_MCP_URL` - Secrets MCP URL
- `BRAVE_SEARCH_MCP_URL` - Brave search MCP URL
- `MCP_SEQUENTIAL_THINKING_URL` - Sequential thinking MCP URL

### MCP Configuration
- `MCP_SERVER_LOG_LEVEL` - MCP server log level
- `MCP_TIMEOUT` - MCP timeout
- `AI_RAILS_SECRETS_MCP_AUTH_TOKEN` - AI Rails MCP auth token
- `AI_RAILS_PROJECT_NAME` - AI Rails project name

## Business/Site Configuration

### Business Information
- `BUSINESS_NAME` - Business name
- `BUSINESS_EMAIL` - Business email
- `BUSINESS_PHONE` - Business phone
- `BUSINESS_ADDRESS` - Business address
- `WEBSITE_URL` - Website URL
- `SITE_NAME` - Site name
- `SITE_URL` - Site URL

### Business Hours
- `BUSINESS_HOURS_MONDAY` - Monday hours
- `BUSINESS_HOURS_TUESDAY` - Tuesday hours
- `BUSINESS_HOURS_WEDNESDAY` - Wednesday hours
- `BUSINESS_HOURS_THURSDAY` - Thursday hours
- `BUSINESS_HOURS_FRIDAY` - Friday hours
- `BUSINESS_HOURS_SATURDAY` - Saturday hours
- `BUSINESS_HOURS_SUNDAY` - Sunday hours

### Social Media
- `FACEBOOK_URL` - Facebook URL
- `INSTAGRAM_URL` - Instagram URL
- `LINKEDIN_URL` - LinkedIn URL
- `YOUTUBE_CHANNEL_URL` - YouTube channel URL
- `TWITTER_HANDLE` - Twitter handle

### SEO & Analytics
- `BING_SITE_VERIFICATION` - Bing site verification
- `ORGANIZATION_FOUNDER_NAME` - Organization founder name
- `ORGANIZATION_LOGO_URL` - Organization logo URL

## Feature-Specific Configuration

### Airtable Tables
- `AIRTABLE_CLIENTS_TABLE` - Clients table name
- `AIRTABLE_SESSIONS_TABLE` - Sessions table name
- `AIRTABLE_LEADS_TABLE` - Leads table name
- `AIRTABLE_FEEDBACK_TABLE` - Feedback table name
- `AIRTABLE_GOALS_TABLE` - Goals table name
- `AIRTABLE_INVOICES_TABLE` - Invoices table name
- `AIRTABLE_PROGRESS_REPORTS_TABLE` - Progress reports table name
- `AIRTABLE_REFERRALS_TABLE` - Referrals table name
- `AIRTABLE_SALES_TABLE` - Sales table name
- `AIRTABLE_AUTOMATION_LOG_TABLE` - Automation log table name
- `AIRTABLE_AUTOMATION_RULES_TABLE` - Automation rules table name
- `AIRTABLE_ZAPIER_LOG_TABLE` - Zapier log table name
- `AIRTABLE_CLIENT_PRIMARY_FIELD` - Client primary field
- `AIRTABLE_SESSION_PRIMARY_FIELD` - Session primary field
- `AIRTABLE_LOG_PRIMARY_FIELD` - Log primary field

### Cal.com Integration
- `CALCOM_DISCOVERY_CALL_ID` - Discovery call event type ID
- `CALCOM_PACKAGE_CONSULTATION_ID` - Package consultation event type ID
- `CALCOM_SESSION_ID` - Session event type ID

### UI/UX Configuration
- `FLOATING_CTA_TEXT` - Floating CTA text
- `FLOATING_CTA_URL` - Floating CTA URL
- `FLOATING_CTA_SCROLL_TRIGGER` - Floating CTA scroll trigger
- `MOBILE_FOOTER_BOOK_TEXT` - Mobile footer book text
- `MOBILE_FOOTER_BOOK_URL` - Mobile footer book URL
- `MOBILE_FOOTER_CALL_TEXT` - Mobile footer call text
- `MOBILE_FOOTER_PHONE` - Mobile footer phone
- `TRUST_COUNTER_NUMBER` - Trust counter number
- `TRUST_COUNTER_TEXT` - Trust counter text
- `TRUST_SHOW_URGENCY` - Trust urgency flag
- `TRUST_URGENCY_TEXT` - Trust urgency text
- `PACKAGE_CURRENCY_SYMBOL` - Package currency symbol
- `PACKAGE_MOST_POPULAR` - Most popular package
- `PACKAGE_SHOW_SAVINGS` - Show savings flag

### Ratings & Reviews
- `AGGREGATE_RATING_VALUE` - Aggregate rating value
- `AGGREGATE_RATING_COUNT` - Aggregate rating count

### AI/ML Configuration
- `OLLAMA_BASE_URL` - Ollama base URL
- `LLM_TIMEOUT` - LLM timeout
- `MAX_LLM_RETRIES` - Max LLM retries
- `EMBED_ENDPOINT` - Embedding endpoint
- `EMBEDDING_SERVICE_URL` - Embedding service URL

### Agent Configuration
- `AGENT_NAME` - Agent name
- `AGENT_SPECIALIZATION` - Agent specialization
- `ADMIN_TELEGRAM_USERNAMES` - Admin Telegram usernames
- `ADMIN_TELEGRAM_ID` - Admin Telegram ID
- `TARGET_CHAT_NAMES` - Target chat names

### Memory/Storage Configuration
- `MAX_MEMORY_AGE_DAYS` - Max memory age in days
- `MEMORY_IMPORTANCE_THRESHOLD` - Memory importance threshold

### Processing Configuration
- `BATCH_SIZE` - Batch size
- `CHUNK_SIZE_CHARS` - Chunk size in characters
- `FETCH_INTERVAL_MINUTES` - Fetch interval in minutes
- `PROCESS_INTERVAL_MINUTES` - Process interval in minutes
- `MAX_MESSAGES_PER_BATCH` - Max messages per batch

### Frontend Configuration
- `VITE_API_URL` - Vite API URL (for frontend builds)

### Timezone
- `GENERIC_TIMEZONE` - Generic timezone setting

## Notes

1. Some services use different naming conventions for the same API key (e.g., `TODOIST_API_KEY` vs `TODOIST_API_TOKEN`)
2. Many projects have both `.env` files and `.mcp/.env` files for MCP-specific configuration
3. Template files (`.env-template`, `.env.example`) help document required variables for each project
4. Database credentials often have multiple naming patterns depending on the project
5. Some variables like `DEBUG` and `LOG_LEVEL` are used across most projects

## Recommendations for Global MCP Environment

Based on this analysis, the following variables should be considered for the global MCP environment file:

### Essential API Keys (commonly used across projects)
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `BRAVE_API_KEY`
- `TAVILY_API_KEY`
- `GITHUB_TOKEN`
- `GOOGLE_API_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

### Common Service Keys
- `TELEGRAM_API_HASH`
- `TELEGRAM_API_ID`
- `TELEGRAM_BOT_TOKEN`
- `TODOIST_API_TOKEN`
- `AIRTABLE_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

### MCP-Specific
- `CODEBASE_SUMMARY_MCP_URL`
- `SECRETS_MCP_URL`
- `BRAVE_SEARCH_MCP_URL`
- `MCP_SEQUENTIAL_THINKING_URL`
- `AI_RAILS_SECRETS_MCP_AUTH_TOKEN`

### Development/Debug
- `LOG_LEVEL`
- `DEBUG`