# PythonAnywhere Deployment Guide for TDIS

## Prerequisites

1. **PythonAnywhere Account** — Sign up at https://www.pythonanywhere.com
2. **Account Type** — Paid account required for:
   - PostgreSQL database access
   - Custom domains
   - Always-on tasks
   - SSH access
3. **Free Account Limitations**:
   - Only MySQL available (not PostgreSQL)
   - Whitelist-only external API access
   - Limited CPU seconds

## Important: Database Choice

### Option A: Use PostgreSQL (Recommended - Requires Paid Account)
Your app is now configured for PostgreSQL with JSONB columns. To use this on PythonAnywhere:
- **Minimum Plan**: Hacker ($5/month)
- PostgreSQL available on all paid plans
- Keeps all JSONB performance benefits

### Option B: Switch Back to SQLite (Free Account Compatible)
If using the free tier:
- Revert `DATABASE_URL` in `.env` to SQLite
- No schema changes needed (models already support both)
- Loses JSONB indexing benefits

## Deployment Steps

### 1. Upload Code to PythonAnywhere

**Option 1: Via GitHub (Recommended)**
```bash
# On your local machine, commit and push to GitHub
git init
git add .
git commit -m "Initial commit for PythonAnywhere deployment"
git remote add origin https://github.com/YOUR_USERNAME/tdis.git
git push -u origin main

# On PythonAnywhere Bash console
git clone https://github.com/YOUR_USERNAME/tdis.git
cd tdis
```

**Option 2: Direct Upload**
- Use PythonAnywhere's "Files" tab
- Upload ZIP of your project
- Extract in your home directory

### 2. Set Up Virtual Environment

```bash
# In PythonAnywhere Bash console
cd ~/tdis
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Database

**For PostgreSQL (Paid Account):**
```bash
# In PythonAnywhere Bash console
# Create database via PythonAnywhere Databases tab first
# Then note the connection details

# Update .env with PythonAnywhere PostgreSQL credentials
nano .env
```

Update `DATABASE_URL`:
```
DATABASE_URL=postgresql://YOUR_PA_USERNAME:YOUR_DB_PASSWORD@YOUR_PA_USERNAME-XXXXX.postgres.pythonanywhere-services.com/YOUR_DB_NAME
```

**For SQLite (Free Account):**
```bash
# .env file
DATABASE_URL=sqlite:///home/YOUR_USERNAME/tdis/instance/tender.db
```

### 4. Run Database Migrations

```bash
cd ~/tdis
source venv/bin/activate
export FLASK_APP=app.py

# Run migrations
flask db upgrade

# Verify tables created
python3 -c "from app import create_app, db; app = create_app(); app.app_context().push(); print(db.engine.table_names())"
```

### 5. Configure WSGI Application

Go to **Web** tab → **Add a new web app** → **Manual configuration** → **Python 3.11**

Edit the WSGI configuration file (click on the link):

```python
# ===================================================================
# WSGI configuration for PythonAnywhere
# ===================================================================
import sys
import os

# Add your project directory to path
project_home = '/home/YOUR_USERNAME/tdis'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Activate virtual environment
activate_this = os.path.join(project_home, 'venv/bin/activate_this.py')
with open(activate_this) as file:
    exec(file.read(), dict(__file__=activate_this))

