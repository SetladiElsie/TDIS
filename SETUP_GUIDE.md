# Complete Setup Guide - Tender Document Extraction Application

Complete instructions to get the full-stack Tender Document Extraction Application running.

## 📋 Prerequisites

- **Python** 3.9+ (for backend)
- **Node.js** 14+ and npm (for frontend)
- **Git** (optional, for version control)

## 🚀 Quick Start (5 Minutes)

### Terminal 1 - Backend Setup

```bash
# Navigate to backend
cd TDIS

# Windows Setup
setup-dev.bat

# macOS/Linux Setup
chmod +x setup-dev.sh
./setup-dev.sh

# Activate virtual environment (Windows)
venv\Scripts\activate.bat

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Start backend server
python app.py
```

**Expected Output:**
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### Terminal 2 - Frontend Setup

```bash
# Navigate to frontend (in a new terminal)
cd TDIS/frontend

# Install dependencies
npm install

# Start development server
npm start
```

**Expected Output:**
```
Compiled successfully!
You can now view tender-document-extraction-frontend in the browser.
  Local:            http://localhost:3000
```

### Terminal 3 - Open Application

Visit: **http://localhost:3000**

---

## 📁 Project Structure

```
TDIS/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── routes.py
│   ├── extraction.py
│   ├── requirements.txt
│   ├── manage.py
│   ├── test_client.py
│   └── ... (other backend files)
│
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   ├── .env
│   └── ... (other frontend files)
│
├── documentation.md
└── SETUP_GUIDE.md (this file)
```

---

## ✅ Step-by-Step Setup

### Step 1: Backend Setup (Python)

#### 1.1 Create Virtual Environment

```bash
cd TDIS

# Windows
python -m venv venv
venv\Scripts\activate.bat

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 1.2 Install Dependencies

```bash
pip install -r requirements.txt
```

**Installation takes ~2-3 minutes**

#### 1.3 Configure Environment

Edit `TDIS/.env`:
```
FLASK_ENV=development
DATABASE_URL=sqlite:///tender.db
SECRET_KEY=your-secret-key-here
UPLOAD_FOLDER=uploads/
```

#### 1.4 Initialize Database

```bash
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
>>>     db.create_all()
>>> exit()
```

#### 1.5 Start Backend

```bash
python app.py
```

✅ Backend running on http://localhost:5000

---

### Step 2: Frontend Setup (React)

#### 2.1 Install Node Modules

```bash
cd TDIS/frontend
npm install
```

**Installation takes ~2-3 minutes**

#### 2.2 Configure Environment

Edit `TDIS/frontend/.env`:
```
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_API_TIMEOUT=30000
```

#### 2.3 Start Frontend

```bash
npm start
```

✅ Frontend running on http://localhost:3000

---

## 🧪 Testing the Application

### Test 1: Health Check

```bash
# In another terminal
curl http://localhost:5000/api/health

# Expected response:
# {"status": "healthy", "timestamp": "..."}
```

### Test 2: Upload & Extract

Using Python:
```bash
cd TDIS
python test_client.py sample_tender.pdf
```

Using cURL:
```bash
# Upload
curl -X POST -F "file=@document.pdf" http://localhost:5000/api/upload

# Extract (replace upload_id)
curl -X POST -H "Content-Type: application/json" \
  -d '{"upload_id":"your_upload_id"}' \
  http://localhost:5000/api/extract
```

### Test 3: UI Testing

1. Open http://localhost:3000 in browser
2. Upload a PDF or DOCX file
3. Wait for extraction
4. View results
5. Test search and export

---

## 🔧 Configuration

### Backend Configuration (`TDIS/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | development | Environment mode |
| `DATABASE_URL` | sqlite:///tender.db | Database connection |
| `UPLOAD_FOLDER` | uploads/ | File upload directory |
| `SECRET_KEY` | dev-key | Secret for sessions |
| `CELERY_BROKER_URL` | redis://localhost:6379 | Message broker |

### Frontend Configuration (`TDIS/frontend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `REACT_APP_API_URL` | http://localhost:5000/api | Backend API URL |
| `REACT_APP_API_TIMEOUT` | 30000 | API timeout (ms) |

---

## 🐛 Troubleshooting

### Backend Issues

#### Port 5000 Already in Use
```bash
# Change port in app.py
app.run(host='0.0.0.0', port=5001)

# Or use manage.py
python manage.py run --port 5001
```

#### Database Lock Error
```bash
rm tender.db
python app.py
```

#### Module Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### API Not Responding
- Verify backend is running: `python app.py`
- Check port is 5000: `netstat -an | grep 5000`
- Check firewall settings

### Frontend Issues

#### Port 3000 Already in Use
```bash
PORT=3001 npm start
```

#### "API is not running" Error
- Start backend: `python app.py`
- Check `REACT_APP_API_URL` in .env
- Refresh browser

#### Blank Screen
- Open DevTools (F12)
- Check Console tab for errors
- Clear cache: Ctrl+Shift+Delete
- Restart: `npm start`

