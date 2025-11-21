# Deploying to Render.com

This guide will help you deploy the Order Management System to Render.com.

## Prerequisites

1. A GitHub or GitLab account
2. A Render.com account (sign up at https://render.com)

## Step 1: Push to GitHub/GitLab

### Option A: Using GitHub

1. **Create a new repository on GitHub:**
   - Go to https://github.com/new
   - Repository name: `order-management-system`
   - Make it **Private** (recommended) or Public
   - Click "Create repository"

2. **Push your code to GitHub:**
   ```bash
   cd C:\Users\aksha\OneDrive\Desktop\order_management_system
   git remote add origin https://github.com/YOUR_USERNAME/order-management-system.git
   git branch -M main
   git push -u origin main
   ```

### Option B: Using GitLab

1. **Create a new project on GitLab:**
   - Go to https://gitlab.com/projects/new
   - Project name: `order-management-system`
   - Visibility: **Private** (recommended) or Public
   - Click "Create project"

2. **Push your code to GitLab:**
   ```bash
   cd C:\Users\aksha\OneDrive\Desktop\order_management_system
   git remote add origin https://gitlab.com/YOUR_USERNAME/order-management-system.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Deploy on Render

1. **Sign in to Render:**
   - Go to https://render.com
   - Sign in with your GitHub/GitLab account

2. **Create a New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub/GitLab repository
   - Select the `order-management-system` repository

3. **Configure the Service:**
   - **Name:** `order-management-system`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
   - **Plan:** Choose Free or Starter (Free has limitations)

4. **Set Environment Variables:**
   Click "Advanced" → "Add Environment Variable" and add:
   ```
   SECRET_KEY=<generate a random secret key>
   TWILIO_ACCOUNT_SID=your_account_sid_here
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   ADMIN_WHATSAPP_NUMBER=whatsapp:+1234567890
    DATABASE_URL=<render-postgres-connection-string>
   # Google OAuth (Recommended - uses your personal storage)
   GOOGLE_OAUTH_CLIENT_ID=your-oauth-client-id.apps.googleusercontent.com
   GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-your-client-secret
   GOOGLE_OAUTH_REDIRECT_URI=https://your-app-name.onrender.com/oauth2callback
    GOOGLE_DRIVE_FOLDER_ID=<optional-folder-id>
   ```
   > **Important**: 
   > - Replace `your-app-name` in `GOOGLE_OAUTH_REDIRECT_URI` with your actual Render app name
   > - Update the redirect URI in Google Cloud Console OAuth Client settings to match
   > - Render sets `PORT` automatically, so you don't need to define it manually

5. **Deploy:**
   - Click "Create Web Service"
   - Render will automatically build and deploy your app
   - Wait for the deployment to complete (5-10 minutes)

## Step 3: Access Your Application

- Once deployed, Render will provide a URL like: `https://order-management-system.onrender.com`
- Your app will be live at this URL!

## Important Notes

### Free Tier Limitations:
- **Spins down after 15 minutes of inactivity** - First request after spin-down takes ~30 seconds
- **Limited resources** - May be slow with many users
- **No persistent storage** - Database resets on redeploy (use Render PostgreSQL for production)

### For Production Use:
1. **Upgrade to a paid plan** for:
   - Always-on service (no spin-down)
   - Better performance
   - Persistent storage

2. **Use Render PostgreSQL:**
   - Create a PostgreSQL database on Render
   - Copy the connection string into the `DATABASE_URL` environment variable (the app automatically detects it)

3. **Set up custom domain:**
   - Add your domain in Render dashboard
   - Update DNS records as instructed

## Troubleshooting

### Build Fails:
- Check the build logs in Render dashboard
- Ensure all dependencies are in `requirements.txt`
- Verify Python version in `runtime.txt`

### App Crashes:
- Check the logs in Render dashboard
- Verify all environment variables are set correctly
- Ensure `PORT` environment variable is used (Render sets this automatically)

### Database Issues:
- Free tier: Database resets on redeploy
- Use Render PostgreSQL for persistent storage

## Security Reminders

⚠️ **IMPORTANT:** 
- Never commit sensitive credentials to Git
- Use environment variables for all secrets
- The `render.yaml` file contains credentials - consider removing it and using only environment variables in Render dashboard

## Next Steps

1. Test your deployed application
2. Share the URL with your BAs
3. Monitor usage and upgrade if needed
4. Set up a custom domain (optional)

