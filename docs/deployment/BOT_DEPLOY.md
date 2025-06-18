# Telegram Bot Deployment Guide

## Deploy Bot as Railway Service

### 1. Create New Service in Railwaywh

1. In your Railway project dashboard
2. Click **"+ New"** → **"Empty Service"**
3. Name it "telegram-bot"

### 2. Configure the Service

1. Go to **Settings** tab
2. Under **Deploy**, set:
   - **Start Command**: `python bot.py`
   - **Restart Policy**: ON_FAILURE
   - **Health Check**: None (bot doesn't need HTTP health checks)

### 3. Add Environment Variables

1. Go to **Variables** tab
2. Click **"RAW Editor"** → **"JSON"**
3. Paste this:

```json
{
  "TELEGRAM_BOT_TOKEN": "8165476295:AAFyLp4vqtHwFngH5MYDn5eOd2DdibHFGLo",
  "WEBAPP_URL": "https://t2t2.vercel.app",
  "BACKEND_URL": "https://t2t2-production.up.railway.app",
  "LOG_LEVEL": "INFO"
}
```

4. Click **"Update Variables"**

### 4. Connect GitHub Repository

1. Go to **Settings** → **Source**
2. Connect to same GitHub repo (T2T2)
3. Set **Root Directory**: `/` (same as backend)
4. Railway will auto-deploy

### 5. Verify Bot is Running

1. Check logs in Railway dashboard
2. Message @talk2telegrambot on Telegram
3. Type `/start` - should see Mini App button
4. Click button - should open Vercel frontend

## Notes

- Bot runs as a "worker" service (no public URL needed)
- Uses polling mode to receive Telegram updates
- Shares same codebase as backend but runs independently
- Only authorized users (@colin_10NetZero, @Joel_10NetZero) can use it
