# Setting Up Render PostgreSQL for Database Persistence

## Problem
Without PostgreSQL, your database (BAs, orders, products) gets deleted every time Render redeploys because SQLite files don't persist.

## Solution: Use Render PostgreSQL

### Step 1: Create PostgreSQL Database on Render

1. **Go to Render Dashboard:**
   - Visit https://dashboard.render.com
   - Click "New +" → "PostgreSQL"

2. **Configure Database:**
   - **Name**: `order-management-db` (or any name you prefer)
   - **Database**: `orders` (or leave default)
   - **User**: (auto-generated)
   - **Region**: Same as your web service
   - **Plan**: Free (or upgrade for better performance)
   - Click "Create Database"

3. **Wait for Database to be Ready:**
   - Status will show "Available" when ready
   - This takes 1-2 minutes

### Step 2: Get Connection String

1. **Copy Internal Database URL:**
   - In your PostgreSQL database dashboard
   - Find "Internal Database URL" or "Connection String"
   - It looks like: `postgresql://user:password@host:5432/dbname`
   - Click "Copy" to copy it

### Step 3: Add to Web Service Environment Variables

1. **Go to Your Web Service:**
   - Click on your `order-management-system` web service
   - Go to "Environment" tab

2. **Add DATABASE_URL:**
   - Click "Add Environment Variable"
   - **Key**: `DATABASE_URL`
   - **Value**: Paste the PostgreSQL connection string you copied
   - Click "Save Changes"

3. **Redeploy:**
   - Render will automatically redeploy
   - Or click "Manual Deploy" → "Deploy latest commit"

### Step 4: Verify It's Working

1. **Check Logs:**
   - Go to "Logs" tab in your web service
   - Look for: "Creating tables" or database connection messages
   - No errors about database connection

2. **Test:**
   - Create a BA user
   - Place a test order
   - Redeploy the app
   - Check if BA and order still exist (they should!)

## Important Notes

### Free Tier Limitations:
- **90 days retention** - Free PostgreSQL databases are deleted after 90 days of inactivity
- **Limited storage** - 1 GB storage limit
- **No backups** - Upgrade for automated backups

### For Production:
- **Upgrade to paid plan** for:
  - Persistent storage (no 90-day deletion)
  - Automated backups
  - Better performance
  - More storage

## Troubleshooting

### "Database connection failed"
- Verify `DATABASE_URL` is set correctly
- Check that PostgreSQL database is "Available" (not paused)
- Ensure connection string format is correct: `postgresql://user:pass@host:5432/dbname`

### "Table doesn't exist"
- The app automatically creates tables on first run
- Check logs for table creation messages
- If tables aren't created, the app will create them on next request

### Data still getting deleted
- Make sure `DATABASE_URL` is set in environment variables
- Verify it's pointing to PostgreSQL (not SQLite)
- Check that PostgreSQL database is running and not paused

## Quick Checklist

- [ ] Created PostgreSQL database on Render
- [ ] Copied Internal Database URL
- [ ] Added `DATABASE_URL` to web service environment variables
- [ ] Redeployed the app
- [ ] Verified data persists after redeploy

