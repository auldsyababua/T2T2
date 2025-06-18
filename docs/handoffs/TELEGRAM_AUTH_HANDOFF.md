# Telegram Mini App Authentication Debug Handoff

## Current Issue
The Telegram Mini App is failing authentication with "Invalid authentication data" error. The backend is receiving a 401 response when trying to authenticate users. The core issue appears to be that the `X-Telegram-Init-Data` header is either not being sent or is being stripped before reaching the backend authentication handler.

## What We've Done So Far

### 1. Fixed Bot Configuration
- Removed incorrect `?user_id=` parameter from WebApp URL in bot.py
- Updated bot to use correct WebApp URL: `https://t2t2-app.vercel.app`
- Fixed user authorization to support both username and user ID checks

### 2. Fixed Backend Issues
- Converted all relative imports to absolute imports throughout the backend
- Fixed CORS configuration to allow Vercel domains
- Added explicit support for `X-Telegram-Init-Data` header in CORS
- Added print statements with `flush=True` for Railway logging
- Created test endpoints to verify logging and header transmission

### 3. Added Comprehensive Logging
- Added detailed error handling in `verify_telegram_webapp_data` function
- Added header logging to see what's being received
- Created test endpoints to debug header transmission
- Added exception catching with detailed error messages
- Added logging for null/empty init_data cases

### 4. Frontend Updates
- Fixed frontend to not send undefined `X-Telegram-Init-Data` header
- Added null checks before sending authentication headers
- Added test call to debug endpoint before authentication
- Removed duplicate `tg.ready()` calls
- Enhanced debugging to show WebApp version, platform, and initDataUnsafe

## Current Code State

### Key Files Modified:
1. `/backend/utils/telegram_auth.py` - Added error logging and null checks
2. `/backend/api/routes/auth.py` - Added detailed header logging and print statements
3. `/backend/main.py` - Added test endpoints for debugging
4. `/UI/src/lib/api.ts` - Fixed header handling and added comprehensive debugging
5. `/UI/src/App.tsx` - Enhanced error messages with platform/version info

### Test Endpoints Added:
- `GET /test-logging` - Verifies logging is working
- `POST /test-auth-headers` - Shows what headers are received
- `GET /health` - Basic health check with logging

### Test Tools Created:
- `/test-auth.html` - Standalone HTML file to test authentication headers

## Next Steps to Debug

1. **Check Railway Logs**
   - Look for `[TEST]`, `[AUTH]`, `[TEST-AUTH]`, or `[HEALTH]` prefixed messages
   - These will show what headers are being received
   - Railway may only show certain log levels - print statements should work

2. **Verify Telegram WebApp Data in Browser Console**
   - Look for `[DEBUG]` prefixed messages showing:
     - Window hash and location
     - Telegram WebApp object
     - initData presence and length
     - initDataUnsafe object (parsed data)
     - WebApp version and platform
   - Look for `[API]` prefixed messages showing:
     - Whether Telegram WebApp is available
     - initData retrieval status
     - Any error details

3. **Test Header Transmission**
   - The frontend now calls `/test-auth-headers` before authentication
   - Check the Network tab for this request
   - The response will show exactly what headers the backend receives

4. **Manual Testing**
   - Open `/test-auth.html` in a browser
   - Click "Test Auth Headers" to see if custom headers reach the backend
   - This helps isolate if it's a Telegram-specific issue

## Debugging Information to Collect

When the Mini App shows the error, collect:
1. The full error message shown (includes version number)
2. Browser console output (all `[DEBUG]` and `[API]` messages)
3. Network tab response from `/test-auth-headers`
4. Railway logs showing any print statements

## Possible Root Causes

1. **Header Stripping**: Railway or a proxy might be stripping the `X-Telegram-Init-Data` header
2. **Timing Issue**: The Telegram WebApp script might not be fully loaded when we try to access `initData`
3. **Domain Mismatch**: The bot might be configured with a different domain in BotFather
4. **HTTPS/Security**: Telegram might not be providing initData due to security restrictions
5. **Platform Issues**: Different behavior on iOS vs Android vs Desktop

## How to Test

1. Open the Mini App from Telegram
2. Open browser developer tools (if possible on your platform)
3. Look for console logs with `[DEBUG]` and `[API]` prefixes
4. Check Network tab for:
   - `/test-auth-headers` request and response
   - `/api/auth/telegram-webapp-auth` request and response
5. Note the error message version (currently "5.00AM FIXED")

## Environment Variables Needed

Backend (Railway):
- `TELEGRAM_BOT_TOKEN`
- `JWT_SECRET_KEY`
- `DATABASE_URL`
- `LOG_LEVEL=DEBUG` (for verbose logging)

Frontend (Vercel):
- `VITE_API_URL=https://t2t2-production.up.railway.app`

## Recent Commits

1. `682f128` - Enhanced Telegram WebApp debugging
2. `cfd30d7` - Added test endpoint to debug header issues
3. `71e66bf` - Added direct stdout logging for Railway debugging
4. `90a7478` - Added comprehensive error handling and logging
5. `0cb2c92` - Removed Railway token from documentation (security fix)

## Critical Questions to Answer

1. Is `window.Telegram.WebApp.initData` populated when the app loads?
2. Does the `/test-auth-headers` endpoint show the `X-Telegram-Init-Data` header?
3. What does `initDataUnsafe` contain (this is the parsed version)?
4. What platform and WebApp version is shown in the logs?
5. Are there any CORS or network errors in the console?

## If Headers Are Being Stripped

If the `/test-auth-headers` endpoint doesn't show the `X-Telegram-Init-Data` header:
1. Try sending the data in the request body instead of headers
2. Try using a different header name (e.g., `Authorization: Telegram <data>`)
3. Consider using URL parameters or cookies as alternative methods
4. Check if Railway has any header size limits or filtering

The most likely issue is that Telegram is not providing initData to the WebApp, which could be due to domain configuration or how the Mini App is being opened.