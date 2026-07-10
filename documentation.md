# Tender Document Extraction Application

## Project Overview

The Tender Document Extraction Application is a full-stack web application designed to automatically read and parse tender documents in any file format and extract critical business information such as scope of work, closing dates, and other relevant details.

## Key Features

- **Multi-Format Support**: Process tender documents in PDF, DOCX, DOC, TXT, XLSX, CSV, and other common document formats
- **Intelligent Information Extraction**: Automatically identify and extract key information from tender documents
- **Scope of Work Parsing**: Extract detailed scope of work descriptions
- **Closing Date Detection**: Identify and parse tender closing dates with timezone awareness
- **Metadata Extraction**: Retrieve tender ID, organization name, budget, contact information, and more
- **User-Friendly Interface**: React-based frontend for easy document upload and result visualization
- **RESTful API**: Clean API endpoints for programmatic access
- **Real-Time Processing**: Fast document processing with status updates
- **Search & Filter**: Search through extracted data with advanced filtering options
- **Export Results**: Download extracted information in CSV or JSON format

## Technology Stack

### Backend
- **Language**: Python 3.9+
- **Framework**: Flask or FastAPI
- **Document Processing**: python-pptx, python-docx, PyPDF2, openpyxl
- **Text Processing**: Natural Language Processing (NLTK, spaCy)
- **File Handling**: Werkzeug
- **Database**: PostgreSQL or MongoDB
- **Task Queue**: Celery (for async processing)
- **API Documentation**: Swagger/OpenAPI

### Frontend
- **Framework**: React 18+
- **State Management**: Redux or Context API
- **UI Library**: Material-UI or Bootstrap
- **HTTP Client**: Axios
- **Form Handling**: React Hook Form
- **Date Parsing**: Moment.js or date-fns
- **File Upload**: React Dropzone

## Application Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Document Upload Interface                           │ │
│  │  - Drag & Drop                                       │ │
│  │  - File Selection                                    │ │
│  │  - Progress Tracking                                │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Results Display & Management                        │ │
│  │  - Extracted Data Table                             │ │
│  │  - Search & Filter                                  │ │
│  │  - Export Options                                   │ │
│  └─────────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
                 HTTP/REST
                     │
┌────────────────────┴────────────────────────────────────┐
│                Backend (Python)                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  API Layer (Flask/FastAPI)                           │ │
│  │  - /api/upload (POST)                               │ │
│  │  - /api/extract (POST)                              │ │
│  │  - /api/results/<id> (GET)                          │ │
│  │  - /api/export (GET)                                │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Document Processing Engine                          │ │
│  │  - Format Detection                                 │ │
│  │  - Text Extraction                                  │ │
│  │  - Content Parsing                                  │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Information Extraction Module                       │ │
│  │  - NLP Processing                                   │ │
│  │  - Pattern Matching                                 │ │
│  │  - Data Structuring                                 │ │
│  └─────────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
              Database Layer
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼───────┐       ┌──────▼──────┐
    │ PostgreSQL │       │   MongoDB   │
    │            │       │             │
    │ - Uploads  │       │ - Documents │
    │ - Results  │       │ - Cache     │
    │ - Metadata │       │ - Sessions  │
    └────────────┘       └─────────────┘
```

## Installation & Setup

### Backend Setup

1. **Create Python Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install flask python-docx PyPDF2 openpyxl nltk spacy python-dotenv psycopg2-binary
   ```

3. **Configure Environment Variables**
   Create a `.env` file:
   ```
   FLASK_ENV=development
   DATABASE_URL=postgresql://user:password@localhost/tender_db
   UPLOAD_FOLDER=uploads/
   MAX_FILE_SIZE=50MB
   ```

4. **Initialize Database**
   ```bash
   python manage.py db init
   python manage.py db migrate
   python manage.py db upgrade
   ```

5. **Run Backend Server**
   ```bash
   python app.py
   ```
   The API will be available at `http://localhost:5000`

### Frontend Setup

1. **Create React Application**
   ```bash
   npx create-react-app tender-extraction-frontend
   cd tender-extraction-frontend
   ```

2. **Install Dependencies**
   ```bash
   npm install axios react-hook-form react-dropzone moment redux react-redux
   npm install @mui/material @emotion/react @emotion/styled
   ```

3. **Configure API Endpoint**
   Create `.env` file:
   ```
   REACT_APP_API_URL=http://localhost:5000/api
   ```

4. **Start Development Server**
   ```bash
   npm start
   ```
   The application will open at `http://localhost:3000`

## API Endpoints

### 1. Upload Document
**Endpoint**: `POST /api/upload`

**Request**:
```
Content-Type: multipart/form-data
Body: file (binary)
```

**Response** (200 OK):
```json
{
  "upload_id": "uuid-1234567890",
  "filename": "tender_doc.pdf",
  "file_type": "application/pdf",
  "upload_timestamp": "2026-07-09T10:30:00Z",
  "file_size": "2048000",
  "status": "uploaded"
}
```

### 2. Extract Information
**Endpoint**: `POST /api/extract`

