# Setting Up OAuth for Local Development

## Problem
Your local app is using the service account, which can't create files in regular Google Drive folders. You need to use OAuth instead.

## Solution: Authorize OAuth Locally

### Step 1: Update Local .env File

Make sure your `.env` file has:

```env
GOOGLE_OAUTH_CLIENT_ID=your-oauth-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:5000/oauth2callback
GOOGLE_DRIVE_FOLDER_ID=your-folder-id
```

**Important:** 
- For local development, use `http://localhost:5000/oauth2callback` (not https)
- Use your correct folder ID

### Step 2: Add Localhost Redirect URI to Google Cloud Console

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", add:
   ```
   http://localhost:5000/oauth2callback
   ```
4. Click "SAVE"

### Step 3: Authorize OAuth Locally

1. Start your local server: `python app.py`
2. Log in as admin: `rtc` / `rtc1336`
3. Visit: http://localhost:5000/admin/google/authorize
4. You'll be redirected to Google
5. Click "Allow" to grant permissions
6. You'll be redirected back with a success message

### Step 4: Test

1. Place a test order
2. Check your Google Drive folder
3. The sheet should appear in the correct folder!

## Why OAuth Instead of Service Account?

- **Service Account**: Can't own files, limited to Shared Drives
- **OAuth**: Uses your personal Google account, can create files anywhere you have access

## For Production (Render)

On Render, use:
```
GOOGLE_OAUTH_REDIRECT_URI=https://order-management-system-q40k.onrender.com/oauth2callback
```

And make sure that URI is also added to Google Cloud Console.

