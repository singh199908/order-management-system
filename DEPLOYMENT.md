# Deployment Guide - Order Management System

## Quick Deployment Options

### Option 1: Render (Recommended - Free Tier Available)

1. **Create Account**: Sign up at https://render.com

2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository (or use manual deploy)

3. **Configure Settings**:
   - **Name**: order-management-system
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Port**: 5000 (or leave default)

4. **Set Environment Variables** (in Render dashboard):
   ```
   TWILIO_ACCOUNT_SID=your_account_sid_here
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   ADMIN_WHATSAPP_NUMBER=whatsapp:+916392104804
   TWILIO_CONTENT_SID=HXb5b62575e6e4ff6129ad7c8efe1f983e
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=<render-postgres-connection-string>
   # Choose one of the following for Google credentials
   GOOGLE_SERVICE_ACCOUNT_JSON=<paste-json-here>
   # or
   GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
   GOOGLE_DRIVE_FOLDER_ID=<optional-folder-id>
   ```

5. **Deploy**: Click "Create Web Service"

Your site will be live at: `https://your-app-name.onrender.com`

---

### Option 2: Railway (Free Tier Available)

1. **Create Account**: Sign up at https://railway.app

2. **New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo" or "Empty Project"

3. **Add Service**:
   - Add a new service
   - Select your repository or upload files

4. **Configure**:
   - Railway auto-detects Python
   - Add environment variables in the Variables tab

5. **Deploy**: Railway will auto-deploy

Your site will be live at: `https://your-app-name.up.railway.app`

---

### Option 3: PythonAnywhere (Free Tier Available)

1. **Create Account**: Sign up at https://www.pythonanywhere.com

2. **Upload Files**:
   - Go to Files tab
   - Upload all project files to `/home/yourusername/order_management_system/`

3. **Open Bash Console**:
   - Install dependencies: `pip3.10 install --user -r requirements.txt`

4. **Create Web App**:
   - Go to Web tab
   - Click "Add a new web app"
   - Select "Manual configuration" → Python 3.10
   - Set source code: `/home/yourusername/order_management_system/`

5. **Edit WSGI File**:
   - Click on the WSGI file link
   - Replace content with:
   ```python
   import sys
   path = '/home/yourusername/order_management_system'
   if path not in sys.path:
       sys.path.append(path)
   
   from app import app as application
   ```

6. **Reload Web App**: Click the reload button

Your site will be live at: `https://yourusername.pythonanywhere.com`

---

### Option 4: Heroku (Paid, but has free tier alternatives)

1. **Install Heroku CLI**: https://devcenter.heroku.com/articles/heroku-cli

2. **Login**:
   ```bash
   heroku login
   ```

3. **Create App**:
   ```bash
   heroku create your-app-name
   ```

4. **Set Environment Variables**:
   ```bash
   heroku config:set TWILIO_ACCOUNT_SID=your_account_sid_here
   heroku config:set TWILIO_AUTH_TOKEN=your_token
   heroku config:set TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   heroku config:set ADMIN_WHATSAPP_NUMBER=whatsapp:+916392104804
   heroku config:set TWILIO_CONTENT_SID=HXb5b62575e6e4ff6129ad7c8efe1f983e
   heroku config:set SECRET_KEY=your-secret-key
   ```

5. **Deploy**:
   ```bash
   git push heroku main
   ```

---

### Option 5: Local Network Hosting (For Testing)

If you want to host on your local network:

1. **Find Your IP Address**:
   - Windows: `ipconfig` (look for IPv4 Address)
   - Mac/Linux: `ifconfig` or `ip addr`

2. **Update app.py** (already configured):
   - The app already runs on `0.0.0.0` which allows network access

3. **Run the App**:
   ```bash
   python app.py
   ```

4. **Access from Other Devices**:
   - On same network: `http://YOUR_IP_ADDRESS:5000`
   - Example: `http://192.168.1.100:5000`

5. **Firewall**: Make sure port 5000 is allowed in Windows Firewall

---

## Important Notes for Production

### Security Checklist:
- [ ] Change default admin password
- [ ] Set a strong SECRET_KEY
- [ ] Use environment variables for sensitive data
- [ ] Enable HTTPS (most hosting platforms do this automatically)
- [ ] Regular backups of orders.db

### Database Considerations:
- SQLite works for small to medium deployments
- For larger scale, consider PostgreSQL (Render/Railway support this)
- Set the `DATABASE_URL` environment variable to your managed database connection string

### WhatsApp Configuration:
- Make sure Twilio credentials are set as environment variables
- Test WhatsApp notifications after deployment
- Verify your WhatsApp number is approved in Twilio

### File Uploads:
- The `uploads/` folder is temporary
- For production, consider cloud storage (AWS S3, etc.)
- Or ensure persistent storage on your hosting platform

---

## Quick Start Commands

### For Local Testing:
```bash
cd order_management_system
pip install -r requirements.txt
python app.py
```

### For Production:
- Use hosting platform's deployment process
- Set environment variables
- Deploy and test

---

## Troubleshooting

### Port Already in Use:
- Change port in app.py or set PORT environment variable
- Kill existing process: `taskkill /F /IM python.exe` (Windows)

### Database Issues:
- Delete orders.db to reset (loses all data)
- Check file permissions

### WhatsApp Not Working:
- Verify Twilio credentials
- Check Twilio console for errors
- Ensure WhatsApp number is approved

---

## Recommended: Render.com (Easiest)

**Why Render?**
- Free tier available
- Easy setup
- Automatic HTTPS
- Environment variable management
- Auto-deploy from GitHub

**Steps:**
1. Push code to GitHub
2. Connect GitHub to Render
3. Set environment variables
4. Deploy!

Your site will be live in minutes! 🚀

