# TDIS - Ready for Render Deployment

## ✅ Pre-Deployment Checklist Complete

All files have been prepared and optimized for Render deployment.

### Files Ready
- ✅ `requirements.txt` - Fixed (removed invalid python version)
- ✅ `render.yaml` - Blueprint configured (4 services)
- ✅ `Procfile` - Gunicorn configuration
- ✅ `runtime.txt` - Python 3.11.0
- ✅ `render-build.sh` - Build script with permissions
- ✅ `frontend/` - React app ready for static site deployment
- ✅ `.gitignore` - Sensitive files excluded
- ✅ `.env.example` - Environment template

### Configuration Updates Made
1. **requirements.txt** - Removed invalid `python==3.10.13` line
2. **render.yaml** - Added `SEED_DEFAULT_USERS=false` for production
3. **render.yaml** - Reordered services (database first, then Redis, then backend, then frontend)
4. **render.yaml** - Fixed build command permissions: `chmod +x render-build.sh`

---

## Deployment Methods

### Method 1: Using Render MCP Server (Recommended)

Since you have the Render MCP server configured, you can deploy directly from Kiro:

#### Step 1: Restart Kiro (if you haven't)
```
Ctrl+Shift+P → Developer: Reload Window
```

#### Step 2: Set Workspace
```
Set my Render workspace to [your-workspace-name]
```

#### Step 3: Deploy Using Natural Language

**Option A: Deploy Everything**
```
Deploy my TDIS application to Render using the render.yaml blueprint in c:\Users\ElsieSetladi\Demo TDIS\TDIS
```

**Option B: Step-by-Step**

1. **Create Database:**
```
Create a new Render Postgres database named tdis-database with plan starter
```

2. **Create Redis:**
```
Create a new Render Redis instance named tdis-redis with plan starter
```

3. **Create Backend:**
```
Create a web service named tdis-backend using Python with the repository at [your-github-repo-url]
```

4. **Create Frontend:**
```
Create a static site named tdis-frontend using the repository at [your-github-repo-url]/frontend
```

---

### Method 2: Manual Deployment via Render Dashboard

#### Step 1: Push to Git

```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

#### Step 2: Create Services on Render

Go to https://dashboard.render.com

##### A. Create PostgreSQL Database
1. Click "New +" → "PostgreSQL"
2. **Name:** `tdis-database`
3. **Database:** `tdis_production`
4. **User:** `tdis_user`
5. **Region:** Oregon (US West)
6. **Plan:** Starter ($7/month)
7. Click "Create Database"
8. **Save the connection string** (you'll need it)

##### B. Create Redis Instance
1. Click "New +" → "Redis"
2. **Name:** `tdis-redis`
3. **Region:** Oregon
4. **Plan:** Starter ($7/month)
5. **Maxmemory Policy:** allkeys-lru
6. Click "Create Redis"
7. **Save the connection string**

##### C. Create Backend Service
1. Click "New +" → "Web Service"
2. Connect your GitHub/GitLab repository
3. **Configuration:**
   - **Name:** `tdis-backend`
   - **Region:** Oregon
   - **Branch:** main
   - **Root Directory:** .
   - **Runtime:** Python 3
   - **Build Command:** `chmod +x render-build.sh && ./render-build.sh`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --access-logfile - --error-logfile -`
   - **Plan:** Starter ($7/month)

4. **Environment Variables:**
   ```
   FLASK_ENV=production
   SECRET_KEY=[auto-generate]
   SEED_DEFAULT_USERS=false
   DATABASE_URL=[paste database connection string]
   REDIS_URL=[paste redis connection string]
   CORS_ORIGINS=https://tdis-frontend.onrender.com
   UPLOAD_FOLDER=/var/data/uploads
   LOGS_FOLDER=/var/data/logs
   MAX_FILE_SIZE=524288000
   ENABLE_FILE_MIME_VALIDATION=true
   LOG_LEVEL=INFO
   LOG_TO_STDOUT=true
   ```

5. **Add Disk:**
   - **Name:** tdis-uploads
   - **Mount Path:** /var/data
   - **Size:** 10 GB
   - Click "Add Disk"

6. Click "Create Web Service"

##### D. Create Frontend Service
1. Click "New +" → "Static Site"
2. Connect same repository
3. **Configuration:**
   - **Name:** `tdis-frontend`
   - **Branch:** main
   - **Root Directory:** .
   - **Build Command:** `cd frontend && npm install && REACT_APP_API_URL=https://tdis-backend.onrender.com npm run build`
   - **Publish Directory:** `./frontend/build`

4. **Environment Variable:**
   ```
   REACT_APP_API_URL=https://tdis-backend.onrender.com
   ```

5. Click "Create Static Site"

#### Step 3: Wait for Deployment

- Database: ~5 minutes
- Redis: ~3 minutes
- Backend: ~10-15 minutes (downloads NLTK data)
- Frontend: ~5-10 minutes

#### Step 4: Create Admin User

Once backend is deployed, use Render Shell:

1. Go to backend service → Shell tab
2. Run:
```bash
python create_admin.py
```

3. Follow prompts to create admin account

---

### Method 3: Using Render Blueprint (Automated)

1. **Ensure render.yaml is in repository root**

2. **Push to Git:**
```bash
git add render.yaml
git commit -m "Add Render blueprint"
git push origin main
```