**Request**:
```json
{
  "upload_id": "uuid-1234567890"
}
```

**Response** (200 OK):
```json
{
  "extraction_id": "extract-uuid-1234",
  "upload_id": "uuid-1234567890",
  "status": "processing",
  "created_at": "2026-07-09T10:31:00Z"
}
```

### 3. Get Extraction Results
**Endpoint**: `GET /api/results/{extraction_id}`

**Response** (200 OK):
```json
{
  "extraction_id": "extract-uuid-1234",
  "status": "completed",
  "extracted_data": {
    "tender_id": "TENDER-2026-001",
    "tender_name": "Construction Project Tender",
    "organization": "Ministry of Infrastructure",
    "scope_of_work": "Design and construction of 5km highway with modern safety features...",
    "closing_date": "2026-08-15T17:00:00Z",
    "closing_date_formatted": "August 15, 2026 at 5:00 PM",
    "budget": {
      "amount": 5000000,
      "currency": "USD"
    },
    "contact_email": "tenders@infrastructure.gov",
    "contact_phone": "+1-555-0100",
    "location": "Northern District",
    "document_type": "Invitation for Tenders",
    "estimated_duration": "24 months",
    "submission_format": "PDF or DOCX",
    "key_requirements": [
      "Valid business license",
      "Previous project experience",
      "Financial stability proof"
    ],
    "evaluation_criteria": [
      "Technical proposal",
      "Price quotation",
      "Experience & capability"
    ]
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
**Endpoint**: `GET /api/results`

**Query Parameters**:
- `page` (default: 1)
- `limit` (default: 20)
- `search` - search term
- `status` - filter by status (completed, processing, failed)

**Response** (200 OK):
```json
{
  "total": 150,
  "page": 1,
  "limit": 20,
  "results": [
    {
      "extraction_id": "extract-uuid-1234",
      "upload_id": "uuid-1234567890",
      "filename": "tender_doc.pdf",
      "status": "completed",
      "tender_name": "Construction Project Tender",
      "closing_date": "2026-08-15T17:00:00Z",
      "created_at": "2026-07-09T10:31:00Z"
    }
  ]
}
```

### 5. Export Results
**Endpoint**: `GET /api/export/{extraction_id}`

**Query Parameters**:
- `format` - export format (csv, json, xml)

**Response** (200 OK):
- Returns file download in requested format

### 6. Delete Result
**Endpoint**: `DELETE /api/results/{extraction_id}`

**Response** (204 No Content)

## Information Extraction Details

### Extracted Fields

#### Primary Information
- **Tender ID/Reference Number**: Unique identifier for the tender
- **Tender Name/Title**: Official name of the tender
- **Organization/Issuing Authority**: Organization issuing the tender
- **Document Date**: Date the tender was issued
- **Closing Date**: Deadline for tender submission
- **Budget/Project Value**: Estimated project cost

#### Scope of Work
- Full scope description with key deliverables
- Project location and geographic area
- Project timeline and duration
- Major tasks and responsibilities

#### Contact Information
- **Email**: Primary contact email
- **Phone**: Contact phone number
- **Address**: Physical address
- **Department/Contact Person**: Specific contact details

#### Requirements & Criteria
- Eligibility criteria
- Required documents
- Evaluation criteria
- Technical requirements
- Insurance and compliance requirements

### Data Extraction Methods

1. **Keyword-Based Extraction**
   - Pattern matching for closing dates (e.g., "Closing Date:", "Deadline:", "Due Date:")
   - Regex patterns for emails, phone numbers, amounts

2. **NLP-Based Extraction**
   - Named Entity Recognition (NER) for organizations, locations, persons
   - Section identification using text structure analysis
   - Scope extraction using sentence similarity

3. **Structured Document Parsing**
   - Table extraction from PDF and DOCX
   - Form field recognition
   - Header and footer analysis

## File Format Support

| Format | Library | Notes |
|--------|---------|-------|
| PDF | PyPDF2, pdfplumber | Text and table extraction |
| DOCX | python-docx | Native document structure |
| DOC | python-docx2docx | Legacy Word format conversion |
| TXT | Built-in | Plain text processing |
| XLSX | openpyxl | Spreadsheet data extraction |
| CSV | csv module | Tabular data parsing |
| RTF | python-docx | Limited support |
| ODT | odfpy | OpenDocument format |

## Usage Example

### Frontend - Document Upload Component

```javascript
import React, { useState } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';

