# Fix redirect_uri_mismatch Error

## The Problem
Google is rejecting the OAuth request because the redirect URI in your app doesn't match what's in Google Cloud Console.

## The Solution: Add Exact Redirect URI to Google Cloud Console

### Step 1: Check What Redirect URI Your App Is Using

1. Go to Render Dashboard: https://dashboard.render.com
2. Click your `order-management-system` service
3. Go to "Logs" tab
4. Look for: "OAuth redirect URI being used: ..."
5. Copy that exact URI

OR use this exact URI (should be):
```
https://order-management-system-q40k.onrender.com/oauth2callback
```

### Step 2: Add to Google Cloud Console

1. **Go to Google Cloud Console:**
   - Visit: https://console.cloud.google.com/apis/credentials
   - Sign in with your Google account

2. **Click your OAuth 2.0 Client ID:**
   - Find your OAuth client
   - Click on it to edit

3. **Add the Redirect URI:**
   - Scroll to "Authorized redirect URIs" section
   - Click "+ ADD URI"
   - Paste EXACTLY this (copy-paste to avoid typos):
     ```
     https://order-management-system-q40k.onrender.com/oauth2callback
     ```
   - **CRITICAL:** Must match EXACTLY:
     - ✅ `https://` (not `http://`)
     - ✅ No trailing slash
     - ✅ Exact subdomain: `q40k`
     - ✅ Exact path: `/oauth2callback`

4. **Click "SAVE"**

### Step 3: Verify in Render

1. Go to Render Dashboard → Your Service → Environment
2. Check `GOOGLE_OAUTH_REDIRECT_URI`:
   - Should be: `https://order-management-system-q40k.onrender.com/oauth2callback`
   - Must match exactly what you added in Google Cloud Console

### Step 4: Wait and Try Again

1. **Wait 1-2 minutes** after saving in Google Cloud Console (Google needs time to update)
2. Try authorization again:
   - Visit: https://order-management-system-q40k.onrender.com/admin/google/authorize
   - Should work now!

## Common Mistakes

❌ **Wrong:**
- `https://order-management-system-q40k.onrender.com/oauth2callback/` (trailing slash)
- `http://order-management-system-q40k.onrender.com/oauth2callback` (http instead of https)
- `https://order-management-system.onrender.com/oauth2callback` (wrong subdomain - missing `-q40k`)
- `https://order-management-system-q40k.onrender.com/oauth2` (wrong path)

✅ **Correct:**
- `https://order-management-system-q40k.onrender.com/oauth2callback` (exact match)

## Still Not Working?

1. **Check Render logs** for the exact redirect URI being used
2. **Double-check Google Cloud Console** - make sure the URI is listed exactly as shown in logs
3. **Wait a few minutes** - Google sometimes takes time to update
4. **Try in incognito/private browser** - clear cache

## Quick Checklist

- [ ] Added redirect URI to Google Cloud Console
- [ ] URI matches exactly (no trailing slash, https, correct subdomain)
- [ ] Clicked "SAVE" in Google Cloud Console
- [ ] Verified `GOOGLE_OAUTH_REDIRECT_URI` in Render matches
- [ ] Waited 1-2 minutes after saving
- [ ] Tried authorization again

