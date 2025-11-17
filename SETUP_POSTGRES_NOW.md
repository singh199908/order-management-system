# Set Up PostgreSQL on Render - Quick Steps

## Why?
Without PostgreSQL, your SQLite database gets deleted every time Render redeploys. PostgreSQL persists your data!

## Quick Setup (5 minutes)

### Step 1: Create PostgreSQL Database

1. **Go to Render Dashboard:**
   - Visit: https://dashboard.render.com
   - Click "New +" → "PostgreSQL"

2. **Configure:**
   - **Name**: `order-management-db` (or any name)
   - **Database**: `orders` (or leave default)
   - **Region**: Same as your web service
   - **Plan**: Free (or upgrade later)
   - Click "Create Database"

3. **Wait 1-2 minutes** for it to be "Available"

### Step 2: Copy Database URL

1. **In your PostgreSQL database dashboard:**
   - Find "Internal Database URL" or "Connection String"
   - It looks like: `postgresql://user:password@host:5432/dbname`
   - Click "Copy" to copy it

### Step 3: Add to Your Web Service

1. **Go to your web service:**
   - Click on `order-management-system` service
   - Go to "Environment" tab

2. **Add DATABASE_URL:**
   - Click "Add Environment Variable"
   - **Key**: `DATABASE_URL`
   - **Value**: Paste the PostgreSQL connection string you copied
   - Click "Save Changes"

3. **Render will auto-redeploy** (wait 1-2 minutes)

### Step 4: Test It Works

1. **After redeploy:**
   - Create a BA user
   - Place a test order
   - Check Render logs - should see database connection messages

2. **Test persistence:**
   - Create a BA user
   - Place an order
   - **Redeploy the app** (Manual Deploy → Deploy latest commit)
   - Check if BA and order still exist (they should!)

## That's It!

Once `DATABASE_URL` is set, your app will:
- ✅ Use PostgreSQL instead of SQLite
- ✅ Keep all data after redeploys
- ✅ Persist BAs, orders, products, and OAuth tokens

## Troubleshooting

### "Database connection failed"
- Check `DATABASE_URL` is set correctly
- Make sure PostgreSQL database is "Available" (not paused)
- Wait a few minutes after setting the variable

### "Tables don't exist"
- The app creates tables automatically on first run
- Check logs for table creation messages

### Data still getting deleted
- Make sure `DATABASE_URL` is set (check Environment tab)
- Verify it's pointing to PostgreSQL (starts with `postgresql://`)
- Check PostgreSQL database is running

## Quick Checklist

- [ ] Created PostgreSQL database on Render
- [ ] Copied Internal Database URL
- [ ] Added `DATABASE_URL` to web service environment variables
- [ ] Waited for auto-redeploy
- [ ] Tested that data persists after redeploy

