# Render Deployment Checklist

## ✅ Pre-Deployment (Complete)

- [x] Fixed requirements.txt (removed invalid python version)
- [x] Updated render.yaml (added SEED_DEFAULT_USERS=false)
- [x] Configured build script permissions
- [x] Removed test credentials from login page
- [x] Updated favicon (large and visible)
- [x] Changed browser title to "Tender Extraction"
- [x] Created admin user script
- [x] Configured MCP server for Render

## 📋 Deployment Steps

### Step 1: Push to Git Repository

- [ ] Ensure you have a GitHub/GitLab account
- [ ] Create repository (if not exists): https://github.com/new
- [ ] Add remote:
  ```bash
  git remote add origin https://github.com/yourusername/tdis.git
  ```
- [ ] Push code:
  ```bash
  .\deploy-to-render.ps1
  ```
  Or manually:
  ```bash
  git add .
  git commit -m "Ready for Render deployment"
  git push origin main
  ```

### Step 2: Deploy to Render

**Option A: MCP (Easiest)**
- [ ] Restart Kiro: `Ctrl+Shift+P` → Reload Window
- [ ] Set workspace: `Set my Render workspace to [name]`
- [ ] Deploy: `Deploy my TDIS application to Render`

**Option B: Blueprint (Automated)**
- [ ] Go to https://dashboard.render.com
- [ ] Click "New +" → "Blueprint"
- [ ] Connect your repository
- [ ] Click "Apply"
- [ ] Wait for deployment (~30-45 min)

**Option C: Manual (Step-by-Step)**
- [ ] See `RENDER_DEPLOY_NOW.md` Method 2

### Step 3: Create Admin User

- [ ] Wait for backend to finish deploying
- [ ] Go to backend service → Shell tab
- [ ] Run: `python create_admin.py`
- [ ] Enter admin details:
  - Name: _____________
  - Email: _____________
  - Password: _____________

### Step 4: Test Deployment

- [ ] Test backend health:
  ```bash
  curl https://tdis-backend.onrender.com/api/health
  ```
- [ ] Visit frontend: https://tdis-frontend.onrender.com
- [ ] Login with admin credentials
- [ ] Upload a test tender document
- [ ] Verify extraction works
- [ ] Test user creation
- [ ] Test password reset

### Step 5: Optional Enhancements

- [ ] Configure custom domain
- [ ] Enable email notifications (SendGrid)
- [ ] Set up monitoring alerts
- [ ] Configure backups schedule
- [ ] Add team members

## 🔍 Verification Checklist

### Backend Verification
- [ ] Service status: Green (running)
- [ ] Health endpoint responds: `/api/health`
- [ ] Database connected (no errors in logs)
- [ ] Redis connected (or gracefully degraded)
- [ ] File uploads work
- [ ] Authentication works

### Frontend Verification
- [ ] Site loads without errors
- [ ] Login page displays correctly
- [ ] Favicon visible in browser tab
- [ ] Title shows "Tender Extraction"
- [ ] API calls reach backend
- [ ] Navigation menu works
- [ ] Purple theme applied

### Database Verification
- [ ] Connection successful
- [ ] Tables created
- [ ] Admin user exists
- [ ] Data persists across deploys

### Security Verification
- [ ] HTTPS enabled (automatic)
- [ ] CORS configured correctly
- [ ] No test credentials visible
- [ ] SECRET_KEY is strong
- [ ] File upload limits enforced

## 📊 Post-Deployment Monitoring

### First 24 Hours
- [ ] Check for errors in logs
- [ ] Monitor CPU/memory usage
- [ ] Verify database performance
- [ ] Test all major features
- [ ] Check response times

### First Week
- [ ] Review error logs daily
- [ ] Monitor disk usage
- [ ] Test backup restoration
- [ ] Verify email notifications (if enabled)
- [ ] Check for performance issues

### Ongoing
- [ ] Weekly log review
- [ ] Monthly dependency updates
- [ ] Quarterly security audit
- [ ] Database backup verification

## 🆘 Troubleshooting

### Build Fails
- [ ] Check build logs in Events tab
- [ ] Verify requirements.txt is valid
- [ ] Check NLTK download didn't timeout
- [ ] Clear build cache and retry

### Backend Won't Start
- [ ] Check environment variables are set
- [ ] Verify DATABASE_URL is correct
- [ ] Check for port conflicts
- [ ] Review error logs

### Frontend Can't Connect
- [ ] Verify REACT_APP_API_URL
- [ ] Check CORS_ORIGINS in backend
- [ ] Ensure backend is running
- [ ] Check network tab in browser DevTools

### Database Issues
- [ ] Verify database is running
- [ ] Check connection string
- [ ] Ensure same region as backend
- [ ] Review database logs

## 📞 Support Resources

- **Render Docs:** https://render.com/docs
- **Render Status:** https://status.render.com
- **Support Tickets:** https://render.com/support
- **Community:** https://community.render.com

## 📝 Notes

Deployment Date: _____________

Backend URL: _____________

Frontend URL: _____________

Admin Email: _____________

Issues Encountered:
_____________________________________________
_____________________________________________
_____________________________________________

Resolution:
_____________________________________________
_____________________________________________
_____________________________________________

## ✅ Deployment Complete!

- [ ] All services deployed successfully
- [ ] Admin user created and tested
- [ ] Application fully functional
- [ ] Monitoring configured
- [ ] Team notified
- [ ] Documentation updated

**Congratulations! Your TDIS application is now live on Render! 🎉**
