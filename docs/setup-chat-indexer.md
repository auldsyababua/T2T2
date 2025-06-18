# T2T2 Chat Indexer Setup Guide

## Overview
The T2T2 Chat Indexer allows users to:
1. Authenticate with their Telegram phone number
2. Select which chats to index
3. Crawl ENTIRE chat histories (not just new messages)
4. Search across all indexed messages

## Prerequisites

✅ **Already Configured:**
- Telegram Bot Token
- Telegram API ID & Hash
- OpenAI API Key
- Supabase connection
- S3 bucket

❌ **Still Needed:**
- `user_sessions` table in Supabase

## Setup Steps

### 1. Add the user_sessions Table

**Option A: Via Supabase Dashboard (Recommended)**
1. Go to your [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Navigate to **SQL Editor**
4. Click **New Query**
5. Copy and paste the contents of `add_user_sessions_table.sql`
6. Click **Run**

**Option B: Via psql (if you have DATABASE_URL)**
```bash
psql $DATABASE_URL < add_user_sessions_table.sql
```

### 2. Test the Setup

Run the test script to verify everything is configured:

```bash
python test_chat_indexer.py
```

You should see all green checkmarks ✅

### 3. Start the Chat Indexer

```bash
python t2t2_chat_indexer.py
```

You'll see:
```
🚀 Starting T2T2 Chat Indexer...
✅ Chat indexer is running!
```

### 4. Use the Bot

In Telegram, message **@talk2telegrambot**:

1. **Start the bot:**
   ```
   /start
   ```
   You'll see a welcome message explaining the bot.

2. **Authenticate your account:**
   ```
   /auth
   ```
   - Enter your phone number with country code (e.g., +1234567890)
   - Enter the verification code you receive

3. **Select chats to index:**
   ```
   /chats
   ```
   - You'll see your top 20 chats
   - Tap chats to toggle selection (✅ = selected)
   - Click "📥 Start Indexing" when ready

4. **Search your messages:**
   ```
   /search your query here
   ```
   Example: `/search meeting notes`

## How It Works

1. **Authentication**: Uses Telethon with your phone number to access full chat history
2. **Chat Selection**: Shows your chats with inline keyboards for easy selection
3. **Indexing**: Crawls ALL messages from selected chats (may take time for large chats)
4. **Storage**: Messages are embedded and stored in Supabase with pgvector
5. **Search**: Uses semantic similarity search across all indexed messages

## Important Notes

- **Privacy**: Your session is encrypted and only you can search your messages
- **First Index**: Initial indexing can take a while for large chats
- **Updates**: Currently indexes once - future versions will sync new messages
- **Message Types**: Currently indexes text messages only (files handled by the other bot)

## Troubleshooting

**"user_sessions table missing"**
- Run the SQL in `add_user_sessions_table.sql` via Supabase dashboard

**"Invalid phone number"**
- Include country code with + (e.g., +1234567890)

**"Session expired"**
- Re-authenticate with `/auth`

**No search results**
- Ensure indexing completed (you'll get a notification)
- Try broader search terms

## Architecture

```
User → Bot Interface → Telethon Client → Telegram API
                ↓
         Chat Selection
                ↓
         Message Crawler
                ↓
         OpenAI Embeddings
                ↓
         Supabase pgvector
```

The indexer maintains:
- User sessions (encrypted Telethon sessions)
- Monitored chats list per user
- Message embeddings in telegram_files table
- Search functionality via similarity matching