# TDIS PythonAnywhere Deployment - Quick Start Summary

## ✅ Your App is Ready for Deployment

All pre-deployment checks passed. Your TDIS application has been successfully migrated to PostgreSQL and is ready for PythonAnywhere deployment.

---

## 📦 What's Been Prepared

### Deployment Files Created
- ✅ `DEPLOYMENT_PYTHONANYWHERE.md` — Complete deployment guide
- ✅ `wsgi_pythonanywhere.py` — WSGI configuration for PythonAnywhere
- ✅ `.env.pythonanywhere.template` — Environment variables template
- ✅ `setup_pythonanywhere.sh` — Automated setup script for PythonAnywhere Bash
- ✅ `prepare_deployment.py` — Pre-deployment verification script
- ✅ `frontend/build/` — Production-ready React build

### Database Migration Status
- ✅ PostgreSQL schema ready
- ✅ Alembic migrations initialized
- ✅ Initial migration `b68706b7f82c` created
- ✅ All tables use JSONB for JSON columns
- ✅ Connection pool configured

---

## 🚀 Quick Deployment Steps (5 Minutes)

### Option A: Deploy via Git (Recommended)

**1. Push to GitHub**
```bash
cd "c:\Users\ElsieSetladi\Demo TDIS\TDIS"
git init
git add .
git commit -m "Initial commit - ready for PythonAnywhere"
git remote add origin https://github.com/YOUR_USERNAME/tdis.git
git push -u origin main
```

**2. On PythonAnywhere Bash Console**
```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/tdis.git
cd tdis

# Run automated setup
bash setup_pythonanywhere.sh

# Edit environment variables
nano .env
# Update YOUR_* placeholders with actual values
```

**3. Configure Web App**
- Go to **Web** tab → **Add new web app**
- Choose **Manual configuration** → **Python 3.11**
- Edit **WSGI configuration file**:
  - Copy content from `wsgi_pythonanywhere.py`
  - Update `YOUR_USERNAME` to your actual username

**4. Set Static Files**
- URL: `/`
  - Directory: `/home/YOUR_USERNAME/tdis/frontend/build`
- URL: `/static`
  - Directory: `/home/YOUR_USERNAME/tdis/frontend/build/static`

**5. Reload & Test**
- Click **Reload** button
- Visit: `https://YOUR_USERNAME.pythonanywhere.com`

---

### Option B: Manual Upload (If No Git)

**1. Create ZIP**
```powershell
# On Windows
Compress-Archive -Path "c:\Users\ElsieSetladi\Demo TDIS\TDIS\*" -DestinationPath "tdis-deployment.zip"
```

**2. Upload to PythonAnywhere**
- Go to **Files** tab
- Upload `tdis-deployment.zip`
- Extract in home directory
- Rename to `tdis`

**3. Continue with steps 2-5 from Option A**

---

## 🔑 Required Configuration

### Environment Variables (.env)
```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# Update these in .env:
SECRET_KEY=<generated-key>
DATABASE_URL=postgresql://USER:PASS@HOST/DB  # From Databases tab
CORS_ORIGINS=https://YOUR_USERNAME.pythonanywhere.com
UPLOAD_FOLDER=/home/YOUR_USERNAME/tdis/uploads/
LOGS_FOLDER=/home/YOUR_USERNAME/tdis/logs/
```

### PythonAnywhere Database Setup

**For PostgreSQL (Paid Account - $5/month minimum):**
1. Go to **Databases** tab
2. Click **Create a PostgreSQL database**
3. Note the connection details
4. Use in `DATABASE_URL`

**For SQLite (Free Account):**
```bash
# In .env file
DATABASE_URL=sqlite:////home/YOUR_USERNAME/tdis/instance/tender.db
```

---

## 📊 Account Requirements

| Feature | Free | Hacker ($5/mo) |
|---------|------|----------------|
| **PostgreSQL** | ❌ | ✅ |
| **MySQL** | ✅ | ✅ |
| **SQLite** | ✅ | ✅ |
| **Always-On** | ❌ | ✅ |
| **SSH Access** | ❌ | ✅ |
| **CPU Seconds** | 100/day | 1000+/day |
| **Disk Space** | 512 MB | 1 GB+ |