#### Module Installation Issues
```bash
# Clear cache and reinstall
npm cache clean --force
rm -rf node_modules
npm install
npm start
```

---

## 📊 File Size Limits

- **Maximum file size**: 50 MB
- **Recommended**: 5-10 MB for faster processing
- **Supported formats**: PDF, DOCX, DOC, TXT, XLSX, CSV

---

## 🔐 Security Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Use PostgreSQL instead of SQLite in production
- [ ] Enable HTTPS
- [ ] Set proper CORS origins
- [ ] Implement authentication
- [ ] Set up rate limiting
- [ ] Enable file scanning

---

## 🚀 Production Deployment

### Using Docker Compose

```bash
cd TDIS
docker-compose up --build
```

Services will run on:
- Frontend: http://localhost:3000
- Backend: http://localhost:5000
- Database: PostgreSQL on port 5432
- pgAdmin: http://localhost:5050

### Manual Deployment

#### Backend (using Gunicorn)
```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 app:create_app()
```

#### Frontend (static hosting)
```bash
npm run build
# Deploy build/ folder to web server (Nginx, Apache, etc.)
```

---

## 📈 Performance Optimization

### Backend
- Use PostgreSQL instead of SQLite
- Enable caching (Redis)
- Use Celery for async tasks
- Add indexing to database
- Monitor with tools like New Relic

### Frontend
- Use production build: `npm run build`
- Enable gzip compression
- Use CDN for assets
- Implement lazy loading
- Monitor with tools like Sentry

---

## 📚 Additional Commands

### Backend Management

```bash
# Initialize database
python manage.py init-db

# Reset database
python manage.py reset-db

# Show statistics
python manage.py show-stats

# Clean old uploads
python manage.py cleanup-uploads

# Run with options
python manage.py run --host 0.0.0.0 --port 5000 --debug
```

### Frontend Commands

```bash
# Development
npm start

# Production build
npm run build

# Run tests
npm test

# Eject (cannot be reversed)
npm eject
```

---

## 📞 Support

### Getting Help
1. Check relevant README files:
   - `TDIS/README.md` (Backend)
   - `TDIS/frontend/README.md` (Frontend)
   - `TDIS/frontend/QUICKSTART.md` (Quick Start)

2. Review console logs for errors

3. Check configuration files:
   - `.env` files for both backend and frontend

### Common Resources
- **API Documentation**: Visit http://localhost:5000 (shows endpoints)
- **Backend Logs**: Console output when running `python app.py`
- **Frontend Logs**: Browser DevTools (F12)

---

## ✨ Features Overview

### Supported Document Formats
✅ PDF (.pdf)  
✅ Word (.docx, .doc)  
✅ Text (.txt)  
✅ Excel (.xlsx)  
✅ CSV (.csv)  

### Extracted Information
✅ Tender ID  
✅ Tender Name  
✅ Organization  
✅ Scope of Work  
✅ Closing Date  
✅ Budget  
✅ Contact Info  
✅ Location  
✅ Evaluation Criteria  
✅ Deliverables  
✅ Required Documents  
✅ And more...

### Application Features
✅ Drag & drop upload  
✅ Real-time extraction  
✅ Search functionality  
✅ Status filtering  
✅ Export to JSON/CSV  
✅ Pagination  
✅ Responsive design  
✅ Error handling  
✅ Toast notifications  

---

## 🎯 Next Steps

### 1. Development
- Customize extraction logic in `TDIS/extraction.py`
- Add new fields in `TDIS/models.py`
- Extend frontend components in `TDIS/frontend/src/components/`

### 2. Testing
- Use test_client.py for API testing
- Test with various document formats
- Test on different devices/browsers

### 3. Deployment
- Follow production deployment guide
- Set up database backups
- Configure monitoring and alerts
- Set up CI/CD pipeline

### 4. Scaling
- Implement Celery for async processing
- Add caching layer (Redis)
- Use PostgreSQL for production
- Implement load balancing

---

## 📋 Checklist

Setup Verification:
- [ ] Python 3.9+ installed
- [ ] Node.js 14+ installed
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Backend running on port 5000
- [ ] Frontend running on port 3000
- [ ] Can access http://localhost:3000
- [ ] API health check passes
- [ ] Can upload documents
- [ ] Can view results
- [ ] Can export data

---

## 📞 Getting Help

### Logs to Check
1. **Backend Console**: Running `python app.py`
2. **Frontend Console**: Browser DevTools (F12)
3. **Network Tab**: Check API calls
4. **Application Tab**: Check stored data

### Common Errors
- "API is not running" → Start backend
- "Port already in use" → Use different port
- "Module not found" → Reinstall dependencies
- "Database locked" → Delete .db file and restart
- "CORS error" → Check backend CORS settings

---

**Version**: 1.0.0  
**Last Updated**: July 9, 2026  
**Status**: Complete and Ready for Use

---

🎉 **Congratulations! You're ready to use the Tender Document Extraction Application!**
