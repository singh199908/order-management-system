# How to Update Your App on Render

After pushing changes to GitHub, here's how to update your Render deployment:

## Option 1: Automatic Deployment (Recommended)

If you connected your GitHub repository to Render, **Render automatically deploys** when you push to the main branch!

1. **Check Render Dashboard:**
   - Go to https://dashboard.render.com
   - Click on your web service: `order-management-system`
   - You should see a new deployment starting automatically

2. **Monitor the Deployment:**
   - Watch the build logs in real-time
   - Wait for "Your service is live" message
   - Usually takes 2-5 minutes

## Option 2: Manual Deploy (If Auto-Deploy is Off)

If automatic deployment is disabled:

1. **Go to Render Dashboard:**
   - Visit https://dashboard.render.com
   - Click on your web service

2. **Manual Deploy:**
   - Click the **"Manual Deploy"** button
   - Select **"Deploy latest commit"**
   - Click **"Deploy"**

## Option 3: Clear Build Cache (If Build Fails)

If you encounter build issues:

1. **Go to your service settings:**
   - Click on your web service
   - Go to **"Settings"** tab

2. **Clear build cache:**
   - Scroll to **"Build & Deploy"** section
   - Click **"Clear build cache"**
   - Then deploy again

## Verify the Update

1. **Check the deployment logs:**
   - Look for successful build messages
   - Verify no errors in the logs

2. **Test your app:**
   - Visit your Render URL (e.g., `https://order-management-system.onrender.com`)
   - Test the new features:
     - Try logging in with: `rtc` / `rtc1336`
     - Check mobile responsiveness
     - Verify all pages work correctly

## Troubleshooting

### Build Fails:
- Check the build logs for error messages
- Ensure all dependencies are in `requirements.txt`
- Verify Python version in `runtime.txt`

### App Crashes After Deploy:
- Check the runtime logs
- Verify environment variables are set correctly
- Ensure database migrations completed

### Changes Not Showing:
- Clear browser cache
- Wait a few minutes for DNS propagation
- Check if deployment actually completed successfully

## Quick Checklist

- ✅ Code pushed to GitHub
- ✅ Render service connected to GitHub repo
- ✅ Auto-deploy enabled (or manual deploy triggered)
- ✅ Build completed successfully
- ✅ App is live and working

## Environment Variables to Verify

Make sure these are set in Render dashboard (Settings → Environment):
- `SECRET_KEY`
- `DATABASE_URL` (Render PostgreSQL connection string)
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_FROM`
- `ADMIN_WHATSAPP_NUMBER`
- `TWILIO_CONTENT_SID`
- `GOOGLE_SERVICE_ACCOUNT_JSON` (or `GOOGLE_SERVICE_ACCOUNT_FILE`)
- `GOOGLE_DRIVE_FOLDER_ID` (optional)


