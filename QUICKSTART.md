# Quick Start Guide - Backend

Get the Tender Document Extraction API running in minutes!

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

## Quick Start (Windows)

### 1. Clone/Setup
```bash
cd path/to/TDIS
```

### 2. Run Setup Script
```bash
setup-dev.bat
```

### 3. Start the Server
```bash
venv\Scripts\activate.bat
python app.py
```

The API will be running at: **http://localhost:5000**

---

## Quick Start (macOS/Linux)

### 1. Clone/Setup
```bash
cd path/to/TDIS
chmod +x setup-dev.sh
```

### 2. Run Setup Script
```bash
./setup-dev.sh
```

### 3. Start the Server
```bash
source venv/bin/activate
python app.py
```

The API will be running at: **http://localhost:5000**

---

## Manual Setup (If Scripts Don't Work)

### 1. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize Database
```bash
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
>>>     db.create_all()
>>> exit()
```

### 4. Create Uploads Directory
```bash
mkdir uploads
```

### 5. Run the Server
```bash
python app.py
```

---

## API Endpoints

Once the server is running, you can access these endpoints:

### Health Check
```bash
curl http://localhost:5000/api/health
```

### Upload Document
```bash
curl -X POST -F "file=@document.pdf" http://localhost:5000/api/upload
```

### Extract Information
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"upload_id": "uuid-here"}' \
  http://localhost:5000/api/extract
```

### Get Results
```bash
curl http://localhost:5000/api/results/extraction-id-here
```

---

## Using the Test Client

Test the API with the included test client:

```bash
python test_client.py path/to/tender_document.pdf
```

---

## Development Commands

### Using manage.py

```bash
# Show database statistics
python manage.py show-stats

# Initialize database
python manage.py init-db

# Reset database
python manage.py reset-db

# Clean up old uploads
python manage.py cleanup-uploads

# Run server with options
python manage.py run --host 0.0.0.0 --port 5000 --debug
```

---

## Common Issues

### Issue: Port 5000 Already in Use
```bash
# Change port when running
python app.py
# Then modify the port in the app.run() call

# Or use manage.py
python manage.py run --port 5001
```

### Issue: Database Lock Error
```bash
# Delete and recreate database
rm tender.db
python app.py
```

### Issue: Module Not Found Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: Permission Denied (Linux/macOS)
```bash
# Make setup script executable
chmod +x setup-dev.sh
./setup-dev.sh
```

---

## Testing with Postman

1. **Download Postman**: https://www.postman.com/downloads/
2. **Import Collection**: Create a new request with these details:

**Upload:**
- Method: POST
- URL: http://localhost:5000/api/upload
- Body: form-data
- Add field "file" (type: File) with your PDF

**Extract:**
- Method: POST
- URL: http://localhost:5000/api/extract
- Body: raw JSON
```json
{
  "upload_id": "your-upload-id-here"
}
```

**Get Results:**
- Method: GET
- URL: http://localhost:5000/api/results/your-extraction-id-here

---

## Testing with Python

```python
import requests

# Upload
with open('document.pdf', 'rb') as f:
    r = requests.post('http://localhost:5000/api/upload', files={'file': f})
    upload_id = r.json()['upload_id']
    print(f"Upload ID: {upload_id}")

# Extract
r = requests.post('http://localhost:5000/api/extract', 
                 json={'upload_id': upload_id})
extraction_id = r.json()['extraction_id']
print(f"Extraction ID: {extraction_id}")

# Get Results
r = requests.get(f'http://localhost:5000/api/results/{extraction_id}')
print(r.json())
```

---

## Testing with cURL

```bash
# Upload file
curl -X POST -F "file=@document.pdf" \
  http://localhost:5000/api/upload

# Extract (replace upload_id)
curl -X POST -H "Content-Type: application/json" \
  -d '{"upload_id":"upload_id_here"}' \
  http://localhost:5000/api/extract

# Get results (replace extraction_id)
curl http://localhost:5000/api/results/extraction_id_here

# List results
curl http://localhost:5000/api/results

# Export as CSV
curl http://localhost:5000/api/export/extraction_id_here?format=csv
```

---

## Environment Variables

Edit `.env` to customize:

```
FLASK_ENV=development
DATABASE_URL=sqlite:///tender.db
UPLOAD_FOLDER=uploads/
SECRET_KEY=your-secret-key
```

---

## Next Steps

1. **Start the Frontend**: Navigate to the frontend folder and start React
2. **Integrate with Frontend**: Update frontend API URL to http://localhost:5000/api
3. **Deploy**: Use Docker or deploy to production server

---

## Need Help?

- Check the full README.md for detailed documentation
- Review code comments in extraction.py for extraction logic
- Check routes.py for API endpoint implementations
- Review models.py for database schema

---

**Happy Coding!** 🚀
