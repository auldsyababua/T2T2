# T2T2 Admin-Assisted Authentication Guide

## Overview
This guide explains how to authenticate users for the T2T2 Chat Indexer using the admin-assisted approach, which avoids Telegram's code detection security feature.

## Why Admin-Assisted Authentication?
Telegram blocks authentication when it detects login codes being shared in chats (even with bots). This is a security feature to prevent phishing. Our workaround uses an admin tool that runs outside of Telegram.

## Setup

### 1. Add Required Tables
Run this SQL in your Supabase dashboard:
```bash
# Go to Supabase SQL Editor and run:
- add_user_sessions_table.sql (if not already done)
- add_pending_auth_table.sql
```

### 2. Start the Chat Indexer Bot
```bash
python t2t2_chat_indexer.py
```

You'll receive notifications when users request authentication.

## Authentication Flow

### User Side:
1. User sends `/start` to @talk2telegrambot
2. User sends `/auth` 
3. User enters phone number (e.g., +17138179392)
4. Bot creates pending authentication request
5. User receives code from Telegram
6. User contacts admin with the code (NOT via Telegram)

### Admin Side:
1. You receive notification in Telegram about new auth request
2. Run the admin tool:
   ```bash
   python admin_auth_tool.py
   ```
3. Enter the user's Telegram ID (shown in notification)
4. Confirm or enter their phone number
5. Tool sends verification code to user
6. User tells you the code via phone/text
7. Enter code in the tool
8. If user has 2FA enabled, they'll also need to provide their password
9. Authentication completes!

## Using the Admin Tool

### Starting the Tool
```bash
python admin_auth_tool.py
```

### Tool Interface
```
==================================================
T2T2 ADMIN AUTHENTICATION TOOL
==================================================

🔍 Checking pending authentications...

📋 Found 1 pending authentication(s):
1. User ID: 5751758169 - Phone: +17138179392
   Requested: 2025-06-18T18:30:00

👤 Enter Telegram User ID to authenticate: 5751758169
📱 Use saved phone number +17138179392? (y/n): y

🔄 Connecting to Telegram...
📤 Sending verification code...

✅ Code sent successfully!

⚠️  IMPORTANT:
1. The user should check their Telegram app for the code
2. They should call/text you the code (NOT send it in Telegram)
3. Enter the code below when you receive it

🔑 Enter the verification code: [USER TELLS YOU CODE]
```

### Testing the Authentication
After successful authentication, the tool offers to test by listing the user's chats:
```
🧪 Test the session by listing chats? (y/n): y

📋 User's chats:
👤 Saved Messages
👥 T2T2 Development Team
📢 Telegram News
...
```

## User Commands

After authentication, users can:
- `/chats` - Select which chats to index
- `/search <query>` - Search indexed messages
- `/status` - Check authentication and indexing status

## Troubleshooting

### "Invalid API key"
- Check `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` in `.env.supabase_bot`
- These come from https://my.telegram.org/apps

### "Table does not exist"
- Run the SQL files in Supabase SQL Editor
- Check table names match exactly

### "Code expired"
- Codes expire quickly if typed in Telegram
- Have user request new code
- Enter it immediately in admin tool

### "Two-steps verification is enabled"
- User has 2FA enabled on their account
- After entering the code, you'll be prompted for password
- User needs to provide their 2FA password
- For security, handle passwords carefully

### User Not Receiving Notifications
- Check user's Telegram ID is correct
- Ensure bot has permission to message them
- User must have started the bot first

## Security Notes

1. **Never** have users send codes in Telegram chats
2. Use secure channel (phone/Signal/etc) for code exchange
3. Session strings are encrypted and user-specific
4. Each user can only access their own chats

## Future Enhancement

For Phase 2, we'll implement:
- Web portal with one-time links
- Users enter codes in secure web form
- No manual admin intervention needed
- See `t2t2_web_auth.py` (already created)

## Common Workflow

1. User requests auth → You get notified
2. Run admin tool → Enter their ID
3. They get code → They call you
4. You enter code → Auth complete
5. They use `/chats` → Select chats
6. Indexing begins → They can search!

## Admin Tips

- Keep admin tool open during onboarding sessions
- Process multiple users in sequence
- Tool saves progress if interrupted
- Check `/status` to verify completion