from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    role = db.Column(db.String(50), default='user')  # user, admin, operator
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    uploads = db.relationship('Upload', backref='user', lazy=True, cascade='all, delete-orphan')
    api_keys = db.relationship('APIKey', backref='user', lazy=True, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    webhooks = db.relationship('Webhook', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_sensitive=False):
        data = {
            'user_id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            data['email_verified'] = True
        
        return data


class APIKey(db.Model):
    """API Key model for programmatic access"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    key = db.Column(db.String(255), unique=True, nullable=False, index=True)
    secret = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    request_count = db.Column(db.Integer, default=0)
    
    def to_dict(self, include_secret=False):
        data = {
            'key_id': self.id,
            'name': self.name,
            'key': self.key,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'request_count': self.request_count
        }
        
        if include_secret:
            data['secret'] = self.secret
        
        return data


class Upload(db.Model):
    """Model for file uploads"""
    __tablename__ = 'uploads'
    __table_args__ = (db.Index('idx_user_timestamp', 'user_id', 'upload_timestamp'),)
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True, index=True)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer)
    upload_path = db.Column(db.String(500), nullable=False)
    upload_timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.String(20), default='uploaded')  # uploaded, processing, completed, failed
    mime_type = db.Column(db.String(100))
    checksum = db.Column(db.String(64))  # SHA-256 checksum
    
    # Relationships
    extractions = db.relationship('Extraction', backref='upload', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'upload_id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'upload_timestamp': self.upload_timestamp.isoformat(),
            'status': self.status,
            'mime_type': self.mime_type
        }


class Extraction(db.Model):
    """Model for tender information extractions"""
    __tablename__ = 'extractions'
    __table_args__ = (
        db.Index('idx_upload_status', 'upload_id', 'status'),
        db.Index('idx_tender_id', 'tender_id'),
        db.Index('idx_created_at', 'created_at'),
    )
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    upload_id = db.Column(db.String(36), db.ForeignKey('uploads.id'), nullable=False)
    status = db.Column(db.String(20), default='processing', index=True)  # processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    completed_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)
    
    # Extracted data (stored as JSON)
    tender_id = db.Column(db.String(100), index=True)
    tender_name = db.Column(db.String(255))
    organization = db.Column(db.String(255))
    scope_of_work = db.Column(db.Text)
    closing_date = db.Column(db.DateTime)
    closing_date_formatted = db.Column(db.String(100))
    budget_amount = db.Column(db.Float)
    budget_currency = db.Column(db.String(10), default='USD')
    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    location = db.Column(db.String(255))
    document_type = db.Column(db.String(100))
    estimated_duration = db.Column(db.String(50))
    submission_format = db.Column(db.String(255))
    
    # Complex fields stored as JSON
    key_requirements = db.Column(db.JSON, default=[])
    evaluation_criteria = db.Column(db.JSON, default=[])
    deliverables = db.Column(db.JSON, default=[])
    compulsory_documents = db.Column(db.JSON, default=[])
    
    # Confidence scores and metadata
    confidence_scores = db.Column(db.JSON, default={})
    processing_time_ms = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    
    # Full text search field
    full_text_search = db.Column(db.Text)
    
    # Relationships
    webhooks = db.relationship('WebhookEvent', backref='extraction', lazy=True)
    
    def to_dict(self):
        extracted_data = {
            'tender_id': self.tender_id,
            'tender_name': self.tender_name,
            'organization': self.organization,
            'scope_of_work': self.scope_of_work,
            'closing_date': self.closing_date.isoformat() if self.closing_date else None,
            'closing_date_formatted': self.closing_date_formatted,
            'budget': {
                'amount': self.budget_amount,
                'currency': self.budget_currency
            },
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'location': self.location,
            'document_type': self.document_type,
            'estimated_duration': self.estimated_duration,
            'submission_format': self.submission_format,
            'key_requirements': self.key_requirements or [],
            'evaluation_criteria': self.evaluation_criteria or [],
            'deliverables': self.deliverables or [],
            'compulsory_documents': self.compulsory_documents or []
        }
        
        return {
            'extraction_id': self.id,
            'upload_id': self.upload_id,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'extracted_data': extracted_data,
            'confidence_scores': self.confidence_scores or {},
            'processing_time_ms': self.processing_time_ms,
            'error_message': self.error_message
        }


class Webhook(db.Model):
    """Webhook endpoints for event notifications"""
    __tablename__ = 'webhooks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    events = db.Column(db.JSON, default=[])  # extraction.completed, extraction.failed, upload.completed
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    events_history = db.relationship('WebhookEvent', backref='webhook', lazy=True)
    
    def to_dict(self):
        return {
            'webhook_id': self.id,
            'name': self.name,
            'url': self.url,
            'events': self.events or [],
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class WebhookEvent(db.Model):
    """Webhook event history"""
    __tablename__ = 'webhook_events'
    __table_args__ = (db.Index('idx_status', 'status'),)
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    webhook_id = db.Column(db.String(36), db.ForeignKey('webhooks.id'), nullable=False, index=True)
    extraction_id = db.Column(db.String(36), db.ForeignKey('extractions.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # extraction.completed, extraction.failed
    payload = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed, retrying
    attempts = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'event_id': self.id,
            'webhook_id': self.webhook_id,
            'extraction_id': self.extraction_id,
            'event_type': self.event_type,
            'status': self.status,
            'attempts': self.attempts,
            'created_at': self.created_at.isoformat(),
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'error_message': self.error_message
        }


class AuditLog(db.Model):
    """Audit log for tracking user actions"""
    __tablename__ = 'audit_logs'
    __table_args__ = (db.Index('idx_user_action', 'user_id', 'action'),)
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)  # upload, extract, export, delete, auth, admin
    resource_type = db.Column(db.String(50))  # upload, extraction, user, api_key
    resource_id = db.Column(db.String(36))
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(500))
    status = db.Column(db.String(20), default='success')  # success, failure
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'log_id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'ip_address': self.ip_address,
            'status': self.status,
            'details': self.details,
            'created_at': self.created_at.isoformat()
        }


class BatchJob(db.Model):
    """Batch processing jobs"""
    __tablename__ = 'batch_jobs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='queued')  # queued, processing, completed, failed
    total_files = db.Column(db.Integer, default=0)
    processed_files = db.Column(db.Integer, default=0)
    failed_files = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    result_file = db.Column(db.String(500))  # Path to result ZIP file
    error_message = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'job_id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'status': self.status,
            'progress': {
                'total': self.total_files,
                'processed': self.processed_files,
                'failed': self.failed_files,
                'percentage': round((self.processed_files / self.total_files * 100) if self.total_files > 0 else 0, 2)
            },
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }


class ExtractionTemplate(db.Model):
    """Templates for custom extraction patterns"""
    __tablename__ = 'extraction_templates'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    patterns = db.Column(db.JSON, nullable=False)  # Custom regex patterns
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'template_id': self.id,
            'name': self.name,
            'description': self.description,
            'patterns': self.patterns,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class StoredSearch(db.Model):
    """Saved search queries"""
    __tablename__ = 'stored_searches'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    query = db.Column(db.String(500), nullable=False)
    filters = db.Column(db.JSON)
    is_favourite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'search_id': self.id,
            'name': self.name,
            'query': self.query,
            'filters': self.filters,
            'is_favourite': self.is_favourite,
            'created_at': self.created_at.isoformat()
        }
