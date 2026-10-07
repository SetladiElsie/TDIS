# TDIS Production Deployment Checklist

## Pre-Deployment Cleanup

### ✅ Completed

- [x] Remove temporary login credentials from Login.js
- [x] Add environment variable control for default user seeding
- [x] Create admin user creation script (`create_admin.py`)
- [x] Update .gitignore to exclude sensitive files
- [x] Remove description from manifest.json
- [x] Increase favicon size for better visibility

### 🔧 Required Before Production Deploy

#### 1. Clean Test Data

```bash
# Remove test uploads (CAUTION: This deletes all uploaded files)
rm -rf uploads/*
mkdir uploads/.gitkeep

# Or on Windows:
Remove-Item -Recurse -Force uploads\*
New-Item -ItemType File -Path uploads\.gitkeep
```

#### 2. Clean Database (Optional - Start Fresh)

```bash
# Remove development database
rm instance/tender.db

# Or on Windows:
Remove-Item instance\tender.db
```

#### 3. Update Environment Variables

Create production `.env` file with:

```bash
# ── Application ────────────────────────────────────────────────
FLASK_ENV=production
SECRET_KEY=<generate-new-secret-key>

# ── Development Settings ───────────────────────────────────────
# MUST be false for production
SEED_DEFAULT_USERS=false

# ── Database (provided by Render) ──────────────────────────────
# DATABASE_URL will be set automatically by Render PostgreSQL

# ── Redis (provided by Render) ─────────────────────────────────
# REDIS_URL will be set automatically by Render Redis

# ── CORS ───────────────────────────────────────────────────────
CORS_ORIGINS=https://your-frontend-domain.onrender.com

# ── Email (Optional) ───────────────────────────────────────────
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=SG.your_api_key
MAIL_FROM=noreply@tia-solutions.co.za

# ── File Upload ────────────────────────────────────────────────
UPLOAD_FOLDER=/var/data/uploads/
LOGS_FOLDER=/var/data/logs/
MAX_FILE_SIZE=524288000

# ── Security ───────────────────────────────────────────────────
ENABLE_FILE_MIME_VALIDATION=True
ENABLE_VIRUS_SCANNING=False

# ── Logging ────────────────────────────────────────────────────
LOG_LEVEL=INFO
LOG_TO_STDOUT=True
```

#### 4. Generate New SECRET_KEY

```python
# Run this to generate a new secret key
python -c "import secrets; print(secrets.token_hex(32))"
```

#### 5. Update Frontend URLs

Update `email_service.py` (lines 113 and 223):

```python
# Change from:
<a href="http://localhost:3000" class="button">Login to Portal</a>

# To:
<a href="https://your-app.onrender.com" class="button">Login to Portal</a>
```

Update `frontend/src/services/api.js`:

```javascript
// Ensure API_URL points to production backend
const API_URL = process.env.REACT_APP_API_URL || 'https://your-backend.onrender.com/api';
```

#### 6. Create First Admin User

After deployment, run:

```bash
python create_admin.py
```

This will interactively prompt for:
- Admin name
- Admin email
- Admin password (with validation)

---

## Deployment Steps

### Option 1: Deploy to Render (Recommended)

#### Backend Deployment

1. **Push to Git:**
   ```bash
   git add .
   git commit -m "Production ready"
   git push origin main
   ```

2. **Configure Render:**
   - Go to Render Dashboard
   - Create PostgreSQL database
   - Create Redis service
   - Create Web Service (backend)
   - Point to your repository
   - Use `render.yaml` blueprint

3. **Set Environment Variables:**
   ```
   FLASK_ENV=production
   SECRET_KEY=<your-generated-key>
   SEED_DEFAULT_USERS=false
   CORS_ORIGINS=https://your-frontend.onrender.com
   ```

4. **Deploy:**
   - Render will automatically deploy from `render.yaml`
   - Wait for build to complete
   - Check logs for errors

5. **Create Admin User:**
   ```bash
   # SSH into Render shell or use local with production DATABASE_URL
   python create_admin.py
   ```

#### Frontend Deployment

1. **Update Environment:**
   Create `frontend/.env.production`:
   ```
   REACT_APP_API_URL=https://your-backend.onrender.com/api
   ```

