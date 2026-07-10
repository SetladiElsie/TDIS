# Tender Document Extraction - Backend

Python Flask backend for the Tender Document Extraction Application.

## Project Structure

```
backend/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── models.py             # Database models
├── routes.py             # API endpoints
├── extraction.py         # Text extraction and information extraction logic
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
├── .gitignore           # Git ignore rules
├── README.md            # This file
└── uploads/             # Uploaded tender documents (created at runtime)
```

## Setup Instructions

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### 1. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Edit the `.env` file and update the following settings:

```
FLASK_ENV=development
DATABASE_URL=sqlite:///tender.db  # Use PostgreSQL in production
SECRET_KEY=your-secret-key-here
UPLOAD_FOLDER=uploads/
```

### 4. Initialize Database

```bash
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
>>>     db.create_all()
>>> exit()
```

Or simply run the app and the database will be created automatically.

### 5. Run the Application

```bash
python app.py
```

The API will be available at: `http://localhost:5000`

## API Endpoints

### 1. Upload Document
```
POST /api/upload
Content-Type: multipart/form-data

File: <tender_document.pdf>
```

**Response:**
```json
{
  "upload_id": "uuid-string",
  "filename": "tender_document.pdf",
  "file_type": "application/pdf",
  "file_size": 2048000,
  "upload_timestamp": "2026-07-09T10:30:00",
  "status": "uploaded"
}
```

### 2. Extract Information
```
POST /api/extract
Content-Type: application/json

{
  "upload_id": "uuid-string"
}
```

**Response:**
```json
{
  "extraction_id": "uuid-string",
  "upload_id": "uuid-string",
  "status": "processing",
  "created_at": "2026-07-09T10:31:00"
}
```

### 3. Get Extraction Results
```
GET /api/results/<extraction_id>
```

**Response:**
```json
{
  "extraction_id": "uuid-string",
  "upload_id": "uuid-string",
  "status": "completed",
  "created_at": "2026-07-09T10:31:00",
  "extracted_data": {
    "tender_id": "TENDER-2026-001",
    "tender_name": "Project Name",
    "organization": "Organization Name",
    "scope_of_work": "Description...",
    "closing_date": "2026-08-15",
    "closing_date_formatted": "August 15, 2026",
    "budget": {
      "amount": 5000000,
      "currency": "USD"
    },
    "contact_email": "email@example.com",
    "contact_phone": "+1-555-0100",
    "location": "District Name",
    "document_type": "RFP",
    "estimated_duration": "24 months",
    "submission_format": "PDF or DOCX",
    "key_requirements": [...],
    "evaluation_criteria": [...],
    "deliverables": [...],
    "compulsory_documents": [...]
  },
  "confidence_scores": {
    "tender_id": 0.95,
    "closing_date": 0.92,
    "scope_of_work": 0.88,
    "budget": 0.85
  },
  "processing_time_ms": 3250
}
```

### 4. List All Results
```
GET /api/results?page=1&limit=20&search=query&status=completed
```

**Response:**
```json
{
  "total": 150,
  "page": 1,
  "limit": 20,
  "results": [...]
}
```

### 5. Export Results
```
GET /api/export/<extraction_id>?format=json

Formats: json, csv
```

### 6. Delete Result
```
DELETE /api/results/<extraction_id>
```

**Response:**
```
204 No Content
```

### 7. Health Check
```
GET /api/health
```

## Supported File Formats

- PDF (.pdf)
- Word Documents (.docx, .doc)
- Plain Text (.txt)
- Excel Spreadsheets (.xlsx)
- CSV (.csv)
- Rich Text Format (.rtf)

## Extracted Information

The system extracts the following information from tender documents:

### Core Information
- Tender ID/Reference Number
- Tender Name/Title
- Issuing Organization
- Budget/Project Value
- Closing Date

### Detailed Information
- Scope of Work
- Project Location
- Project Duration
- Evaluation Criteria
- Deliverables
- Compulsory Documents Required
- Contact Information
- Submission Format

## Database

### Default Database
The application uses SQLite by default (`tender.db`). For production, use PostgreSQL:

```
postgresql://username:password@localhost:5432/tender_db
```

### Models
- **Upload**: Stores uploaded document metadata
- **Extraction**: Stores extracted tender information

## Configuration

Edit `config.py` to customize:
- Database URL
- Upload folder path
- Maximum file size
- Allowed file extensions
- CORS settings

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK` - Successful request
- `201 Created` - Resource created
- `204 No Content` - Successful deletion
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Resource not found
- `415 Unsupported Media Type` - Unsupported file format
- `500 Internal Server Error` - Server error

Error responses include:
```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "details": "Additional details (if applicable)"
}
```

## Testing

To test the API, you can use:

1. **cURL**
```bash
curl -X POST http://localhost:5000/api/upload -F "file=@document.pdf"
```

2. **Postman**
- Create a POST request to `http://localhost:5000/api/upload`
- Add file in Form Data
- Send

3. **Python Requests**
```python
import requests

# Upload
with open('document.pdf', 'rb') as f:
    response = requests.post('http://localhost:5000/api/upload', files={'file': f})
    upload_id = response.json()['upload_id']

# Extract
response = requests.post('http://localhost:5000/api/extract', json={'upload_id': upload_id})
extraction_id = response.json()['extraction_id']

# Get Results
response = requests.get(f'http://localhost:5000/api/results/{extraction_id}')
print(response.json())
```

## Troubleshooting

### Database Lock Error
If you get a database lock error:
```bash
rm tender.db
python app.py
```

### Port Already in Use
Change the port in `app.py`:
```python
app.run(host='0.0.0.0', port=5001)
```

### Missing Dependencies
Reinstall dependencies:
```bash
pip install -r requirements.txt --force-reinstall
```

## Deployment

For production deployment:

1. Set `FLASK_ENV=production`
2. Use PostgreSQL database
3. Update `SECRET_KEY` in `.env`
4. Use a production WSGI server (Gunicorn, uWSGI)
5. Enable HTTPS

### Docker Deployment

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]
```

```bash
docker build -t tender-api .
docker run -p 5000:5000 tender-api
```

## Performance Tips

1. Use PostgreSQL instead of SQLite
2. Enable request caching
3. Use asynchronous processing (Celery) for large files
4. Implement database indexing
5. Add pagination to list endpoints

## Future Enhancements

- [ ] Async file processing with Celery
- [ ] Advanced NLP for better extraction accuracy
- [ ] Machine Learning models for pattern recognition
- [ ] Support for more file formats
- [ ] Batch document processing
- [ ] Extraction history and versioning
- [ ] User authentication and authorization
- [ ] Advanced search and filtering

## Support

For issues or questions, contact the development team.

---

**Version:** 1.0.0  
**Last Updated:** July 9, 2026
