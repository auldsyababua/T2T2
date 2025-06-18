# Frontend Environment Variable Update

## Update Vercel Frontend to Use Railway Backend

### 1. Go to Vercel Dashboard
1. Visit https://vercel.com/dashboard
2. Find your **t2t2-app** project
3. Click on it to open project settings

### 2. Update Environment Variables
1. Go to **Settings** → **Environment Variables**
2. Add or update:
   - **Variable Name**: `VITE_API_URL`
   - **Value**: `https://t2t2-production.up.railway.app`
   - **Environment**: Select all (Production, Preview, Development)
3. Click **Save**

### 3. Redeploy Frontend
1. Go to **Deployments** tab
2. Find the latest deployment
3. Click the **...** menu → **Redeploy**
4. Or trigger by pushing any change to your frontend repo

### 4. Verify Integration
1. Visit https://t2t2-app.vercel.app directly
   - Should show "Authentication Error" (expected)
2. Open from Telegram bot:
   - Message @talk2telegrambot
   - Click "Open App" button
   - Should authenticate properly

## Troubleshooting

If frontend can't connect to backend:
1. Check browser console for CORS errors
2. Verify Railway backend has correct CORS_ORIGINS
3. Ensure VITE_API_URL has no trailing slash