**Recommendation:** Use **Hacker plan ($5/month)** for PostgreSQL + full features

---

## 🧪 Testing Your Deployment

### 1. Backend API Tests
```bash
# Health check
curl https://YOUR_USERNAME.pythonanywhere.com/api/health

# Users list
curl https://YOUR_USERNAME.pythonanywhere.com/api/users

# Results list
curl https://YOUR_USERNAME.pythonanywhere.com/api/results?page=1&limit=10
```

### 2. Frontend Test
- Open: `https://YOUR_USERNAME.pythonanywhere.com`
- Check console for errors (F12)
- Test file upload
- Verify extraction works

### 3. Database Test
```bash
# In PythonAnywhere Bash console
cd ~/tdis
source venv/bin/activate
python3 -c "
from app import create_app, db
from models import User
app = create_app('production')
with app.app_context():
    users = User.query.all()
    print(f'Found {len(users)} users')
    for u in users:
        print(f'  - {u.name}: {u.email}')
"
```

---

## 🐛 Troubleshooting

### Check Logs
```bash
# In PythonAnywhere
tail -f /var/log/YOUR_USERNAME.pythonanywhere.com.error.log
tail -f /var/log/YOUR_USERNAME.pythonanywhere.com.server.log
```

### Common Issues

**1. "ModuleNotFoundError: No module named 'app'"**
```bash
# Ensure project in correct path
cd ~/tdis
source venv/bin/activate
python -c "import app; print('OK')"
```

**2. "Database connection failed"**
- Check `DATABASE_URL` in `.env`
- Verify database exists in Databases tab
- Test connection: `psql -h HOST -U USER -d DB`

**3. "CORS errors in frontend"**
- Update `CORS_ORIGINS` in `.env`
- Must match your PythonAnywhere URL exactly
- Reload web app after changes

**4. "Static files not loading"**
- Verify `frontend/build/` uploaded
- Check static file mappings in Web tab
- Clear browser cache (Ctrl+Shift+R)

**5. "Permission denied on uploads/"**
```bash
chmod 755 ~/tdis/uploads
chmod 755 ~/tdis/logs
```

---

## 📞 Support Resources

- **PythonAnywhere Help**: https://help.pythonanywhere.com/
- **Forums**: https://www.pythonanywhere.com/forums/
- **Email**: support@pythonanywhere.com
- **Your Deployment Guide**: `DEPLOYMENT_PYTHONANYWHERE.md`

---

## 🎯 Post-Deployment Checklist

- [ ] App accessible at `https://YOUR_USERNAME.pythonanywhere.com`
- [ ] `/api/health` returns healthy status
- [ ] `/api/users` returns 6 users
- [ ] Frontend loads without errors
- [ ] File upload works
- [ ] Extraction pipeline functional
- [ ] Database migrations applied
- [ ] Environment variables secured
- [ ] Logs accessible and monitored

---

## 🔒 Security Reminders

1. **Never commit `.env` with real credentials**
2. **Use strong `SECRET_KEY` (32+ chars)**
3. **Keep PostgreSQL credentials secure**
4. **Update `CORS_ORIGINS` to exact domain**
5. **Use HTTPS only (PythonAnywhere provides this by default)**
6. **Regularly backup database** (pg_dump for PostgreSQL)

---

## 💰 Cost Breakdown

**Hacker Plan ($5/month):**
- PostgreSQL database
- 1 GB disk space
- 1000 CPU seconds/day
- Always-on web apps
- SSH access
- Scheduled tasks

**Total Monthly Cost: $5 USD**

---

## 📚 Additional Resources

- Full deployment guide: `DEPLOYMENT_PYTHONANYWHERE.md`
- WSGI configuration: `wsgi_pythonanywhere.py`
- Setup script: `setup_pythonanywhere.sh`
- Environment template: `.env.pythonanywhere.template`

---

**You're all set!** 🎉

Your TDIS app is production-ready and configured for PythonAnywhere. Follow the quick deployment steps above to get it live in minutes.
