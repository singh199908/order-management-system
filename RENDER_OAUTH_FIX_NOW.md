# Fix OAuth on Render - Step by Step

## Your Render App
**URL:** `https://order-management-system-q40k.onrender.com`

## The Problem
You're getting `redirect_uri_mismatch` because the redirect URI isn't added to Google Cloud Console.

## The Fix (3 Steps)

### Step 1: Add Redirect URI to Google Cloud Console

1. **Go to Google Cloud Console:**
   - Visit: https://console.cloud.google.com/apis/credentials
   - Sign in with your Google account

2. **Click your OAuth 2.0 Client ID:**
   - Find your OAuth client
   - Click on it

3. **Add the Render Redirect URI:**
   - Scroll to "Authorized redirect URIs"
   - Click "+ ADD URI"
   - Paste EXACTLY this (copy-paste to avoid typos):
     ```
     https://order-management-system-q40k.onrender.com/oauth2callback
     ```
   - **Important:** No trailing slash, exact match
   - Click "SAVE"

### Step 2: Verify Render Environment Variables

1. **Go to Render Dashboard:**
   - Visit: https://dashboard.render.com
   - Click your `order-management-system` service
   - Go to "Environment" tab

2. **Check these variables are set:**
   ```
   GOOGLE_OAUTH_CLIENT_ID=your-oauth-client-id.apps.googleusercontent.com
   GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-your-client-secret
   GOOGLE_OAUTH_REDIRECT_URI=https://order-management-system-q40k.onrender.com/oauth2callback
   GOOGLE_DRIVE_FOLDER_ID=your-folder-id
   ```

3. **If any are missing or wrong:**
   - Click "Add Environment Variable" or edit existing
   - Set the exact values above
   - Click "Save Changes"
   - Render will auto-redeploy

### Step 3: Authorize OAuth on Render

1. **Log in to your Render app:**
   - Visit: https://order-management-system-q40k.onrender.com
   - Log in with admin: `rtc` / `rtc1336`

2. **Authorize Google OAuth:**
   - Visit: https://order-management-system-q40k.onrender.com/admin/google/authorize
   - You'll be redirected to Google
   - Click "Allow" to grant permissions
   - You'll be redirected back with a success message

3. **Test:**
   - Place a test order
   - Check your Google Drive folder
   - The sheet should appear!

## Quick Checklist

- [ ] Added `https://order-management-system-q40k.onrender.com/oauth2callback` to Google Cloud Console
- [ ] Verified all 4 environment variables are set in Render
- [ ] Redeployed (if you changed environment variables)
- [ ] Authorized OAuth on Render (`/admin/google/authorize`)
- [ ] Tested by placing an order

## Common Mistakes

❌ **Wrong redirect URI:**
- `https://order-management-system-q40k.onrender.com/oauth2callback/` (trailing slash)
- `http://order-management-system-q40k.onrender.com/oauth2callback` (http instead of https)
- `https://order-management-system.onrender.com/oauth2callback` (wrong subdomain)

✅ **Correct redirect URI:**
- `https://order-management-system-q40k.onrender.com/oauth2callback` (exact match)

## Still Not Working?

Check Render logs:
1. Go to Render Dashboard → Your Service → "Logs"
2. Look for: "OAuth redirect URI being used: ..."
3. Make sure that exact URI is in Google Cloud Console

