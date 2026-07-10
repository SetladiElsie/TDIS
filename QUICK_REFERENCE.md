# Quick Reference - Using the New Infrastructure

## 🚀 Quick Start with Enhancements

### 1. Authentication

```python
from flask import Flask, request
from auth import require_auth, generate_jwt_token

app = Flask(__name__)

# Protected route
@app.route('/api/protected')
@require_auth
def protected():
    user_id = request.user_id
    return {'message': f'Hello {user_id}'}

# Login endpoint (example)
@app.route('/api/login', methods=['POST'])
def login():
    # Verify credentials...
    token = generate_jwt_token(user_id=user.id, expires_in=24)
    return {'token': token}
```

### 2. Input Validation

```python
from validators import validate_file, validate_email, ValidationError

@app.route('/api/upload', methods=['POST'])
def upload():
    try:
        # Validate file
        file_info = validate_file(request.files['file'])
        
        # Validate email
        if not validate_email(request.form.get('email')):
            raise ValidationError("Invalid email")
        
        return {'filename': file_info['filename']}
    except ValidationError as e:
        return {'error': str(e)}, 400
```

### 3. Error Handling

```python
from errors import ValidationError, NotFoundError, UnauthorizedError
from flask import jsonify

# Errors are automatically caught and converted to JSON
@app.route('/api/user/<user_id>')
def get_user(user_id):
    user = db.session.query(User).get(user_id)
    if not user:
        raise NotFoundError(f"User {user_id} not found")
    return user.to_dict()

# Global error handler already in app.py
```

### 4. Caching

```python
from cache import cache, cache_extraction_result, @cache_result

# Manual caching
cache.set("extraction:123", extraction_data, expire=3600)
data = cache.get("extraction:123")

# Decorator caching
@cache_result("expensive_operation", expire=1800)
def get_expensive_data():
    return expensive_calculation()

# Specific caching functions
cache_extraction_result(extraction_id, data)
data = get_cached_extraction_result(extraction_id)
```

### 5. Async Tasks

```python
from celery_app import extract_document_async, celery_app

# Queue async task
task = extract_document_async.delay(upload_id, extraction_id)

# Check status
status = celery_app.AsyncResult(task.id).status

# In production, Celery processes in background:
# - Extracts document
# - Updates database
# - Sends webhooks
# - Caches results
```

### 6. Logging

```python
from logger import get_logger, audit_logger

logger = get_logger(__name__)

# Regular logging
logger.info("User uploaded file")
logger.warning("Cache unavailable")
logger.error("Extraction failed", exc_info=True)

# Audit logging
audit_logger.log_upload(user_id, filename, file_size)
audit_logger.log_extraction(extraction_id, upload_id, status)
audit_logger.log_delete(user_id, extraction_id)
audit_logger.log_auth_attempt(user_id, success=True)
```

### 7. Webhooks

```python
from webhook_handler import webhook_handler, webhook_queue

# Send webhook directly
webhook_handler.send_webhook(
    webhook_url="https://example.com/webhook",
    event_type="extraction.completed",
    payload={"extraction_id": "123", "status": "completed"}
)

# Queue webhooks for user
webhooks = db.session.query(Webhook).filter_by(user_id=user_id).all()
webhook_queue.queue_event(db, user_id, "extraction.completed", webhooks, payload)
```

### 8. Database Backup

```python
from backup_manager import BackupManager

mgr = BackupManager()

# Create backup
result = mgr.create_backup(db_type='postgresql')
# Returns: {'status': 'success', 'backup_path': '...', 'timestamp': '...'}

# List backups
backups = mgr.list_backups()

# Restore backup
mgr.restore_backup('backup_postgres_20260709_120000.sql')
```

### 9. OCR (For Scanned PDFs)

```python
from ocr_handler import ocr_handler

if ocr_handler.available:
    # Check if PDF is scanned
    is_scanned = ocr_handler.is_scanned_pdf('/path/to/pdf.pdf')
    
    if is_scanned:
        # Extract text using OCR
        text_pages = ocr_handler.extract_text_from_pdf_images('/path/to/pdf.pdf')
        for page in text_pages:
            print(f"Page {page['page']}: {page['text']}")
```

### 10. Machine Learning Extraction

```python
from ml_model import ml_model, confidence_scorer

# Use ML model if available
if ml_model.available:
    result = ml_model.extract_field_ml(text, 'tender_id')
    # Returns: {'value': '...' , 'confidence': 0.95}
    
    # Score confidence
    conf = confidence_scorer.score_date(date_value, original_text)
```

### 11. Decorators