2. **Build:**
   ```bash
   cd frontend
   npm run build
   ```

3. **Deploy to Render:**
   - Create Static Site on Render
   - Point to `frontend` directory
   - Build command: `npm install && npm run build`
   - Publish directory: `build`

### Option 2: Deploy to Other Platform

See `RENDER_DEPLOYMENT_GUIDE.md` for detailed instructions.

---

## Post-Deployment Verification

### ✅ Backend Checks

```bash
# Test health endpoint
curl https://your-backend.onrender.com/api/health

# Test authentication
curl -X POST https://your-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"YourPassword123!"}'
```

### ✅ Frontend Checks

1. Open `https://your-frontend.onrender.com`
2. Verify login page loads
3. Test login with admin credentials
4. Upload a test tender document
5. Verify extraction works
6. Test user management
7. Test password reset flow

### ✅ Email Checks (if configured)

1. Create a test user with temporary password
2. Check if email is received
3. Verify email formatting
4. Test password reset email

### ✅ Security Checks

- [ ] HTTPS enabled
- [ ] CORS configured correctly
- [ ] No default credentials in code
- [ ] SECRET_KEY is unique and secure
- [ ] Database backups configured
- [ ] File upload limits set
- [ ] Error messages don't expose sensitive info

---

## Production Environment Variables Summary

| Variable | Required | Description |
|----------|----------|-------------|
| `FLASK_ENV` | Yes | Set to `production` |
| `SECRET_KEY` | Yes | Unique secret key (64 chars) |
| `SEED_DEFAULT_USERS` | Yes | Set to `false` |
| `DATABASE_URL` | Auto | PostgreSQL connection (Render provides) |
| `REDIS_URL` | Auto | Redis connection (Render provides) |
| `CORS_ORIGINS` | Yes | Frontend domain(s) |
| `MAIL_SERVER` | Optional | SMTP server for emails |
| `MAIL_USERNAME` | Optional | SMTP username |
| `MAIL_PASSWORD` | Optional | SMTP password/API key |
| `MAIL_FROM` | Optional | From email address |
| `UPLOAD_FOLDER` | Yes | `/var/data/uploads/` |
| `LOG_LEVEL` | Yes | `INFO` or `WARNING` |

---

## Rollback Plan

If deployment fails:

1. **Revert Code:**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Restore Database:**
   - Use Render's database backups
   - Or restore from your backup

3. **Check Logs:**
   ```bash
   # Render dashboard → Service → Logs
   # Look for error messages
   ```

---

## Maintenance

### Regular Tasks

- **Weekly:** Review logs for errors
- **Monthly:** Update dependencies
- **Quarterly:** Security audit
- **As needed:** Database backups

### Monitoring

Set up monitoring for:
- Uptime (Render provides basic monitoring)
- Error rates
- Response times
- Storage usage

---

## Support Contacts

- **Render Support:** https://render.com/docs
- **Application Issues:** Check logs first
- **Database Issues:** Verify DATABASE_URL
- **Email Issues:** Check MAIL_* configuration

---

## Security Best Practices

✅ **Implemented:**
- Environment variables for secrets
- Password hashing (bcrypt)
- JWT token authentication
- CORS protection
- SQL injection protection (SQLAlchemy ORM)
- File upload validation
- Security headers

⚠️ **Recommendations:**
- Enable HTTPS (Render provides free SSL)
- Set up rate limiting
- Enable virus scanning (if available)
- Regular security audits
- Monitor for suspicious activity
- Keep dependencies updated

---

## Troubleshooting Common Issues

### "No admin users found"

**Solution:** Run `python create_admin.py` to create first admin

### "Database connection failed"

**Solution:** Check `DATABASE_URL` environment variable

### "CORS error"

**Solution:** Verify `CORS_ORIGINS` includes your frontend domain

### "File upload fails"

**Solution:** Check `UPLOAD_FOLDER` permissions and `MAX_FILE_SIZE`

### "Email not sending"

**Solution:** Verify MAIL_* variables and check logs

---

**Last Updated:** January 2025
**Version:** 1.0
**Status:** Production Ready ✅