# Import Flask app
from app import create_app
application = create_app('production')
```

### 6. Set Environment Variables

In **Web** tab, scroll to **Environment variables**:

```
FLASK_ENV=production
SECRET_KEY=your-super-secret-production-key-change-this
DATABASE_URL=postgresql://... (or sqlite://...)
UPLOAD_FOLDER=/home/YOUR_USERNAME/tdis/uploads
LOGS_FOLDER=/home/YOUR_USERNAME/tdis/logs
```

### 7. Configure Static Files (for React Frontend)

**Build React Frontend Locally:**
```bash
# On your local machine
cd frontend
npm run build
# This creates frontend/build/ directory
```

**Upload to PythonAnywhere:**
- Upload the `frontend/build/` folder to `/home/YOUR_USERNAME/tdis/frontend/build/`

**Configure Static Files in Web Tab:**
- URL: `/`
- Directory: `/home/YOUR_USERNAME/tdis/frontend/build`

- URL: `/static`
- Directory: `/home/YOUR_USERNAME/tdis/frontend/build/static`

### 8. Configure CORS for Production

Update `.env` on PythonAnywhere:
```
CORS_ORIGINS=https://YOUR_USERNAME.pythonanywhere.com
```

### 9. Create Required Directories

```bash
mkdir -p ~/tdis/uploads
mkdir -p ~/tdis/logs
chmod 755 ~/tdis/uploads
chmod 755 ~/tdis/logs
```

### 10. Reload Web App

Click **Reload YOUR_USERNAME.pythonanywhere.com** button in Web tab.

## Testing the Deployment

1. **Backend API**: `https://YOUR_USERNAME.pythonanywhere.com/api/health`
2. **Frontend**: `https://YOUR_USERNAME.pythonanywhere.com/`
3. **Users endpoint**: `https://YOUR_USERNAME.pythonanywhere.com/api/users`

## Troubleshooting

### Check Error Logs
- **Web** tab → **Log files** section
- `/var/log/YOUR_USERNAME.pythonanywhere.com.error.log`
- `/var/log/YOUR_USERNAME.pythonanywhere.com.server.log`

### Common Issues

**1. ModuleNotFoundError**
```bash
# Ensure all packages installed in venv
source ~/tdis/venv/bin/activate
pip install -r requirements.txt
```

**2. Database Connection Errors**
- Check `DATABASE_URL` in environment variables
- For PostgreSQL: Verify credentials in Databases tab
- Test connection: `psql -h HOST -U USER -d DATABASE`

**3. Permission Errors**
```bash
chmod -R 755 ~/tdis/uploads
chmod -R 755 ~/tdis/logs
```

**4. Static Files Not Loading**
- Verify `frontend/build/` uploaded correctly
- Check static file mappings in Web tab
- Clear browser cache

**5. CORS Errors**
- Update `CORS_ORIGINS` to match your PythonAnywhere URL
- Reload web app after changing environment variables

## Scheduled Tasks (Paid Accounts Only)

For cleanup/maintenance:
1. Go to **Tasks** tab
2. Schedule daily task:
```bash
cd /home/YOUR_USERNAME/tdis && source venv/bin/activate && python manage.py cleanup_uploads
```

## Limitations on Free Tier

- **CPU seconds**: 100 seconds/day
- **Disk space**: 512 MB
- **Database**: MySQL only (no PostgreSQL)
- **Always-on**: No (site sleeps after inactivity)
- **External API**: Whitelist required

## Production Checklist

- [ ] Generate strong `SECRET_KEY`
- [ ] Update `CORS_ORIGINS` to production domain
- [ ] Set `FLASK_ENV=production`
- [ ] Use PostgreSQL for better performance (paid tier)
- [ ] Set up database backups
- [ ] Configure error monitoring
- [ ] Test all API endpoints
- [ ] Test file upload functionality
- [ ] Verify extraction pipeline works
- [ ] Set up scheduled cleanup tasks

## Cost Estimate

| Plan | Price | Features |
|------|-------|----------|
| **Beginner** | Free | MySQL, SQLite, limited CPU |
| **Hacker** | $5/month | PostgreSQL, more CPU, SSH |
| **Web Dev** | $12/month | More resources, multiple web apps |

## Support

- PythonAnywhere Forums: https://www.pythonanywhere.com/forums/
- Help Pages: https://help.pythonanywhere.com/
- Email: support@pythonanywhere.com

## Alternative: Use a .pythonanywhere.com Subdomain

Your app will be available at:
- `https://YOUR_USERNAME.pythonanywhere.com`

Custom domains require paid accounts.
