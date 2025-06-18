# T2T2 Team Bot Setup Guide

This bot provides a private, encrypted Telegram interface for your team to query their chat history using AI.

## Features

- **Admin Control**: As admin, you control who can access the bot
- **Complete Privacy**: Each user's data is encrypted and isolated
- **Supabase Vector Storage**: Scalable cloud-based vector search
- **Bot Memory**: The bot remembers all conversations for better context
- **No User Setup**: Team members don't need Supabase accounts

## Setup Instructions

### 1. Get Your Telegram User ID

Send `/start` to [@userinfobot](https://t.me/userinfobot) on Telegram to get your user ID.

### 2. Get Supabase Service Key

1. Go to your Supabase project dashboard
2. Navigate to Settings → API
3. Copy the `service_role` key (NOT the `anon` key)
4. This key has full database access - keep it secure!

### 3. Setup Supabase Database

1. Open your Supabase project's SQL editor
2. Run the entire contents of `supabase_setup.sql`
3. This creates the required tables and functions

### 4. Configure Environment

1. Copy `.env.supabase_bot` to `.env`
2. Fill in:
   - `SUPABASE_SERVICE_KEY`: Your service role key from step 2
   - `ADMIN_TELEGRAM_ID`: Your Telegram user ID from step 1
   - Leave `TEAM_ENCRYPTION_KEY` empty - it will auto-generate

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the Bot

```bash
python supabase_team_bot.py
```

The bot will:
- Generate an encryption key (save it from the logs!)
- Start listening for commands
- Create an empty `authorized_users.enc` file

## Admin Commands

- `/admin` - Show admin menu
- `/add_user <telegram_id or @username>` - Authorize a user
- `/remove_user <telegram_id or @username>` - Remove authorization
- `/list_users` - Show all authorized users
- `/user_stats` - View usage statistics (coming soon)
- `/broadcast <message>` - Message all users (coming soon)

## User Commands

- `/start` - Initialize and show help
- `/index` - Instructions for indexing Telegram history
- `/memory` - Show what the bot remembers about you
- Just send a message to query your indexed data

## How It Works

1. **Authorization**: Admin adds users by Telegram ID or username
2. **First Contact**: When user messages bot, their ID is saved
3. **Data Isolation**: Each user gets a unique encrypted collection
4. **Vector Storage**: Messages are embedded and stored in Supabase
5. **RAG Queries**: User questions search their isolated vector store
6. **Encryption**: All data is encrypted with team-wide key

## Security Features

- End-to-end encryption of all user data
- Isolated vector collections per user
- Encrypted local storage of authorized users
- Service role key never exposed to users
- User IDs hashed for privacy

## Adding Team Members

1. Get their Telegram username or have them get their ID
2. Run `/add_user @theirusername` or `/add_user their_id`
3. Tell them to message the bot
4. They're ready to use it!

## Important Notes

- Keep your service role key secure
- Save the encryption key from first run
- Regular backups of `authorized_users.enc` recommended
- Each user's data is completely isolated
- Bot conversations are indexed for better memory

## Troubleshooting

**Bot doesn't respond**: 
- Check if user is authorized with `/list_users`
- Verify all environment variables are set
- Check bot token is correct

**Vector search errors**:
- Ensure Supabase SQL setup was run
- Check service key has proper permissions
- Verify Supabase URL is correct

**User can't access bot**:
- Confirm they're added with `/list_users`
- Have them send `/start` to initialize
- Check if using username vs ID consistently