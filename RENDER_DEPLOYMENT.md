# Render Deployment Guide - Fixed ModuleNotFoundError

## Problems & Solutions

### ✅ Fixed: ModuleNotFoundError: No module named 'app'
- **Cause**: Running from project root, but app was in `backend/` folder
- **Fixed**: Using correct module path from project root

### ✅ Fixed: ModuleNotFoundError: No module named 'app.models'
- **Cause**: Missing `__init__.py` files in package directories
- **Fixed**: Added `__init__.py` to all subdirectories

## Updated Configuration

### render.yaml (Recommended)
```yaml
services:
  - type: web
    name: ai-chatbot
    runtime: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: "3.11"
```

### Procfile (Alternative)
```
web: python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

## Key Changes

| Component | Before | After | Why |
|-----------|--------|-------|-----|
| **Working Directory** | `cd backend &&` | Project root | Cleaner path handling |
| **Module Path** | `app.main:app` | `backend.app.main:app` | Full module path from root |
| **Package Files** | Missing `__init__.py` in some dirs | All dirs have `__init__.py` | Python package recognition |

## Files Created/Updated

✅ **Created missing `__init__.py` files:**
- `backend/__init__.py`
- `backend/app/data/__init__.py`
- `backend/app/scripts/__init__.py`
- `backend/app/models/__init__.py` (may have been missing)

✅ **Updated configuration files:**
- `render.yaml` - Use project root with full module path
- `Procfile` - Use project root with full module path

## Deploy Steps

### 1. Commit all changes
```bash
cd "d:\RA\AI Chatbot"
git add -A
git commit -m "Fix Render deployment: add missing __init__.py files and update configuration"
git push origin main
```

### 2. Redeploy on Render
- Go to Render Dashboard → Your Service
- Click **Redeploy** button
- Wait for deployment to complete

### 3. Monitor Logs
- Check **Logs** tab
- Look for: `Uvicorn running on`
- Health check: `https://your-app.onrender.com/health`

## Environment Variables

Add in Render Dashboard → **Environment**:

```env
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...
SUPABASE_KEY=...
DEBUG=False
ENVIRONMENT=production
HOST=0.0.0.0
PORT=10000
```

## Start Command Breakdown

```bash
python -m uvicorn backend.app.main:app \
  --host 0.0.0.0 \           # Listen on all IPs
  --port $PORT               # Use Render's PORT (10000)
```

- `python -m uvicorn` - Run uvicorn as Python module
- `backend.app.main:app` - Path to FastAPI app (from project root)
- `--host 0.0.0.0` - Accept external connections
- `--port $PORT` - Use environment variable

## Troubleshooting

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'app'` | Use `backend.app.main:app` not just `app.main:app` |
| `ModuleNotFoundError: No module named 'app.models'` | Ensure `__init__.py` exists in all subdirectories |
| `No open ports detected` | App might be crashing - check logs |
| `Connection refused` | Make sure port is `$PORT` variable not hardcoded |

## Verify Deployment

After successful deployment, test:

```bash
# Health check
curl https://your-app.onrender.com/health

# Should return:
# {"status":"ok"}
```

## Local Testing

Test locally before pushing:

```bash
# From project root
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Should work identically to Render!

---

**✅ Ready to Deploy!** Push changes and redeploy.

