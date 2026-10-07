# TDIS Deployment Guide - Render Platform

## Overview
This guide walks you through deploying the Tender Document Information System (TDIS) to Render, a modern cloud platform that supports full-stack applications with PostgreSQL, Redis, and persistent storage.

## Prerequisites

### 1. Render Account
- Sign up at [render.com](https://render.com)
- Free tier available (sufficient for testing)
- Credit card required for paid plans

### 2. GitHub Repository
- Push your TDIS code to GitHub
- Make sure `.gitignore` excludes sensitive files
- Ensure all deployment files are committed

### 3. Required Files (Already Created)
- ✅ `render.yaml` - Render infrastructure configuration
- ✅ `render-build.sh` - Backend build script
- ✅ `Procfile` - Process definition for gunicorn
- ✅ `runtime.txt` - Python version specification
- ✅ `requirements.txt` - Python dependencies
- ✅ `.env.example` - Environment variable template

## Architecture on Render

```
┌─────────────────────────────────────────────────────────────┐
│                         Render Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Static Site     │         │  Web Service     │         │
│  │  (Frontend)      │────────▶│  (Backend)       │         │
│  │  React Build     │   API   │  Flask + Gunicorn│         │
│  │  Port: 443       │         │  Port: Dynamic   │         │
│  └──────────────────┘         └──────────────────┘         │
│                                        │                     │
│                                        │                     │
│                     ┌──────────────────┼──────────────────┐ │
│                     │                  │                  │ │
│              ┌──────▼──────┐    ┌─────▼──────┐  ┌───────▼────┐
│              │ PostgreSQL  │    │   Redis    │  │ Persistent │
│              │  Database   │    │   Cache    │  │   Disk     │
│              │             │    │            │  │  (Uploads) │
│              └─────────────┘    └────────────┘  └────────────┘
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Methods

### Option 1: Deploy with render.yaml (Recommended)

This method uses the `render.yaml` Blueprint to deploy all services at once.

#### Step 1: Prepare Your Repository

1. **Commit all deployment files:**
   ```bash
   git add render.yaml render-build.sh Procfile runtime.txt .env.example
   git commit -m "Add Render deployment configuration"
   git push origin main
   ```

2. **Make build script executable:**
   ```bash
   git update-index --chmod=+x render-build.sh
   git commit -m "Make render-build.sh executable"
   git push origin main
   ```

#### Step 2: Create New Blueprint on Render

1. **Login to Render Dashboard:**
   - Go to https://dashboard.render.com
   - Click "New +" button
   - Select "Blueprint"

2. **Connect Repository:**
   - Select "Connect a repository"
   - Authorize GitHub access
   - Choose your TDIS repository
   - Click "Connect"

3. **Configure Blueprint:**
   - Render will detect `render.yaml`
   - Review the services:
     - `tdis-backend` (Web Service)
     - `tdis-frontend` (Static Site)
     - `tdis-database` (PostgreSQL)
     - `tdis-redis` (Redis)
   
4. **Set Environment Variables:**
   - Most variables are set automatically
   - **IMPORTANT**: Update `CORS_ORIGINS` to match your frontend URL
   - Generate a strong `SECRET_KEY` (32+ characters)

5. **Deploy:**
   - Click "Apply"
   - Wait for services to build and deploy (5-10 minutes)
   - Monitor logs for any errors

#### Step 3: Post-Deployment Configuration

1. **Update Frontend API URL:**
   - Go to `tdis-frontend` service
   - Navigate to "Environment" tab
   - Set `REACT_APP_API_URL` to your backend URL:
     ```
     https://tdis-backend.onrender.com/api
     ```
   - Save and redeploy

2. **Update Backend CORS:**
   - Go to `tdis-backend` service
   - Navigate to "Environment" tab
   - Update `CORS_ORIGINS` to your frontend URL:
     ```
     https://tdis-frontend.onrender.com
     ```
   - Save and redeploy

3. **Verify Database Connection:**
   - Check backend logs for "Database tables created/verified"
   - If errors occur, check `DATABASE_URL` environment variable

### Option 2: Manual Deployment (Step by Step)

If you prefer manual control, deploy each service individually:

#### A. Deploy PostgreSQL Database

1. **Create Database:**
   - Click "New +" → "PostgreSQL"
   - Name: `tdis-database`
   - Database: `tdis_production`
   - User: `tdis_user`
   - Region: Choose closest to your users
   - Plan: Starter ($7/month) or Free
   - Click "Create Database"

2. **Note Connection Details:**
   - Internal Database URL (for backend)
   - External Database URL (for local access)

#### B. Deploy Redis Cache

1. **Create Redis:**
   - Click "New +" → "Redis"
   - Name: `tdis-redis`
   - Region: Same as database
   - Plan: Starter ($10/month) or Free (25MB)
   - Maxmemory Policy: `allkeys-lru`
   - Click "Create Redis"

2. **Note Connection URL:**
   - Will be used in backend environment variables

#### C. Deploy Backend (Flask API)

1. **Create Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Name: `tdis-backend`
   - Region: Same as database
   - Branch: `main`
   - Root Directory: Leave empty
   - Runtime: Python 3
   - Build Command:
     ```bash
     ./render-build.sh
     ```
   - Start Command:
     ```bash
     gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --access-logfile - --error-logfile -
     ```

2. **Add Environment Variables:**
   ```
   FLASK_ENV=production
   SECRET_KEY=<generate-random-32-char-string>
   DATABASE_URL=<from-postgresql-service>
   REDIS_URL=<from-redis-service>
   CORS_ORIGINS=https://tdis-frontend.onrender.com
   UPLOAD_FOLDER=/var/data/uploads
   LOGS_FOLDER=/var/data/logs
   MAX_FILE_SIZE=524288000
   ENABLE_FILE_MIME_VALIDATION=true
   ENABLE_VIRUS_SCANNING=false
   LOG_LEVEL=INFO
   LOG_TO_STDOUT=true
   ```

3. **Add Disk Storage:**
   - Name: `tdis-uploads`
   - Mount Path: `/var/data`
   - Size: 10 GB (adjust as needed)

4. **Deploy:**
   - Click "Create Web Service"
   - Wait for build and deployment

#### D. Deploy Frontend (React)

1. **Create Static Site:**
   - Click "New +" → "Static Site"
   - Connect your GitHub repository
   - Name: `tdis-frontend`
   - Branch: `main`
   - Root Directory: `frontend`
   - Build Command:
     ```bash
     npm install && npm run build
     ```
   - Publish Directory: `build`

2. **Add Environment Variables:**
   ```
   REACT_APP_API_URL=https://tdis-backend.onrender.com/api
   REACT_APP_API_TIMEOUT=30000
   ```

3. **Configure Redirects:**
   - Add rewrite rule for SPA routing:
   - Source: `/*`
   - Destination: `/index.html`
   - Action: Rewrite

4. **Deploy:**
   - Click "Create Static Site"
   - Wait for build and deployment

## Post-Deployment Steps

### 1. Verify Services

**Check Backend:**
```bash
curl https://tdis-backend.onrender.com/api/health
```
Should return: `{"status": "ok", "version": "1.0.0"}`

**Check Frontend:**
- Open `https://tdis-frontend.onrender.com`
- Should see login page
- Check browser console for errors

### 2. Create First Admin User

Connect to your backend shell and create admin:

```bash
# From Render dashboard, open backend service
# Click "Shell" tab and run:

python3 << EOF
from app import create_app
from models import db, User
from auth import hash_password

app = create_app('production')
with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(email='admin@yourdomain.com').first()
    if not admin:
        admin = User(
            name='Admin User',
            email='admin@yourdomain.com',
            password_hash=hash_password('TempAdmin123!'),
            is_admin=True,
            is_active=True,
            must_change_password=True
        )
        db.session.add(admin)
        db.session.commit()
        print('✅ Admin user created successfully')
    else:
        print('Admin user already exists')
EOF
```

### 3. Test Complete Flow

1. **Login:**
   - Navigate to frontend URL
   - Login with admin credentials
   - Change temporary password

2. **Upload Document:**
   - Test file upload
   - Verify extraction works
   - Check persistent storage

3. **Create Users:**
   - Test temporary password generation
   - Verify user can login and change password

### 4. Custom Domain (Optional)

**Add Custom Domain to Frontend:**
1. Go to frontend service settings
2. Click "Custom Domain"
3. Add your domain: `tenders.yourdomain.com`
4. Update DNS records as instructed
5. Render provides free SSL certificate

**Add Custom Domain to Backend:**
1. Go to backend service settings
2. Click "Custom Domain"
3. Add your domain: `api.yourdomain.com`
4. Update DNS records
5. Update frontend `REACT_APP_API_URL`

**Update CORS:**
```
CORS_ORIGINS=https://tenders.yourdomain.com,https://www.yourdomain.com
```

## Environment Variables Reference

### Backend Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `production` |
| `SECRET_KEY` | Flask secret key | Auto-generated |
| `DATABASE_URL` | PostgreSQL connection | Auto-set by Render |
| `REDIS_URL` | Redis connection | Auto-set by Render |
| `CORS_ORIGINS` | Allowed origins | Frontend URL |
| `UPLOAD_FOLDER` | Upload directory | `/var/data/uploads` |
| `LOGS_FOLDER` | Logs directory | `/var/data/logs` |
| `MAX_FILE_SIZE` | Max upload size (bytes) | `524288000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_TO_STDOUT` | Log to stdout | `true` |

### Frontend Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `REACT_APP_API_URL` | Backend API URL | `https://tdis-backend.onrender.com/api` |
| `REACT_APP_API_TIMEOUT` | API timeout (ms) | `30000` |

## Monitoring and Maintenance

### 1. View Logs

**Backend Logs:**
- Go to backend service
- Click "Logs" tab
- Filter by severity
- Download for analysis

**Frontend Logs:**
- Build logs show compilation
- Runtime logs limited for static sites
- Use browser console for client errors

### 2. Metrics and Alerts

**Enable Monitoring:**
- Go to service settings
- Enable metrics collection
- View CPU, memory, bandwidth usage
- Set up alerts for high usage

### 3. Backups

**Database Backups:**
- Automatic daily backups (Starter plan+)
- Manual backups available
- Download backups for local storage

**Upload Files:**
- Persistent disk is NOT automatically backed up
- Implement periodic backup strategy:
  1. Create backup script
  2. Run as cron job
  3. Store in cloud storage (S3, Google Cloud Storage)

### 4. Scaling

**Vertical Scaling:**
- Upgrade instance type
- More CPU/RAM for backend
- Larger disk for uploads

**Horizontal Scaling:**
- Increase web service instances
- Enable autoscaling (Pro plan+)
- Load balancer included

## Troubleshooting

### Build Failures

**Issue: Python dependencies fail to install**
```
Solution:
1. Check requirements.txt for conflicts
2. Pin specific versions
3. Check Render build logs for details
```

**Issue: NLTK data download fails**
```
Solution:
1. Check render-build.sh script
2. Verify SSL certificate handling
3. Download data during runtime if needed
```

### Runtime Errors

**Issue: "No module named 'app'"**
```
Solution:
1. Check start command in Render settings
2. Verify app.py creates 'app' variable
3. Check Python path and working directory
```

**Issue: Database connection fails**
```
Solution:
1. Verify DATABASE_URL is set
2. Check PostgreSQL service is running
3. Ensure connection string format is correct
4. Check network connectivity between services
```

**Issue: File uploads fail**
```
Solution:
1. Verify disk is attached at /var/data
2. Check UPLOAD_FOLDER environment variable
3. Verify disk has sufficient space
4. Check file permissions
```

### Frontend Issues

**Issue: "Failed to fetch" API errors**
```
Solution:
1. Verify REACT_APP_API_URL is correct
2. Check backend CORS_ORIGINS includes frontend URL
3. Verify backend is running
4. Check browser console for CORS errors
```

**Issue: 404 on page refresh**
```
Solution:
1. Add rewrite rule: /* → /index.html
2. Verify in Render static site settings
3. Redeploy frontend
```

## Cost Estimates

### Free Tier (Testing)
- Static Site: Free
- Web Service: Free (750 hrs/month)
- PostgreSQL: Free (90 days)
- Redis: Free (25MB, 30 days)
- **Total: $0** (limited duration)

### Starter Tier (Production)
- Static Site: Free
- Web Service: $7/month (512 MB RAM)
- PostgreSQL: $7/month (1 GB storage)
- Redis: $10/month (25 MB)
- Disk Storage: $0.25/GB/month (10 GB = $2.50)
- **Total: ~$26.50/month**

### Professional Tier (Scaling)
- Static Site: $20/month (CDN + custom)
- Web Service: $25/month (2 GB RAM)
- PostgreSQL: $25/month (10 GB storage)
- Redis: $30/month (1 GB)
- Disk Storage: $2.50/month (10 GB)
- **Total: ~$102.50/month**

## Security Best Practices

### 1. Environment Variables
- ✅ Never commit `.env` files
- ✅ Use Render's environment variables
- ✅ Rotate secrets regularly
- ✅ Use strong SECRET_KEY (32+ chars)

### 2. Database Security
- ✅ Use internal database URL for backend
- ✅ Limit external access
- ✅ Enable SSL connections
- ✅ Regular backups

### 3. API Security
- ✅ Strict CORS configuration
- ✅ JWT token authentication
- ✅ Rate limiting (implement if needed)
- ✅ Input validation

### 4. File Upload Security
- ✅ MIME type validation enabled
- ✅ File size limits enforced
- ✅ Quarantine suspicious files
- ✅ Virus scanning (if enabled)

## Performance Optimization

### 1. Backend
- ✅ Gunicorn with multiple workers (4)
- ✅ Redis caching enabled
- ✅ Database connection pooling
- ✅ Gzip compression

### 2. Frontend
- ✅ Production React build
- ✅ Static asset optimization
- ✅ CDN delivery (on Render)
- ✅ Browser caching headers

### 3. Database
- ✅ PostgreSQL indexes
- ✅ Query optimization
- ✅ Connection pooling
- ✅ Regular VACUUM

## Next Steps After Deployment

1. **Test Thoroughly:**
   - All features working
   - File uploads and extraction
   - User authentication
   - Password changes

2. **Configure Monitoring:**
   - Set up alerts
   - Monitor resource usage
   - Track errors

3. **Set Up Backups:**
   - Database automatic backups
   - Manual file backups
   - Disaster recovery plan

4. **Document for Team:**
   - Access credentials
   - Deployment process
   - Troubleshooting guide

5. **Plan for Scale:**
   - Monitor usage patterns
   - Upgrade plan as needed
   - Implement caching strategies

## Support Resources

- **Render Documentation:** https://render.com/docs
- **Render Community:** https://community.render.com
- **Status Page:** https://status.render.com
- **Support:** support@render.com

## Appendix: Quick Commands

### Generate Strong Secret Key
```python
import secrets
print(secrets.token_urlsafe(32))
```

### Check Service Health
```bash
# Backend
curl https://your-backend.onrender.com/api/health

# Database (from backend shell)
python -c "from app import create_app; from models import db; app = create_app('production'); app.app_context().push(); print('✅ DB Connected')"
```

### Manual Database Migration
```bash
# From backend shell
flask db upgrade
```

### Clear Redis Cache
```bash
# From Render Redis console
FLUSHALL
```

---

## ✅ Deployment Checklist

- [ ] GitHub repository set up
- [ ] All deployment files committed
- [ ] Render account created
- [ ] Blueprint deployed (or manual services created)
- [ ] Environment variables configured
- [ ] Frontend pointing to backend URL
- [ ] Backend CORS configured for frontend
- [ ] Database initialized
- [ ] Admin user created
- [ ] Test upload and extraction
- [ ] Custom domains configured (if applicable)
- [ ] Monitoring enabled
- [ ] Backups configured
- [ ] Documentation updated with URLs

**Status: Ready to Deploy! 🚀**
