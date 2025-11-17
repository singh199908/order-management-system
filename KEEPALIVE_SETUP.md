# Keepalive Setup for Render

Render's **free tier** automatically spins down your app after **15 minutes of inactivity**. This means the first request after spin-down takes ~30 seconds to respond.

To keep your app alive, you need to ping it regularly (at least every 14 minutes).

## Solution 1: External Ping Service (Recommended - Free)

Use an external service to ping your app automatically.

### Option A: UptimeRobot (Free, Easy)

1. **Sign up**: Go to https://uptimerobot.com (free account)
2. **Add Monitor**:
   - Click "Add New Monitor"
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: Order Management System
   - **URL**: `https://your-app-name.onrender.com/health`
   - **Monitoring Interval**: 5 minutes (recommended)
   - Click "Create Monitor"

3. **Done!** UptimeRobot will ping your app every 5 minutes, keeping it alive.

### Option B: cron-job.org (Free, Simple)

1. **Sign up**: Go to https://cron-job.org (free account)
2. **Create Cronjob**:
   - Click "Create cronjob"
   - **Title**: Render Keepalive
   - **Address**: `https://your-app-name.onrender.com/health`
   - **Schedule**: Every 10 minutes (`*/10 * * * *`)
   - Click "Create cronjob"

3. **Done!** Your app will be pinged every 10 minutes.

### Option C: EasyCron (Free Tier Available)

1. **Sign up**: Go to https://www.easycron.com
2. **Create Cron Job**:
   - **URL**: `https://your-app-name.onrender.com/health`
   - **Schedule**: Every 10 minutes
   - Save

## Solution 2: Self-Pinging Script (Advanced)

If you have a server that's always on, you can create a simple script:

### Python Script:
```python
import requests
import time
from datetime import datetime

def ping_app():
    url = "https://your-app-name.onrender.com/health"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"[{datetime.now()}] ✅ Ping successful")
        else:
            print(f"[{datetime.now()}] ⚠️ Ping failed: {response.status_code}")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error: {e}")

# Run every 10 minutes
while True:
    ping_app()
    time.sleep(600)  # 10 minutes = 600 seconds
```

### Windows Task Scheduler:
1. Create a batch file `ping_render.bat`:
   ```batch
   @echo off
   curl https://your-app-name.onrender.com/health
   ```
2. Open Task Scheduler
3. Create Basic Task
4. Set to run every 10 minutes

## Solution 3: Upgrade to Paid Plan

Render's **Starter plan** ($7/month) includes:
- ✅ Always-on service (no spin-down)
- ✅ Better performance
- ✅ More resources

**Upgrade**: Go to Render Dashboard → Your Service → Settings → Change Plan

## Health Check Endpoint

Your app now has a health check endpoint:
- **URL**: `https://your-app-name.onrender.com/health`
- **Method**: GET
- **Response**: 
  ```json
  {
    "status": "ok",
    "message": "Server is running",
    "timestamp": "2025-11-16T19:30:00.000000"
  }
  ```

You can also use `/ping` - it's the same endpoint.

## Testing

Test your health check endpoint:
```bash
curl https://your-app-name.onrender.com/health
```

Or visit in browser: `https://your-app-name.onrender.com/health`

## Recommended Setup

**For Free Tier:**
1. Use **UptimeRobot** (easiest, most reliable)
2. Set monitoring interval to **5 minutes**
3. Monitor the `/health` endpoint

**For Production:**
- Upgrade to Render Starter plan ($7/month) for always-on service

## Troubleshooting

### App Still Spinning Down?
- Check that your ping service is actually running
- Verify the URL is correct (include `/health`)
- Check UptimeRobot/cron-job logs for errors
- Make sure ping interval is less than 14 minutes

### First Request Still Slow?
- This is normal on free tier - the app needs to wake up
- Consider upgrading to paid plan for instant responses

## Notes

- ⚠️ **Free tier limitations**: Even with keepalive, Render free tier has resource limits
- ✅ **Health endpoint**: Added to your app at `/health` and `/ping`
- 🔄 **Auto-ping**: External services handle this automatically
- 💰 **Upgrade**: Paid plans eliminate the need for keepalive


