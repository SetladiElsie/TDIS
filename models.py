from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()


class Upload(db.Model):
    """Model for file uploads"""
    __tablename__ = 'uploads'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer)
    upload_path = db.Column(db.String(500), nullable=False)
    upload_timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.String(20), default='uploaded')
    mime_type = db.Column(db.String(100))

    extractions = db.relationship('Extraction', backref='upload', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'upload_id': self.id,
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'upload_timestamp': self.upload_timestamp.isoformat(),
            'status': self.status,
            'mime_type': self.mime_type,
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
    status = db.Column(db.String(20), default='processing', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    completed_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)

    # Core extracted fields
    tender_id = db.Column(db.String(100), index=True)
    tender_name = db.Column(db.String(255))
    scope_of_work = db.Column(db.Text)
    closing_date = db.Column(db.DateTime)
    closing_date_formatted = db.Column(db.String(100))
    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    location = db.Column(db.String(255))
    estimated_duration = db.Column(db.String(100))
    submission_format = db.Column(db.String(500))

    # JSON list fields
    deliverables = db.Column(db.JSON, default=list)
    compulsory_documents = db.Column(db.JSON, default=list)
    mandatory_criteria = db.Column(db.JSON, default=list)
    pricing_schedule = db.Column(db.JSON, default=list)

    # Metadata
    confidence_scores = db.Column(db.JSON, default=dict)
    processing_time_ms = db.Column(db.Integer)
    error_message = db.Column(db.Text)

    def to_dict(self):
        extracted_data = {
            'tender_id':             self.tender_id,
            'tender_name':           self.tender_name,
            'scope_of_work':         self.scope_of_work,
            'closing_date':          self.closing_date.isoformat() if self.closing_date else None,
            'closing_date_formatted': self.closing_date_formatted,
            'contact_email':         self.contact_email,
            'contact_phone':         self.contact_phone,
            'location':              self.location,
            'estimated_duration':    self.estimated_duration,
            'submission_format':     self.submission_format,
            'deliverables':          self.deliverables or [],
            'compulsory_documents':  self.compulsory_documents or [],
            'mandatory_criteria':    self.mandatory_criteria or [],
            'pricing_schedule':      self.pricing_schedule or [],
        }

        return {
            'extraction_id':     self.id,
            'upload_id':         self.upload_id,
            'status':            self.status,
            'created_at':        self.created_at.isoformat(),
            'completed_at':      self.completed_at.isoformat() if self.completed_at else None,
            'extracted_data':    extracted_data,
            'confidence_scores': self.confidence_scores or {},
            'processing_time_ms': self.processing_time_ms,
            'error_message':     self.error_message,
        }