```python
from decorators import (
    @timing_decorator,
    @error_handler_decorator,
    @validate_json,
    @require_params,
    @cache_route,
    @paginated,
    @log_request_response,
    @require_file
)

# Measure time
@timing_decorator
def slow_function():
    time.sleep(2)

# Require JSON body
@app.route('/api/data', methods=['POST'])
@validate_json
def post_data():
    data = request.get_json()
    return {'received': data}

# Require specific parameters
@app.route('/api/search', methods=['POST'])
@require_params('query', 'limit')
def search():
    query = request.json['query']
    limit = request.json['limit']
    return {'results': []}

# Cache response
@app.route('/api/stats')
@cache_route(expire=3600)
def stats():
    # Only computed once per hour
    return {'stats': 'data'}

# Pagination helper
@app.route('/api/items')
@paginated
def list_items(page, limit):
    offset = (page - 1) * limit
    items = Item.query.offset(offset).limit(limit).all()
    return {'items': [i.to_dict() for i in items]}

# Require file upload
@app.route('/api/upload', methods=['POST'])
@require_file()
def upload_file():
    file = request.files['file']
    # Process file
    return {'uploaded': file.filename}
```

---

## 📝 Common Patterns

### Pattern 1: Upload → Extract → Cache
```python
@app.route('/api/extract', methods=['POST'])
@require_auth
@validate_json
@require_params('upload_id')
def extract():
    try:
        upload_id = request.json['upload_id']
        
        # Create extraction
        extraction = Extraction(upload_id=upload_id)
        db.session.add(extraction)
        db.session.commit()
        
        # Queue async
        extract_document_async.delay(upload_id, extraction.id)
        
        # Cache soon-to-be result
        cache.set(f"extraction:{extraction.id}", {'status': 'processing'}, 300)
        
        return {'extraction_id': extraction.id, 'status': 'queued'}, 202
    except ValidationError as e:
        return {'error': str(e)}, 400
```

### Pattern 2: Admin Audit Trail
```python
from models import AuditLog

def log_action(user_id, action, resource_type=None, resource_id=None, status='success'):
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        status=status
    )
    db.session.add(log)
    db.session.commit()
    audit_logger.log_action_func(user_id, action, status)
```

### Pattern 3: Webhook on Completion
```python
from webhook_handler import webhook_queue, webhook_handler

# In extraction completion handler
def on_extraction_complete(extraction):
    # Find user's webhooks
    webhooks = db.session.query(Webhook).filter(
        Webhook.user_id == extraction.upload.user_id,
        Webhook.is_active == True
    ).all()
    
    # Build payload
    payload = webhook_handler.build_extraction_payload(extraction)
    
    # Queue events
    webhook_queue.queue_event(
        db, extraction.upload.user_id, 'extraction.completed',
        webhooks, payload
    )
```

---

## 🔄 Workflow Examples

### Complete Upload → Extract → Webhook Flow
```
1. User calls POST /api/upload → Upload model created
2. File stored → Celery task queued
3. Async: extract_document_async processes
4. On completion:
   - Update Extraction model
   - Cache result (1 hour)
   - Queue webhooks
   - Log audit entry
   - Send notifications
5. Frontend polls or receives webhook
6. User exports to JSON/CSV
7. Audit log recorded
8. Result cached for next view
```

### Admin Dashboard Stats
```
1. Admin calls GET /api/admin/stats
2. Check cache for stats
3. If cache miss:
   - Query: total uploads (count)
   - Query: successful extractions (count)
   - Query: failed extractions (count)
   - Query: recent users
   - Calculate percentages
   - Cache result (1 hour)
4. Return JSON stats
```

---

## ⚙️ Configuration

All configuration in `config.py`. Environment-based:

```bash
# Development
export FLASK_ENV=development
export ENABLE_ASYNC=False

# Production
export FLASK_ENV=production
export SECRET_KEY=<random-key>
export DATABASE_URL=postgresql://...
export REDIS_URL=redis://...
export ENABLE_ASYNC=True
export ENABLE_WEBHOOKS=True
```

---

## 🧪 Testing Pattern

```python
import pytest
from app import create_app, db
from models import User, Extraction

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_extraction(app):
    client = app.test_client()
    
    # Create test data
    user = User(username='test', email='test@test.com')
    db.session.add(user)
    db.session.commit()
    
    # Test endpoint
    response = client.post('/api/extract', json={'upload_id': '123'})
    assert response.status_code == 400  # No upload with that ID
```

---

## 📚 Implementation Tips

1. **Always validate input** - Use validators module
2. **Always catch errors** - Let custom errors bubble up
3. **Always log actions** - Use audit_logger
4. **Always cache expensive** - Use @cache_result
5. **Always authenticate** - Use @require_auth
6. **Always test** - Write unit and integration tests
7. **Always backup** - Test restore regularly
8. **Always monitor** - Check logs and Sentry

---

**Happy Implementing! 🚀**

All the infrastructure is ready. Just build the routes and UI!
