# Railway Deployment Issues & Solutions

## Issues Found

### 1. Wrong Commit Hash (4a28a72)
The deployment is using an old commit that doesn't exist in recent history. This suggests Railway is either:
- Deploying from the wrong branch
- Has cached an old deployment

### 2. Unwanted `function-bun` Service
Railway automatically created a Bun runtime service because it detected the `supabase/functions/` directory. This is unnecessary and consumes resources.

### 3. Health Check Failure
The T2T2 service is failing health checks, likely due to missing environment variables.

## Solutions Applied

### 1. Code Updates
- ✅ Fixed health endpoint response (now returns "healthy" instead of "ok")
- ✅ Updated `.railwayignore` to explicitly exclude Supabase functions
- ✅ Removed dead code and unused imports
- ✅ Verified all required Python dependencies are in `requirements.txt`

### 2. Branch Updates
- ✅ Merged all fixes from `cleanup/remove-dead-code` to `refactor/tdlib-chat-history`
- ✅ Pushed updates to GitHub

## Actions Needed in Railway Dashboard

### 1. Delete the `function-bun` Service
1. Click on the `function-bun` service
2. Go to Settings
3. Scroll to bottom and click "Delete Service"
4. Confirm deletion

### 2. Fix T2T2 Service Configuration

#### A. Update Deployment Branch
1. Click on T2T2 service
2. Go to Settings → Source
3. **Current**: Appears to be deploying from `main` (commit 4a28a72)
4. **Change to**: `refactor/tdlib-chat-history` (latest: 5155c97)

#### B. Verify Environment Variables
Go to Settings → Variables and ensure ALL of these are set:
- `TELEGRAM_API_ID` - Number (e.g., 23585726)
- `TELEGRAM_API_HASH` - 32-char hex string
- `TELEGRAM_BOT_TOKEN` - Format: 1234567890:ABC...
- `SUPABASE_URL` - https://xxxx.supabase.co
- `SUPABASE_SERVICE_KEY` - JWT token (eyJ...)

### 3. Redeploy
After fixing the above:
1. Click "Redeploy" on the latest deployment
2. Or trigger new deployment by clicking "Deploy"

## Expected Success Indicators

When working correctly:
1. Build completes without errors
2. Health check passes (green checkmark)
3. No `function-bun` service appears
4. Logs show: "Starting T2T2 QR Auth Server on port XXXX"
5. `/health` endpoint returns: `{"status": "healthy", "service": "T2T2 QR Auth"}`

## Quick Test

Once deployed, test the service:
```bash
curl https://t2t2-production.up.railway.app/health
```

Should return:
```json
{"status": "healthy", "service": "T2T2 QR Auth"}
```

## If Still Failing

Check the deployment logs for:
- Missing module errors → Check requirements.txt
- "SUPABASE_URL not set" → Add environment variables
- Port binding errors → Should use PORT env var
- Import errors → Should not import from 'backend' module