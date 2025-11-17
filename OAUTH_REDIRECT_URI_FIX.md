# Fix OAuth Redirect URI Mismatch Error

## Error: `redirect_uri_mismatch`

This error means the redirect URI in your OAuth request doesn't match what's configured in Google Cloud Console.

## Solution: Update Google Cloud Console

### Step 1: Go to OAuth Client Settings

1. Visit: https://console.cloud.google.com/apis/credentials
2. Click on your OAuth 2.0 Client ID: `529145545514-a2kg4po7pr81gr5ns7g4819gpb45p20f`
3. You'll see "Authorized redirect URIs" section

### Step 2: Add Your Render Redirect URI

1. Under "Authorized redirect URIs", click **"+ ADD URI"**
2. Add this EXACT URL (no trailing slash):
   ```
   https://order-management-system-q40k.onrender.com/oauth2callback
   ```
3. Click **"SAVE"**

### Step 3: Verify in Render Environment Variables

1. Go to Render Dashboard: https://dashboard.render.com
2. Click your `order-management-system` service
3. Go to "Environment" tab
4. Check `GOOGLE_OAUTH_REDIRECT_URI` value:
   - Should be: `https://order-management-system-q40k.onrender.com/oauth2callback`
   - Must match EXACTLY (no trailing slash, correct domain)

### Step 4: Redeploy (if needed)

If you changed the environment variable:
1. Render will auto-redeploy
2. Or click "Manual Deploy" → "Deploy latest commit"

### Step 5: Try Authorization Again

1. Visit: https://order-management-system-q40k.onrender.com/admin/google/authorize
2. Should work now!

## Common Mistakes to Avoid

❌ **Wrong:**
- `https://order-management-system-q40k.onrender.com/oauth2callback/` (trailing slash)
- `http://order-management-system-q40k.onrender.com/oauth2callback` (http instead of https)
- `https://order-management-system.onrender.com/oauth2callback` (wrong subdomain)

✅ **Correct:**
- `https://order-management-system-q40k.onrender.com/oauth2callback` (exact match)

## Quick Checklist

- [ ] Added redirect URI in Google Cloud Console
- [ ] Verified `GOOGLE_OAUTH_REDIRECT_URI` in Render matches exactly
- [ ] No trailing slash
- [ ] Using `https://` not `http://`
- [ ] Correct subdomain (`q40k`)
- [ ] Redeployed if changed environment variable
- [ ] Tried authorization again

