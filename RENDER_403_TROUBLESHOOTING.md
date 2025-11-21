# Fixing 403 Error on Render

## What 403 Error Means

A 403 error on Render usually means:
- The app hasn't deployed successfully
- The app crashed on startup
- There's a build error
- The app is still building (wait a few minutes)

## Step 1: Check Deployment Status

1. **Go to Render Dashboard:**
   - Visit https://dashboard.render.com
   - Click on your `order-management-system` service

2. **Check Status:**
   - Look at the top - should show "Live" (green) or "Building" (yellow)
   - If it shows "Failed" (red), there's an error

## Step 2: Check Build Logs

1. **Go to "Logs" Tab:**
   - Click "Logs" in your service dashboard
   - Look for error messages

2. **Common Build Errors:**
   - Missing dependencies
   - Python version mismatch
   - Import errors
   - Database connection errors

## Step 3: Check Runtime Logs

1. **Scroll to Runtime Logs:**
   - Look for errors after "Build successful"
   - Common errors:
     - `ModuleNotFoundError`
     - `ImportError`
     - Database connection failures
     - Missing environment variables

## Step 4: Verify Environment Variables

Make sure these are set in Render:

**Required:**
- `SECRET_KEY` - Must be set!

**For OAuth:**
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `GOOGLE_OAUTH_REDIRECT_URI` = `https://order-management-system-q40k.onrender.com/oauth2callback`

**For WhatsApp:**
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_FROM`
- `ADMIN_WHATSAPP_NUMBER`

**For Database (Recommended):**
- `DATABASE_URL` - PostgreSQL connection string

## Step 5: Common Fixes

### Fix 1: Missing SECRET_KEY
- **Error**: App crashes on startup
- **Fix**: Add `SECRET_KEY` environment variable in Render

### Fix 2: Database Connection Error
- **Error**: Can't connect to database
- **Fix**: 
  - If using PostgreSQL, verify `DATABASE_URL` is correct
  - If not using PostgreSQL, the app will use SQLite (should work)

### Fix 3: Import Errors
- **Error**: `ModuleNotFoundError: No module named 'X'`
- **Fix**: Check `requirements.txt` has all dependencies

### Fix 4: Port Issues
- **Error**: Port binding errors
- **Fix**: Render sets PORT automatically - don't override it

## Step 6: Manual Redeploy

If nothing works:

1. **Go to "Manual Deploy" Tab:**
   - Click "Manual Deploy"
   - Select "Deploy latest commit"
   - Wait for deployment to complete

2. **Or Clear Build Cache:**
   - Go to "Settings"
   - Scroll to "Clear build cache"
   - Click "Clear build cache"
   - Redeploy

## Step 7: Check Health Endpoint

Once deployed, test:
```
https://order-management-system-q40k.onrender.com/health
```

Should return:
```json
{"status": "ok", "message": "Server is running"}
```

## Quick Checklist

- [ ] Service status is "Live" (not "Failed" or "Building")
- [ ] Checked build logs for errors
- [ ] Checked runtime logs for errors
- [ ] `SECRET_KEY` is set
- [ ] All required environment variables are set
- [ ] Tried manual redeploy
- [ ] Health endpoint works

## Still Not Working?

Share the error messages from:
1. Build logs (if build failed)
2. Runtime logs (if app crashed)
3. Service status

Then I can help fix the specific issue!

