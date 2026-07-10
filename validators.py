"""Input validation utilities"""

import re
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from logger import get_logger

logger = get_logger(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'xlsx', 'csv', 'rtf', 'odt', 'odp'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'text/plain',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv',
    'application/rtf',
    'application/vnd.oasis.opendocument.text',
    'application/vnd.oasis.opendocument.presentation'
}

class ValidationError(Exception):
    """Custom validation error"""
    pass


def validate_file(file, max_size=50*1024*1024):
    """Validate uploaded file"""
    errors = []
    
    if not file:
        errors.append('No file provided')
    elif not file.filename:
        errors.append('Invalid filename')
    
    if errors:
        raise ValidationError(', '.join(errors))
    
    # Check filename
    filename = secure_filename(file.filename)
    if not filename:
        raise ValidationError('Invalid filename after sanitization')
    
    # Check extension
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f'Invalid file extension: {ext}. Allowed: {", ".join(ALLOWED_EXTENSIONS)}')
    
    # Check MIME type
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"Suspicious MIME type: {file.content_type} for file {filename}")
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size == 0:
        raise ValidationError('File is empty')
    
    if file_size > max_size:
        raise ValidationError(f'File too large: {file_size} bytes (max: {max_size})')
    
    return {
        'filename': filename,
        'size': file_size,
        'extension': ext
    }


def validate_extraction_data(data):
    """Validate extracted data"""
    if not isinstance(data, dict):
        raise ValidationError('Data must be a dictionary')
    
    # Required fields
    required_fields = ['tender_id', 'tender_name']
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        raise ValidationError(f'Missing required fields: {", ".join(missing)}')
    
    # Validate dates
    for date_field in ['closing_date']:
        if date_field in data and data[date_field]:
            if not validate_date(data[date_field]):
                raise ValidationError(f'Invalid date format for {date_field}')
    
    # Validate budget
    if 'budget_amount' in data and data['budget_amount']:
        if not validate_number(data['budget_amount']):
            raise ValidationError('Invalid budget amount')
    
    # Validate email
    if 'contact_email' in data and data['contact_email']:
        if not validate_email(data['contact_email']):
            raise ValidationError('Invalid email format')
    
    # Validate phone
    if 'contact_phone' in data and data['contact_phone']:
        if not validate_phone(data['contact_phone']):
            raise ValidationError('Invalid phone number format')
    
    return True


def validate_date(date_string):
    """Validate date string"""
    if not date_string:
        return True
    
    if isinstance(date_string, datetime):
        return True
    
    # Try common formats
    formats = [
        '%Y-%m-%d',
        '%d-%m-%Y',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%Y/%m/%d',
        '%d.%m.%Y',
        '%B %d, %Y',
        '%d %B %Y',
        '%b %d, %Y',
        '%d %b %Y'
    ]
    
    for fmt in formats:
        try:
            datetime.strptime(str(date_string).strip(), fmt)
            return True
        except ValueError:
            continue
    
    return False


def validate_email(email):
    """Validate email address"""
    if not email:
        return True
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, str(email).strip()))


def validate_phone(phone):
    """Validate phone number"""
    if not phone:
        return True
    
    # Remove common separators
    cleaned = re.sub(r'[\s\-().]', '', str(phone))
    
    # Should be mostly digits
    if not re.match(r'^\+?[0-9]{7,15}$', cleaned):
        return False
    
    return True


def validate_number(value):
    """Validate numeric value"""
    if not value:
        return True
    
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def validate_confidence_score(score):
    """Validate confidence score (0-1)"""
    try:
        score = float(score)
        return 0 <= score <= 1
    except (ValueError, TypeError):
        return False


def sanitize_filename(filename):
    """Sanitize filename for safety"""
    filename = secure_filename(filename)
    if not filename:
        return 'file'
    return filename


def sanitize_text(text):
    """Sanitize text to prevent injection attacks"""
    if not isinstance(text, str):
        return str(text)
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Limit length to prevent DOS
    max_length = 10000
    if len(text) > max_length:
        text = text[:max_length]
    
    return text


def validate_pagination(page, limit):
    """Validate pagination parameters"""
    try:
        page = int(page) if page else 1
        limit = int(limit) if limit else 20
        
        if page < 1:
            raise ValueError('Page must be >= 1')
        if limit < 1 or limit > 100:
            raise ValueError('Limit must be between 1 and 100')
        
        return page, limit
    except (ValueError, TypeError) as e:
        raise ValidationError(f'Invalid pagination parameters: {str(e)}')


def validate_api_key_format(api_key):
    """Validate API key format"""
    if not api_key or len(api_key) < 32:
        return False
    
    # API keys should be alphanumeric and hyphens
    return bool(re.match(r'^[a-zA-Z0-9\-]{32,}$', api_key))
