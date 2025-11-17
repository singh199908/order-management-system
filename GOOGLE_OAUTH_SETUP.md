# Google OAuth Setup Guide

This guide will help you set up OAuth authentication for Google Drive/Sheets integration. OAuth allows the app to create files directly in your Google Drive using your storage quota.

## Why OAuth Instead of Service Account?

- **Service accounts** have limited storage quotas and cannot own files
- **OAuth** uses your personal Google account storage (2 TB for most accounts)
- Files created via OAuth are owned by you, not a service account

## Step 1: Create OAuth Credentials in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one)
3. Navigate to **APIs & Services** > **Credentials**
4. Click **+ CREATE CREDENTIALS** > **OAuth client ID**
5. If prompted, configure the OAuth consent screen:
   - Choose **External** (unless you have Google Workspace)
   - Fill in the required fields:
     - App name: `Order Management System`
     - User support email: Your email
     - Developer contact: Your email
   - Click **Save and Continue**
   - Add scopes (if needed):
     - `https://www.googleapis.com/auth/spreadsheets`
     - `https://www.googleapis.com/auth/drive`
   - Click **Save and Continue**
   - Add test users (your email) if app is in testing mode
   - Click **Save and Continue**
6. Back in Credentials, select **Web application** as the application type
7. Configure:
   - **Name**: `Order Management System OAuth`
   - **Authorized redirect URIs**: 
     - For local: `http://localhost:5000/oauth2callback`
     - For production: `https://your-domain.com/oauth2callback`
8. Click **Create**
9. **Copy the Client ID and Client Secret** - you'll need these!

## Step 2: Set Environment Variables

Add these to your `.env` file:

```bash
GOOGLE_OAUTH_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret-here
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:5000/oauth2callback
```

For production (Render), set these in your environment variables:
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `GOOGLE_OAUTH_REDIRECT_URI` (use your production URL)

## Step 3: Authorize the Application

1. Start your Flask application
2. Log in as admin
3. Navigate to the admin dashboard
4. Go to `/admin/google/authorize` (or add a button in the admin dashboard)
5. You'll be redirected to Google to authorize the app
6. Grant the requested permissions
7. You'll be redirected back to the app
8. The OAuth token will be saved automatically

## Step 4: Verify It's Working

1. Place a test order
2. Check the logs - you should see "Google OAuth credentials loaded successfully"
3. The Google Sheet should be created in your Drive folder
4. Check your Google Drive - the sheet should appear!

## Troubleshooting

### "OAuth libraries not installed"
```bash
pip install google-auth-oauthlib google-auth-httplib2
```

### "Invalid redirect URI"
- Make sure the redirect URI in your `.env` matches exactly what you configured in Google Cloud Console
- For local: `http://localhost:5000/oauth2callback`
- For production: `https://your-domain.com/oauth2callback`

### "Access blocked: This app's request is invalid"
- Make sure you added your email as a test user in the OAuth consent screen
- Or publish your app (if you want it available to all users)

### Token expires
- The app automatically refreshes tokens when they expire
- If refresh fails, re-authorize by visiting `/admin/google/authorize` again

## Notes

- OAuth tokens are stored securely in the database
- Tokens are automatically refreshed when expired
- You can revoke access at any time in [Google Account Settings](https://myaccount.google.com/permissions)
- OAuth takes precedence over service account if both are configured

