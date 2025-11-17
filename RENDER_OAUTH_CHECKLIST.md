# OAuth Authorization Checklist for Render

## Your Render App URL
**Production URL:** `https://order-management-system-q40k.onrender.com`

## Step-by-Step OAuth Setup

### Step 1: Verify Environment Variables in Render

Go to Render Dashboard → Your Service → Environment and verify:

```
GOOGLE_OAUTH_CLIENT_ID=your-oauth-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=https://order-management-system-q40k.onrender.com/oauth2callback
GOOGLE_DRIVE_FOLDER_ID=your-folder-id
```

**Important:** The redirect URI must be EXACTLY:
```
https://order-management-system-q40k.onrender.com/oauth2callback
```
- No trailing slash
- Use `https://` not `http://`
- Correct subdomain (`q40k`)

### Step 2: Add Redirect URI to Google Cloud Console

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click on your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", click "+ ADD URI"
4. Add EXACTLY this (copy-paste to avoid typos):
   ```
   https://order-management-system-q40k.onrender.com/oauth2callback
   ```
5. Click "SAVE"

### Step 3: Check Render Logs for Redirect URI

1. Go to Render Dashboard → Your Service → "Logs" tab
2. Try to authorize: Visit `https://order-management-system-q40k.onrender.com/admin/google/authorize`
3. Look in logs for: "OAuth redirect URI being used: ..."
4. Verify it matches what you added in Google Cloud Console

### Step 4: Authorize the App

1. Log in to your Render app: https://order-management-system-q40k.onrender.com
2. Use admin credentials: `rtc` / `rtc1336`
3. Visit: https://order-management-system-q40k.onrender.com/admin/google/authorize
4. You should be redirected to Google
5. Click "Allow" to grant permissions
6. You'll be redirected back with a success message

### Step 5: Test Google Sheets Creation

1. Place a test order
2. Check your Google Drive folder
3. The sheet should appear in your configured folder

## Troubleshooting

### Still getting redirect_uri_mismatch?

1. **Check Render logs** - Look for "OAuth redirect URI being used:"
2. **Verify in Google Cloud Console** - Make sure the URI is listed exactly as shown in logs
3. **Check for typos** - Common mistakes:
   - Trailing slash: `/oauth2callback/` ❌
   - Wrong protocol: `http://` instead of `https://` ❌
   - Wrong subdomain: missing `-q40k` ❌

### Can't access Google Cloud Console?

- Try different browser
- Clear cache and cookies
- Sign in with correct Google account
- Try incognito/private mode

## Quick Test

After setup, test the health endpoint:
```
https://order-management-system-q40k.onrender.com/health
```

Should return: `{"status": "ok", "message": "Server is running"}`