3. **Deploy Blueprint:**
   - Go to https://dashboard.render.com
   - Click "New +" → "Blueprint"
   - Connect repository
   - Render will auto-detect `render.yaml`
   - Review services (4 total)
   - Click "Apply"
   - All services deploy automatically!

---

## Post-Deployment Steps

### 1. Create Admin User

**Via Render Shell:**
```bash
python create_admin.py
```

**Or via Python:**
```python
from app import create_app
from models import db, User
from auth import hash_password

app = create_app('production')
with app.app_context():
    admin = User(
        name='Your Name',
        email='admin@example.com',
        password_hash=hash_password('YourSecurePassword123!'),
        is_admin=True,
        is_active=True,
        must_change_password=False
    )
    db.session.add(admin)
    db.session.commit()
    print('Admin created!')
```

### 2. Test Deployment

**Backend Health Check:**
```bash
curl https://tdis-backend.onrender.com/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-10-21T...",
  "services": {...}
}
```

**Frontend:**
Visit: https://tdis-frontend.onrender.com

### 3. Configure Custom Domain (Optional)

1. Go to frontend service → Settings → Custom Domain
2. Add your domain (e.g., `tdis.yourdomain.com`)
3. Update DNS records as instructed
4. Update `CORS_ORIGINS` in backend to include custom domain

### 4. Enable Email (Optional)

Add to backend environment variables:

```
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=[your-sendgrid-api-key]
MAIL_FROM=noreply@yourdomain.com
```

Redeploy backend after adding.

---

## Cost Estimate

Monthly costs on Render Starter plan:

| Service | Plan | Cost/Month |
|---------|------|------------|
| PostgreSQL | Starter | $7 |
| Redis | Starter | $7 |
| Backend Web Service | Starter | $7 |
| Frontend Static Site | Free | $0 |
| Disk Storage (10GB) | Included | $0 |
| **Total** | | **$21/month** |

### Free Tier Alternative

For testing, you can use free tier:
- Backend: Free (sleeps after 15 min inactivity)
- Frontend: Free
- PostgreSQL: Use external (Supabase free tier)
- Redis: Skip (app works without it)

**Estimated:** Free for 750 hours/month

---

## Monitoring & Maintenance

### View Logs

**Backend Logs:**
```bash
# Via Render Dashboard
Services → tdis-backend → Logs

# Via MCP (if configured)
Show recent logs for tdis-backend
```

**Database Logs:**
```bash
Services → tdis-database → Logs
```

### Monitor Metrics

- **CPU Usage:** Dashboard → Service → Metrics
- **Memory Usage:** Dashboard → Service → Metrics
- **Request Count:** Dashboard → Service → Metrics
- **Response Times:** Dashboard → Service → Metrics (Pro+ only)

### Database Backups

Render automatically backs up Postgres:
- **Frequency:** Daily
- **Retention:** 7 days (Starter plan)
- **Location:** Dashboard → Database → Backups

### Manual Backup

```bash
# Export database
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

---

## Troubleshooting

### Build Fails

**Check build logs:**
1. Services → tdis-backend → Events
2. Look for error messages
3. Common issues:
   - Missing dependencies in requirements.txt
   - NLTK download timeout (increase timeout)
   - Disk space full

**Solution:**
```bash
# Clear build cache and redeploy
Manual Deploy → Clear build cache → Deploy
```

### Database Connection Error

**Check:**
1. Database is running (green status)
2. `DATABASE_URL` environment variable is set correctly
3. Backend and database are in same region

**Test connection:**
```python
python -c "from app import create_app; app = create_app('production'); print('Connected!')"
```

### Frontend Can't Reach Backend

**Check:**
1. `REACT_APP_API_URL` points to correct backend URL
2. `CORS_ORIGINS` in backend includes frontend URL
3. Backend is running (not sleeping)

**Fix:**
Rebuild frontend with correct API URL

### App Running But No Admin

**Solution:**
Use Shell to create admin:
```bash
python create_admin.py
```

---

## Security Checklist

Before going live:

- [ ] Change all generated passwords
- [ ] Set strong `SECRET_KEY`
- [ ] Enable HTTPS (automatic on Render)
- [ ] Configure `CORS_ORIGINS` to specific domains
- [ ] Review database access (use private networks)
- [ ] Enable email notifications
- [ ] Set up monitoring alerts
- [ ] Configure backup schedule
- [ ] Review user permissions
- [ ] Test authentication flow
- [ ] Verify file upload limits
- [ ] Check log level (INFO for production)

---

## Quick Deploy Commands (MCP)

If MCP is configured:

```
# Deploy entire blueprint
Deploy TDIS using blueprint at c:\Users\ElsieSetladi\Demo TDIS\TDIS\render.yaml

# Check status
List my Render services

# View logs
Show logs for tdis-backend

# Redeploy
Deploy tdis-backend and clear build cache

# Check metrics
What was the CPU usage for tdis-backend today?
```

---

## URLs After Deployment

**Backend API:**
```
https://tdis-backend.onrender.com
https://tdis-backend.onrender.com/api/health
```

**Frontend:**
```
https://tdis-frontend.onrender.com
```

**Database:**
```
Internal URL (provided in env vars)
```

**Redis:**
```
Internal URL (provided in env vars)
```

---

## Need Help?

- **Render Documentation:** https://render.com/docs
- **Render Status:** https://status.render.com
- **Support:** https://render.com/support
- **Community:** https://community.render.com

---

**Status:** ✅ Ready to Deploy  
**Next Step:** Choose deployment method above  
**Estimated Time:** 30-45 minutes (automated)
