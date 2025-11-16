# Environment Variables for Render

This document lists all environment variables that need to be set in your Render dashboard.

## Required Variables

### 1. **SECRET_KEY** (Required)
- **Purpose**: Flask session encryption key
- **How to generate**: Use a random string generator or run: `python -c "import secrets; print(secrets.token_hex(32))"`
- **Example**: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6`
- **Where to set**: Render Dashboard → Your Service → Environment → Add Environment Variable

### 2. **TWILIO_ACCOUNT_SID** (Required for WhatsApp)
- **Purpose**: Your Twilio Account SID
- **Where to find**: Twilio Console → Account Info
- **Example**: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **Note**: Required if you want WhatsApp notifications

### 3. **TWILIO_AUTH_TOKEN** (Required for WhatsApp)
- **Purpose**: Your Twilio Auth Token
- **Where to find**: Twilio Console → Account Info
- **Example**: `your-auth-token-here`
- **Note**: Required if you want WhatsApp notifications
- **⚠️ Keep this secret!**

### 4. **TWILIO_WHATSAPP_FROM** (Required for WhatsApp)
- **Purpose**: Your Twilio WhatsApp sender number
- **Format**: Must start with `whatsapp:`
- **Example**: `whatsapp:+14155238886`
- **Note**: This is usually your Twilio sandbox number or approved WhatsApp Business number

### 5. **ADMIN_WHATSAPP_NUMBER** (Required for WhatsApp)
- **Purpose**: Your WhatsApp number to receive order notifications
- **Format**: Must start with `whatsapp:`
- **Example**: `whatsapp:+1234567890`
- **Note**: This is where you'll receive "YOU HAVE A NEW ORDER FROM..." messages

### 6. **TWILIO_CONTENT_SID** (Optional - Not Currently Used)
- **Purpose**: Twilio Content Template SID (if using templates)
- **Note**: Currently not used - the app sends plain text messages
- **Can be left empty** or set to any value

## Optional Variables

### 7. **PORT** (Auto-set by Render)
- **Purpose**: Server port number
- **Default**: Render automatically sets this
- **Note**: You don't need to set this manually - Render handles it

### 8. **SQLALCHEMY_DATABASE_URI** (Optional - for PostgreSQL)
- **Purpose**: Database connection string
- **Default**: Uses SQLite (`sqlite:///orders.db`)
- **For Production**: Use Render PostgreSQL database
- **Example**: `postgresql://user:pass@host:5432/dbname`
- **Note**: Only needed if you want persistent database (recommended for production)

## How to Set Environment Variables on Render

### Step-by-Step Instructions:

1. **Go to Render Dashboard:**
   - Visit https://dashboard.render.com
   - Click on your `order-management-system` service

2. **Navigate to Environment:**
   - Click on the **"Environment"** tab (or **"Settings"** → **"Environment"**)

3. **Add Variables:**
   - Click **"Add Environment Variable"**
   - Enter the **Key** (variable name)
   - Enter the **Value** (variable value)
   - Click **"Save Changes"**

4. **Redeploy:**
   - After adding variables, Render will automatically redeploy
   - Or click **"Manual Deploy"** → **"Deploy latest commit"**

## Minimum Required Variables

**For Basic Functionality (without WhatsApp):**
```
SECRET_KEY=<your-secret-key>
```

**For Full Functionality (with WhatsApp):**
```
SECRET_KEY=<your-secret-key>
TWILIO_ACCOUNT_SID=<your-account-sid>
TWILIO_AUTH_TOKEN=<your-auth-token>
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
ADMIN_WHATSAPP_NUMBER=whatsapp:+1234567890
```

## Security Best Practices

⚠️ **IMPORTANT:**
- Never commit environment variables to Git
- Never share your `TWILIO_AUTH_TOKEN` publicly
- Use strong, random values for `SECRET_KEY`
- Rotate credentials if they're ever exposed

## Testing Your Variables

After setting variables, check the logs:
1. Go to Render Dashboard → Your Service → **"Logs"** tab
2. Look for any error messages about missing variables
3. Test WhatsApp notifications by placing a test order

## Troubleshooting

### "WhatsApp not configured" warning:
- Check that all Twilio variables are set correctly
- Verify the format includes `whatsapp:` prefix
- Check Twilio console to ensure your account is active

### App crashes on startup:
- Verify `SECRET_KEY` is set
- Check all required variables are present
- Review logs for specific error messages

### WhatsApp messages not sending:
- Verify Twilio credentials are correct
- Check that numbers are in correct format (`whatsapp:+...`)
- Ensure your Twilio account has WhatsApp enabled
- Check Twilio console for any errors

