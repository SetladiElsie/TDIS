# Render Deployment - Unauthorized Error Fix

## Common Causes of "Unauthorized" Error

### 1. Database Connection Issue (Most Common)

**Problem:** The backend can't connect to PostgreSQL during build

**Solutions:**

#### A. Skip Database Init During Build
The database connection might not be available during build time. Let's move database initialization to runtime.

**Update Build Command to:**
```bash
pip install --upgrade pip && pip install -r requirements.txt && mkdir -p instance && python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('averaged_perceptron_tagger', quiet=True); print('NLTK data downloaded')"
```

(Removed the database initialization part)

The database will auto-initialize when the app first runs.

#### B. Check DATABASE_URL Environment Variable
1. Go to your backend service → Environment
2. Verify `DATABASE_URL` is set
3. Format should be: `postgresql://user:password@host:5432/database`
4. Make sure it's from the **Internal Database URL** of your PostgreSQL

---

### 2. PostgreSQL Database Not Created Yet

**Check:**
1. Go to Render Dashboard
2. Look for PostgreSQL database named `tdis-database`
3. Status should be **"Available"** (green)

**If database doesn't exist:**
1. Click "New +" → PostgreSQL
2. Name: `tdis-database`
3. Database: `tdis_production`
4. User: `tdis_user`
5. Region: Oregon (same as backend)
6. Plan: Free
7. Create Database
8. Wait ~5 minutes for it to be ready
9. Copy the **Internal Database URL**
10. Add it to backend environment variables as `DATABASE_URL`

---

### 3. Redis Connection Issue

**Check:**
1. Verify Redis service exists and is running
2. If not, you can disable Redis temporarily

**To disable Redis:**
In backend environment variables, remove or comment out:
- `REDIS_URL`

The app will work without Redis (uses in-memory cache).

---

### 4. Secret Key Issue

**Check:**
1. Go to backend service → Environment
2. Verify `SECRET_KEY` exists
3. If not, add it:
   - Key: `SECRET_KEY`
   - Value: Click "Generate" button (or use a long random string)

---

## Recommended Fix: Simplified Build

### Step 1: Update Build Command (No Database Init)

In your Render service settings:

**Build Command:**
```bash
pip install --upgrade pip && pip install -r requirements.txt && python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('averaged_perceptron_tagger', quiet=True); print('NLTK data downloaded')"
```

### Step 2: Verify Environment Variables

Required minimum:
```
FLASK_ENV=production
SECRET_KEY=[generated value]
SEED_DEFAULT_USERS=false
DATABASE_URL=[from PostgreSQL Internal URL]
UPLOAD_FOLDER=/tmp/uploads
LOGS_FOLDER=/tmp/logs
LOG_LEVEL=INFO
LOG_TO_STDOUT=true
```

Optional (can remove if causing issues):
```
REDIS_URL=[only if Redis service exists]
CORS_ORIGINS=http://localhost:3000
```

### Step 3: Deploy

1. Save changes
2. Manual Deploy → Clear build cache & deploy
3. Watch logs for errors

---

## Check Build Logs

Look for specific error messages:

### "no pg_hba.conf entry"
**Solution:** Use Internal Database URL, not External

### "password authentication failed"
**Solution:** 
1. Delete DATABASE_URL env var
2. Re-add it with fresh Internal URL from database page

### "database does not exist"
**Solution:** 
1. Database might not be ready
2. Wait 5 minutes
3. Refresh database page - status should be "Available"

### "Redis connection refused"
**Solution:** 
1. Remove REDIS_URL from environment variables
2. App will work without Redis

---

## Test Database Connection Separately

Once service is deployed (even if failing), use Shell to test:

1. Go to service → Shell tab
2. Run:
```bash
python -c "import os; print('DB URL:', os.getenv('DATABASE_URL', 'NOT SET'))"
```

3. Check if DATABASE_URL is set correctly

4. Test connection:
```bash
python -c "from app import create_app; app = create_app('production'); print('App created successfully')"
```

---

## Alternative: Manual Database Setup

If auto-initialization keeps failing, initialize database manually:

### Step 1: Deploy WITHOUT database init
Use simplified build command above

### Step 2: Once deployed, use Shell
1. Service → Shell tab
2. Run:
```bash
python -c "from app import create_app; from models import db; app = create_app('production'); app.app_context().push(); db.create_all(); print('Database initialized')"
```

### Step 3: Create Admin User
```bash
python create_admin.py
```

---

## Quick Fix Checklist

- [ ] PostgreSQL database is created and **"Available"**
- [ ] DATABASE_URL points to **Internal Database URL**
- [ ] SECRET_KEY is set (generated)
- [ ] Build command does NOT include database initialization
- [ ] SEED_DEFAULT_USERS=false
- [ ] Region matches between database and backend (both Oregon)
- [ ] Removed REDIS_URL if Redis not created
- [ ] Cleared build cache before redeploying

---

## If All Else Fails: Start Fresh

### Delete Everything and Recreate:

1. **Delete Services:**
   - Backend web service
   - Redis (if exists)
   - PostgreSQL database

2. **Create PostgreSQL First:**
   - New + → PostgreSQL
   - Name: `tdis-database`
   - Wait until "Available"
   - Copy Internal Database URL

3. **Create Backend:**
   - New + → Web Service
   - Repo: branch `develop`
   - Build command: (simplified - see above)
   - Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - Add environment variables
   - Create service

4. **Initialize Database via Shell:**
   - Wait for deployment
   - Shell → run database init
   - Create admin user

---

## Contact Me

If still getting unauthorized error, share:
1. Full error message from build logs
2. Which step it fails at (build or runtime?)
3. Screenshot of Environment variables (hide sensitive values)

I'll help you fix it! 🚀
