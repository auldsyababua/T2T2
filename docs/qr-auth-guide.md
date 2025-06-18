# T2T2 QR Authentication Guide

## Overview
QR authentication allows users to authenticate with Telegram without sharing passwords or codes. Users simply scan a QR code with their Telegram app.

## How It Works

1. **User requests authentication** - `/auth` command in bot
2. **Bot generates secure link** - Unique session ID + GitHub Pages URL
3. **User clicks link** - Opens QR auth page (hosted on GitHub Pages)
4. **Backend generates QR code** - Using Telegram's QR login API
5. **User scans with Telegram** - Settings → Devices → Scan QR Code
6. **Authentication completes** - Session saved, no passwords shared!

## Setup Instructions

### 1. Install Dependencies
```bash
./install_qr_deps.sh
```

### 2. Start the QR Auth Server
```bash
python t2t2_qr_auth.py
```
This runs on http://localhost:5000

### 3. Start the Chat Indexer Bot
```bash
python t2t2_chat_indexer.py
```

### 4. Test Authentication
- Send `/auth` to the bot
- Click the link
- Scan QR code with Telegram

## Architecture

```
User → Bot → GitHub Pages → QR Server → Telegram API
         ↓                       ↓
    Session Link            QR Code
         ↓                       ↓
    GitHub Pages ← CORS → QR Server
```

### Components:

1. **GitHub Pages Frontend** (`docs/qr-auth.html`)
   - Static HTML page
   - Shows QR code and instructions
   - Works offline (shows manual auth option)

2. **QR Auth Server** (`t2t2_qr_auth.py`)
   - Generates QR codes
   - Handles Telegram authentication
   - Saves sessions to Supabase

3. **Chat Indexer Bot** (`t2t2_chat_indexer.py`)
   - Generates auth links
   - Points to GitHub Pages

## Security Features

- **30-second expiration** - QR codes expire quickly
- **Unique sessions** - Each auth attempt has unique ID
- **No password sharing** - Uses Telegram's native QR login
- **CORS enabled** - Only allows requests from your GitHub Pages
- **HTTPS frontend** - GitHub Pages provides SSL

## Deployment Options

### Local Development
- QR server runs on localhost:5000
- Frontend on GitHub Pages
- Works for testing

### Production Deployment
Options for the QR server:
1. **Railway/Render** - Deploy QR server to cloud
2. **VPS** - Run on your own server
3. **Ngrok** - Temporary public URL for localhost

Update the bot's server URL:
```python
server_url = "https://your-server.com"  # Replace localhost:5000
```

## Troubleshooting

### "Authentication server is offline"
- Ensure QR server is running: `python t2t2_qr_auth.py`
- Check server URL in bot matches actual server

### "QR code expired"
- QR codes expire after 30 seconds
- User needs to get a new link

### CORS errors
- Make sure flask-cors is installed
- Server must be running when user clicks link

### Can't scan QR code
- Telegram: Settings → Devices → Scan QR Code
- Must use Telegram mobile app (not desktop)

## Manual Authentication Fallback

If QR auth isn't working:
1. User clicks "authenticate manually"
2. Shows their User ID
3. Admin uses `admin_auth_tool.py`
4. No passwords shared in Telegram!

## Future Enhancements

1. **Deploy QR server** to cloud for 24/7 availability
2. **Add WebSocket** for real-time auth status
3. **Multiple auth methods** - QR, link, manual
4. **Session management** - View/revoke sessions