# Google Sheets Setup Guide

This guide will help you set up Google Sheets integration to send order data via WhatsApp.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - **Google Sheets API**
   - **Google Drive API**

## Step 2: Create a Service Account

1. In Google Cloud Console, go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **Service Account**
3. Fill in the details:
   - **Service account name**: `order-management-system` (or any name you prefer)
   - **Service account ID**: Will be auto-generated
   - Click **Create and Continue**
4. Skip the optional steps and click **Done**

## Step 3: Create and Download Service Account Key

1. Click on the service account you just created
2. Go to the **Keys** tab
3. Click **Add Key** > **Create new key**
4. Select **JSON** format
5. Click **Create** - this will download a JSON file
6. **Save this file** as `credentials.json` in your `order_management_system` folder

## Step 4: Share a Google Drive Folder (Optional but Recommended)

1. Create a folder in Google Drive for your order sheets
2. Right-click the folder > **Share**
3. Add the service account email (found in the JSON file as `client_email`)
4. Give it **Editor** access
5. Click **Share**

## Step 5: Enable Google Sheets in the App

1. Place the `credentials.json` file in your `order_management_system` folder
2. Set environment variable or update `app.py`:
   ```python
   app.config['GOOGLE_SHEETS_ENABLED'] = True
   app.config['GOOGLE_SHEETS_CREDENTIALS_FILE'] = 'credentials.json'
   ```

Or set environment variables:
```bash
export GOOGLE_SHEETS_ENABLED=true
export GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
```

## Step 6: Install Required Packages

```bash
pip install -r requirements.txt
```

This will install:
- `gspread` - Google Sheets API client
- `google-auth` - Google authentication
- `google-auth-oauthlib` - OAuth support
- `google-auth-httplib2` - HTTP transport

## How It Works

When an order is placed:
1. The system creates a new Google Sheet with the order data
2. The sheet is automatically shared as "Anyone with the link can view"
3. A WhatsApp message is sent with the Google Sheets link
4. You can view, edit, and download the order data from Google Sheets

## Troubleshooting

### Error: "Credentials file not found"
- Make sure `credentials.json` is in the `order_management_system` folder
- Check the file path in your configuration

### Error: "Permission denied"
- Make sure the service account has access to Google Sheets and Drive APIs
- Check that the APIs are enabled in Google Cloud Console

### Error: "Invalid credentials"
- Re-download the JSON key file
- Make sure the service account email has proper permissions

## Security Note

**IMPORTANT**: Never commit `credentials.json` to version control!
- Add it to `.gitignore`
- Keep it secure and private
- If exposed, delete the service account and create a new one

