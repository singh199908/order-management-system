# Render OAuth Setup Checklist

## Your Render App
**URL:** `https://order-management-system-q40k.onrender.com`

## Step 1: Verify Render Environment Variables

Go to: https://dashboard.render.com → Your Service → Environment

**Check these are set correctly:**

1. **GOOGLE_OAUTH_CLIENT_ID**
   - Should be: your OAuth client ID

2. **GOOGLE_OAUTH_CLIENT_SECRET**
   - Should be: your OAuth client secret

3. **GOOGLE_OAUTH_REDIRECT_URI**
   - Should be: `https://order-management-system-q40k.onrender.com/oauth2callback`
   - **MUST match exactly** (no trailing slash)

4. **GOOGLE_DRIVE_FOLDER_ID**
   - Should be: `1SWKqTRDRaRMRhyH9RJL25xTr1Y1C_HBu`
   - **NOT** `1NRjuJn3nvggU4tEcmUMTiw94EWzCMrBUv_HBu` (old/wrong one)

5. **SECRET_KEY** (required for sessions)

## Step 2: Add Redirect URI to Google Cloud Console

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", add:
   ```
   https://order-management-system-q40k.onrender.com/oauth2callback
   ```
4. Click "SAVE"

## Step 3: Authorize OAuth on Render

1. Visit: https://order-management-system-q40k.onrender.com
2. Log in: `rtc` / `rtc1336`
3. Visit: https://order-management-system-q40k.onrender.com/admin/google/authorize
4. Click "Allow" on Google
5. Should see: "Google OAuth authorization successful!"

## Step 4: Check Render Logs

1. Go to Render Dashboard → Your Service → "Logs"
2. Place a test order
3. Look for:
   - "Google OAuth credentials loaded successfully" ✅ (good - using OAuth)
   - "Using Google Drive folder ID: 1SWKqTRDRaRMRhyH9RJL25xTr1Y1C_HBu" ✅ (correct folder)
   - "Successfully created sheet in folder" ✅ (success!)

## Common Issues

### ❌ Still using service account?
- Check logs for: "Loading Google credentials from GOOGLE_SERVICE_ACCOUNT_JSON"
- **Fix:** Authorize OAuth on Render (Step 3)

### ❌ Wrong folder ID?
- Check logs for: "Using Google Drive folder ID: 1NRjuJn3nvggU4tEcmUMTiw94EWzCMrBUv_HBu"
- **Fix:** Update `GOOGLE_DRIVE_FOLDER_ID` in Render environment variables to `1SWKqTRDRaRMRhyH9RJL25xTr1Y1C_HBu`

### ❌ redirect_uri_mismatch?
- **Fix:** Add redirect URI to Google Cloud Console (Step 2)

### ❌ Quota error?
- **Fix:** Make sure OAuth is authorized (not service account)

## Quick Test

After setup:
1. Place a test order on Render
2. Check your Google Drive folder: `1SWKqTRDRaRMRhyH9RJL25xTr1Y1C_HBu`
3. Sheet should appear!

