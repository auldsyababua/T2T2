# Telegram Mini App Authentication Debug Handoff

## Current Issue
The Telegram Mini App is failing authentication with "Invalid authentication data" error. The backend is receiving a 401 response when trying to authenticate users.

## What We've Done So Far

### 1. Fixed Bot Configuration
- Removed incorrect `?user_id=` parameter from WebApp URL in bot.py
- Updated bot to use correct WebApp URL: `https://t2t2-app.vercel.app`
- Fixed user authorization to support both username and user ID checks

### 2. Fixed Backend Issues
- Converted all relative imports to absolute imports throughout the backend
- Fixed CORS configuration to allow Vercel domains
- Added explicit support for `X-Telegram-Init-Data` header in CORS

### 3. Added Comprehensive Logging
- Added detailed error handling in `verify_telegram_webapp_data` function
- Added header logging to see what's being received
- Created test endpoints to debug header transmission

### 4. Frontend Updates
- Fixed frontend to not send undefined `X-Telegram-Init-Data` header
- Added null checks before sending authentication headers
- Added test call to debug endpoint before authentication

## Current Code State

### Key Files Modified:
1. `/backend/utils/telegram_auth.py` - Added error logging and null checks
2. `/backend/api/routes/auth.py` - Added detailed header logging
3. `/backend/main.py` - Added test endpoints for debugging
4. `/UI/src/lib/api.ts` - Fixed header handling

### Test Endpoints Added:
- `GET /test-logging` - Verifies logging is working
- `POST /test-auth-headers` - Shows what headers are received

## Next Steps to Debug

1. **Check Railway Logs**
   - Look for `[TEST]`, `[AUTH]`, or `[TEST-AUTH]` prefixed messages
   - These will show what headers are being received

2. **Verify Telegram WebApp Data**
   - Open browser console in Mini App
   - Check if `window.Telegram.WebApp.initData` has a value
   - Look for console logs starting with `[API]`

3. **Test Header Transmission**
   - The frontend now calls `/test-auth-headers` before authentication
   - This will show exactly what headers the backend receives

## Possible Root Causes

1. **Header Stripping**: Railway or a proxy might be stripping the `X-Telegram-Init-Data` header
2. **Timing Issue**: The Telegram WebApp script might not be fully loaded when we try to access `initData`
3. **Domain Mismatch**: The bot might be configured with a different domain in BotFather
4. **HTTPS/Security**: Telegram might not be providing initData due to security restrictions

## How to Test

1. Open the Mini App from Telegram
2. Open browser developer tools (if possible)
3. Look for network requests to `/test-auth-headers`
4. Check the response to see what headers were received
5. Check Railway logs for print statements

## Environment Variables Needed

Backend (Railway):
- `TELEGRAM_BOT_TOKEN`
- `JWT_SECRET_KEY`
- `DATABASE_URL`
- `LOG_LEVEL=DEBUG` (for verbose logging)

Frontend (Vercel):
- `VITE_API_URL=https://t2t2-production.up.railway.app`

## Recent Commits

1. `cfd30d7` - Added test endpoint to debug header issues
2. `71e66bf` - Added direct stdout logging for Railway debugging
3. `90a7478` - Added comprehensive error handling and logging
4. `0cb2c92` - Removed Railway token from documentation (security fix)

## Contact for Help

If you need to continue debugging:
1. Check Railway logs for the new debug output
2. Share the output from `/test-auth-headers` endpoint
3. Check browser console for `[API]` prefixed logs
4. Verify `window.Telegram.WebApp.initData` has a value in the Mini App

The core issue appears to be that the `X-Telegram-Init-Data` header is either not being sent or is being stripped before reaching the backend authentication handler.