function DocumentUpload() {
  const [uploadStatus, setUploadStatus] = useState(null);
  const [extractedData, setExtractedData] = useState(null);

  const onDrop = async (acceptedFiles) => {
    const file = acceptedFiles[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
      // Upload file
      const uploadRes = await axios.post(
        `${process.env.REACT_APP_API_URL}/upload`,
        formData
      );

      // Extract information
      const extractRes = await axios.post(
        `${process.env.REACT_APP_API_URL}/extract`,
        { upload_id: uploadRes.data.upload_id }
      );

      // Poll for results
      let results = null;
      let polling = true;
      while (polling) {
        const resultRes = await axios.get(
          `${process.env.REACT_APP_API_URL}/results/${extractRes.data.extraction_id}`
        );
        if (resultRes.data.status === 'completed') {
          results = resultRes.data;
          polling = false;
        }
        await new Promise(resolve => setTimeout(resolve, 2000));
      }

      setExtractedData(results.extracted_data);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const { getRootProps, getInputProps } = useDropzone({ onDrop });

  return (
    <div {...getRootProps()}>
      <input {...getInputProps()} />
      <p>Drag tender documents here or click to select</p>
      {extractedData && (
        <div>
          <h3>{extractedData.tender_name}</h3>
          <p><strong>Closing Date:</strong> {extractedData.closing_date_formatted}</p>
          <p><strong>Scope:</strong> {extractedData.scope_of_work}</p>
          <p><strong>Budget:</strong> {extractedData.budget.currency} {extractedData.budget.amount}</p>
        </div>
      )}
    </div>
  );
}

export default DocumentUpload;
```

### Backend - Information Extraction Function

```python
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import PyPDF2
from docx import Document
import re
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads/'

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    upload_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(upload_path)

    return jsonify({
        'upload_id': str(uuid.uuid4()),
        'filename': filename,
        'file_type': file.content_type,
        'status': 'uploaded'
    })

@app.route('/api/extract', methods=['POST'])
def extract_information():
    data = request.json
    upload_id = data.get('upload_id')
    
    extraction_id = str(uuid.uuid4())
    # Start async extraction task
    celery_task.delay(upload_id, extraction_id)
    
    return jsonify({
        'extraction_id': extraction_id,
        'status': 'processing'
    })

def extract_text_from_pdf(filepath):
    text = ""
    with open(filepath, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_docx(filepath):
    text = ""
    doc = Document(filepath)
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def extract_closing_date(text):
    patterns = [
        r'(?:closing\s+date|deadline|due\s+date)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def extract_scope_of_work(text):
    patterns = [
        r'(?:scope\s+of\s+work)[:\s]+(.*?)(?=\n\n|\n[A-Z])',
        r'(?:description|objective)[:\s]+(.*?)(?=\n\n|\n[A-Z])',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    return None

def process_extraction(upload_id, extraction_id):
    # Retrieve file and extract text
    filepath = os.path.join(UPLOAD_FOLDER, upload_id)
    
    if filepath.endswith('.pdf'):
        text = extract_text_from_pdf(filepath)
    elif filepath.endswith('.docx'):
        text = extract_text_from_docx(filepath)
    else:
        with open(filepath, 'r') as f:
            text = f.read()
    
    # Extract key information
    extracted_data = {
        'closing_date': extract_closing_date(text),
        'scope_of_work': extract_scope_of_work(text),
        # Add more extraction logic
    }
    
    # Store results in database
    save_extraction_results(extraction_id, extracted_data)
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK` - Successful request
- `201 Created` - Resource created
- `204 No Content` - Successful deletion
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required
- `413 Payload Too Large` - File exceeds size limit
- `415 Unsupported Media Type` - File format not supported
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Processing service unavailable

Example error response:
```json
{
  "error": "File format not supported",
  "code": "UNSUPPORTED_FORMAT",
  "details": "Supported formats: PDF, DOCX, TXT, XLSX, CSV"
}
```

## Security Considerations

1. **File Upload Security**
   - Validate file types (whitelist allowed extensions)
   - Scan uploads for malware
   - Limit file size
   - Implement rate limiting

2. **Data Protection**
   - Encrypt sensitive data at rest
   - Use HTTPS for all communications
   - Implement access control (JWT authentication)
   - Log all access attempts

3. **Input Validation**
   - Sanitize all user inputs
   - Validate file names
   - Escape special characters

## Performance Optimization

1. **Async Processing**
   - Use Celery for background tasks
   - Don't block on file processing
   - Implement job queue system

2. **Caching**
   - Cache extraction results
   - Cache frequently accessed data
   - Use Redis for session storage

3. **Database Optimization**
   - Index key fields (extraction_id, upload_id)
   - Archive old records
   - Implement pagination for large result sets

## Deployment

### Docker Deployment

**Dockerfile (Backend)**:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["flask", "run", "--host=0.0.0.0"]
```

**docker-compose.yml**:
```yaml
version: '3'
services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/tender_db
    depends_on:
      - db
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
  
  db:
    image: postgres:13
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: tender_db
```

## Testing

### Backend Unit Tests
```bash
pytest tests/
```

### Frontend Unit Tests
```bash
npm test
```

### Integration Tests
```bash
pytest tests/integration/
```

## Maintenance & Monitoring

1. **Logging**: Use structured logging with ELK stack
2. **Monitoring**: Track API response times, error rates
3. **Alerts**: Set up alerts for system failures
4. **Backups**: Regular database backups
5. **Updates**: Keep dependencies up to date

## Support & Contribution

For issues, feature requests, or contributions, please contact the development team or submit a pull request.

---

**Version**: 1.0.0  
**Last Updated**: July 9, 2026  
**Author**: Development Team
