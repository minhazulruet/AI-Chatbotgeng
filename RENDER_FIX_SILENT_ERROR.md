# Render Deployment - Silent Exit Error Fix

## Issue
App exits with status 1 but shows no error. Usually due to missing environment variables.

## Solution: Add Environment Variables

### Go to Render Dashboard:
1. Click your **AI-Chatbot** service
2. Click **Settings**
3. Scroll to **Environment**
4. Add these variables:

**Minimum Required:**
```
DEBUG=False
ENVIRONMENT=production
```

**Recommended:**
```
DEBUG=False
ENVIRONMENT=production
OPENAI_API_KEY=sk-your-key-here
SUPABASE_URL=https://your-db.supabase.co
SUPABASE_KEY=your-supabase-key
```

### Then:
5. Click **Save**
6. Click **Redeploy**
7. Check logs for `Uvicorn running on http://0.0.0.0:10000` ✓

## What Changed

✅ **asgi.py** - Added better error logging  
✅ **main.py** - Database init now handles errors gracefully  
✅ **Startup** - App won't crash if DB connection fails

## Test Locally

```bash
cd "d:\RA\AI Chatbot"
python -m uvicorn asgi:app --host 0.0.0.0 --port 8000
```

Should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Still Not Working?

Check Render logs for actual error message and share it.
