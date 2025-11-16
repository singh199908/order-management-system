# Twilio Authentication Error Troubleshooting

## Error: "Authentication Error - invalid username" (401)

This error means your **Twilio Account SID** is incorrect or not set properly.

## Quick Fix Checklist

### 1. Verify Your Twilio Credentials

Your Twilio credentials should be:
- **Account SID**: Starts with `AC` (e.g., `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
- **Auth Token**: Long alphanumeric string (e.g., `your-auth-token-here`)

**Where to find them:**
1. Go to https://console.twilio.com
2. Click on your account name (top right)
3. View "Account Info" - you'll see:
   - **Account SID**: `AC...`
   - **Auth Token**: Click "View" to reveal

### 2. Check Environment Variables

#### For Local Development:

**Option A: Using .env file**
1. Open `.env` file in your project root
2. Make sure it contains:
   ```env
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your-auth-token-here
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   ADMIN_WHATSAPP_NUMBER=whatsapp:+1234567890
   ```
3. **Important**: Replace with your actual credentials!

**Option B: Set in PowerShell (temporary)**
```powershell
$env:TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$env:TWILIO_AUTH_TOKEN="your-auth-token-here"
$env:TWILIO_WHATSAPP_FROM="whatsapp:+14155238886"
$env:ADMIN_WHATSAPP_NUMBER="whatsapp:+1234567890"
```

#### For Render Deployment:

1. Go to https://dashboard.render.com
2. Click on your service
3. Go to **Environment** tab
4. Verify these variables are set:
   - `TWILIO_ACCOUNT_SID` = `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - `TWILIO_AUTH_TOKEN` = `your-auth-token-here`
   - `TWILIO_WHATSAPP_FROM` = `whatsapp:+14155238886`
   - `ADMIN_WHATSAPP_NUMBER` = `whatsapp:+1234567890`

5. **Important**: 
   - Make sure there are no extra spaces
   - Make sure Account SID starts with `AC`
   - Make sure Auth Token is the full token (not truncated)

### 3. Check Admin Dashboard Settings

If you set credentials via Admin Dashboard:

1. Go to Admin Dashboard → WhatsApp Settings
2. Verify:
   - **Account SID** starts with `AC`
   - **Auth Token** is complete (not cut off)
   - All fields are filled

### 4. Common Mistakes

❌ **Wrong Account SID format:**
- Wrong: `AUGdWCqV7FR445qeZN7NtgrX5Xzox2jzXJ` (this is NOT Account SID - it's an Auth Token)
- Correct: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (starts with `AC`)

❌ **Using Auth Token as Account SID:**
- The value starting with `AU` is an **Auth Token**, not Account SID
- Account SID should start with `AC`

❌ **Extra spaces or quotes:**
- Wrong: `TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"` (quotes)
- Wrong: `TWILIO_ACCOUNT_SID= ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (space)
- Correct: `TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## Finding Your Credentials

To find your correct credentials:

1. **From your curl command:**
   - The Account SID is in the URL: `https://api.twilio.com/2010-04-01/Accounts/{ACCOUNT_SID}/Messages.json`
   - The Auth Token is after `-u` flag: `ACCOUNT_SID:AUTH_TOKEN`

2. **From Twilio Console:**
   - Go to https://console.twilio.com
   - Click Account Info
   - Copy Account SID and Auth Token

3. **Format:**
   ```env
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your-auth-token-here
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   ADMIN_WHATSAPP_NUMBER=whatsapp:+your-phone-number
   TWILIO_CONTENT_SID=HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

## Testing Your Credentials

### Test via curl (PowerShell):
```powershell
$accountSid = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$authToken = "your-auth-token-here"
$to = "whatsapp:+1234567890"
$from = "whatsapp:+14155238886"

$base64Auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${accountSid}:${authToken}"))

$headers = @{
    "Authorization" = "Basic $base64Auth"
}

$body = @{
    To = $to
    From = $from
    Body = "Test message"
}

Invoke-RestMethod -Uri "https://api.twilio.com/2010-04-01/Accounts/$accountSid/Messages.json" -Method Post -Headers $headers -Body $body
```

If this works, your credentials are correct. If not, check your Twilio console.

## Still Not Working?

1. **Verify Twilio Account is Active:**
   - Log into https://console.twilio.com
   - Check if account is suspended or has billing issues

2. **Check WhatsApp is Enabled:**
   - Go to Twilio Console → Messaging → Try it out → Send a WhatsApp message
   - Verify WhatsApp sandbox is set up

3. **Check Logs:**
   - Look at your app logs for more detailed error messages
   - The app now shows masked Account SID in debug logs

4. **Regenerate Auth Token:**
   - If credentials were exposed, regenerate them in Twilio Console
   - Update environment variables with new token

## Need Help?

- Twilio Support: https://support.twilio.com
- Twilio Docs: https://www.twilio.com/docs/errors/20003

