# Railway Deployment Checklist

## Current Deployment Status
- **Project**: Talk2Telegram  
- **Service**: T2T2
- **URL**: https://t2t2-production.up.railway.app
- **Latest Deployment**: In Progress (started a few minutes ago)

## ✅ Verified Working Locally
1. **Python Dependencies**: All modules install and import correctly
2. **Environment Variables**: All required vars present in .env.supabase_bot
3. **Port Binding**: Correctly uses PORT env var and binds to 0.0.0.0
4. **No Conflicts**: No package.json or deno.json files present

## 🔍 Check in Railway Dashboard

### 1. Environment Variables
Go to Settings → Variables and ensure these are set:
- `TELEGRAM_API_ID` - Should be a number (e.g., 23585726)
- `TELEGRAM_API_HASH` - 32-character hex string
- `TELEGRAM_BOT_TOKEN` - Format: 1234567890:ABCdef...
- `SUPABASE_URL` - Format: https://xxxx.supabase.co
- `SUPABASE_SERVICE_KEY` - Long JWT token starting with eyJ...

### 2. Build Logs
Check the Deployments tab for the latest deployment:
- Look for "Successfully built" message
- Check for any pip install errors
- Ensure Python 3.11+ is being used

### 3. Common Issues to Look For

#### Missing Dependencies
If you see `ModuleNotFoundError`:
```bash
# Already in requirements.txt, but double-check:
flask==3.0.0
flask-cors==4.0.0
telethon==1.34.0
python-dotenv==1.0.0
qrcode==7.4.2
Pillow==10.2.0
supabase>=2.0.0
nest-asyncio==1.5.8
python-json-logger==2.0.7
```

#### Port Binding Error
If health check fails, ensure:
- Service is using PORT environment variable
- Server starts with message like "Running on http://0.0.0.0:XXXX"

#### Import Errors
If you see import errors for `backend` module:
- The t2t2_qr_auth.py doesn't use backend imports
- Check if .railwayignore is causing issues

## 🚀 Quick Fixes

### If Environment Variables Are Missing
1. Go to Settings → Variables
2. Add missing variables
3. Redeploy by clicking "Redeploy" on the latest deployment

### If Build Fails
1. Check Python version (should be 3.11+)
2. Ensure requirements.txt is in root directory
3. Check for syntax errors in Python files

### If Health Check Fails
1. Check that `/health` endpoint returns 200 OK
2. Verify server starts on correct port
3. Check runtime logs for startup errors

## 📊 Monitoring Commands

Once deployment succeeds, you can monitor with:
```bash
# Check service status
./scratch/railway-cli-wrapper.sh status

# Deploy updates
./scratch/railway-cli-wrapper.sh up --service T2T2 --detach
```

## 🔗 Important URLs
- **Railway Dashboard**: https://railway.app
- **Project Direct Link**: https://railway.com/project/93cb60dc-7655-4583-99ae-f503cf6f9433
- **Service URL**: https://t2t2-production.up.railway.app

## ✨ Success Indicators
When deployment is successful:
1. Health check passes (green checkmark in Railway)
2. `/health` endpoint returns: `{"status": "healthy", "service": "T2T2 QR Auth"}`
3. QR code generation works at `/qr/<session_id>`
4. Bot can send users to auth URL