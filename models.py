from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Index
from datetime import datetime
import uuid

db = SQLAlchemy()

# ---------------------------------------------------------------------------
# Helper — use JSONB on PostgreSQL, fall back to plain JSON on SQLite/other
# ---------------------------------------------------------------------------

def _json_col(**kwargs):
    """
    Returns a Column that stores JSON as native JSONB on PostgreSQL
    (indexed, faster operators) and falls back to JSON on other backends.
    SQLAlchemy picks the right type at DDL time based on the dialect.
    """
    return db.Column(
        db.JSON().with_variant(JSONB, 'postgresql'),
        **kwargs
    )


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(db.Model):
    """Application users who can be assigned tenders."""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    
    # Authentication fields
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    must_change_password = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Flask-Login integration
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)

    def to_dict(self, include_sensitive=False):
        data = {
            'id':         self.id,
            'name':       self.name,
            'email':      self.email,
            'is_active':  self.is_active,
            'is_admin':   self.is_admin,
            'must_change_password': self.must_change_password,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }
        if include_sensitive:
            data['password_hash'] = self.password_hash
        return data

    def __repr__(self):
        return f'<User {self.name}>'


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

class Upload(db.Model):
    """Uploaded tender document files."""
    __tablename__ = 'uploads'

    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer)
    upload_path = db.Column(db.String(500), nullable=False)
    upload_timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.String(20), default='uploaded')
    mime_type = db.Column(db.String(100))
    assigned_user_id = db.Column(db.String(36),
                                  db.ForeignKey('users.id'), nullable=True)
    assigned_user_name = db.Column(db.String(100))

    extractions = db.relationship(
        'Extraction', backref='upload',
        lazy=True, cascade='all, delete-orphan'
    )

    def to_dict(self):
        return {
            'upload_id':         self.id,
            'filename':          self.filename,
            'file_type':         self.file_type,
            'file_size':         self.file_size,
            'upload_timestamp':  self.upload_timestamp.isoformat(),
            'status':            self.status,
            'mime_type':         self.mime_type,
            'assigned_user_id':  self.assigned_user_id,
            'assigned_user_name': self.assigned_user_name,
        }

    def __repr__(self):
        return f'<Upload {self.filename}>'


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

class Extraction(db.Model):
    """Extracted tender information from an uploaded document."""
    __tablename__ = 'extractions'
    __table_args__ = (
        # Composite index — most list queries filter by upload + status
        Index('idx_upload_status', 'upload_id', 'status'),
        Index('idx_tender_id',  'tender_id'),
        Index('idx_created_at', 'created_at'),
    )

    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    upload_id = db.Column(db.String(36),
                           db.ForeignKey('uploads.id'), nullable=False)
    status = db.Column(db.String(20), default='processing', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    completed_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)

    # ── Core extracted text fields ────────────────────────────────────────
    tender_id            = db.Column(db.String(100), index=True)
    tender_name          = db.Column(db.String(500))
    organization         = db.Column(db.String(255))
    scope_of_work        = db.Column(db.Text)
    closing_date         = db.Column(db.DateTime)
    closing_date_formatted = db.Column(db.String(100))
    contact_email        = db.Column(db.String(255))
    contact_phone        = db.Column(db.String(50))
    address              = db.Column(db.String(500))
    estimated_duration   = db.Column(db.String(200))
    submission_format    = db.Column(db.Text)
    document_type        = db.Column(db.String(100), default='RFQ/RFP')
    budget_amount        = db.Column(db.String(100))
    budget_currency      = db.Column(db.String(20), default='ZAR')
    briefing_session     = db.Column(db.String(500))

    # ── Assignment / workflow ─────────────────────────────────────────────
    assigned_user_id   = db.Column(db.String(36),
                                    db.ForeignKey('users.id'), nullable=True)
    assigned_user_name = db.Column(db.String(100))
    comment            = db.Column(db.Text)
    total_bid_price    = db.Column(db.String(100))

    # ── JSONB list fields (native JSONB on PostgreSQL, JSON on SQLite) ────
    # JSONB gives: faster reads, GIN indexing, @> containment queries,
    #              and proper NULL vs missing-key distinction.
    deliverables          = _json_col(default=list)
    compulsory_documents  = _json_col(default=list)
    mandatory_criteria    = _json_col(default=list)
    evaluation_criteria   = _json_col(default=list)
    pricing_schedule      = _json_col(default=list)
    key_requirements      = _json_col(default=list)
    contact_persons       = _json_col(default=list)
    supporting_documents  = _json_col(default=list)

    # ── JSONB dict fields ─────────────────────────────────────────────────
    confidence_scores     = _json_col(default=dict)

    # ── Metadata ──────────────────────────────────────────────────────────
    processing_time_ms = db.Column(db.Integer)
    error_message      = db.Column(db.Text)

    # ── to_dict ───────────────────────────────────────────────────────────
    def to_dict(self):
        extracted_data = {
            'tender_id':              self.tender_id,
            'tender_name':            self.tender_name,
            'organization':           self.organization,
            'scope_of_work':          self.scope_of_work,
            'closing_date':           self.closing_date.isoformat() if self.closing_date else None,
            'closing_date_formatted': self.closing_date_formatted,
            'contact_email':          self.contact_email,
            'contact_phone':          self.contact_phone,
            'address':                self.address,
            'estimated_duration':     self.estimated_duration,
            'submission_format':      self.submission_format,
            'document_type':          self.document_type,
            'briefing_session':       self.briefing_session,
            'budget': {
                'amount':   self.budget_amount,
                'currency': self.budget_currency or 'ZAR',
            },
            'budget_amount':          self.budget_amount,
            'budget_currency':        self.budget_currency or 'ZAR',
            'deliverables':           self.deliverables or [],
            'compulsory_documents':   self.compulsory_documents or [],
            'mandatory_criteria':     self.mandatory_criteria or [],
            'evaluation_criteria':    self.evaluation_criteria or [],
            'key_requirements':       self.key_requirements or [],
            'pricing_schedule':       self.pricing_schedule or [],
            'contact_persons':        self.contact_persons or [],
            'comment':                self.comment or '',
            'total_bid_price':        self.total_bid_price or '',
            'supporting_documents':   self.supporting_documents or [],
        }

        return {
            'extraction_id':      self.id,
            'upload_id':          self.upload_id,
            'status':             self.status,
            'created_at':         self.created_at.isoformat(),
            'completed_at':       self.completed_at.isoformat() if self.completed_at else None,
            'assigned_user': {
                'id':   self.assigned_user_id,
                'name': self.assigned_user_name,
            },
            'comment':            self.comment or '',
            'total_bid_price':    self.total_bid_price or '',
            'supporting_documents': self.supporting_documents or [],
            'extracted_data':     extracted_data,
            'confidence_scores':  self.confidence_scores or {},
            'processing_time_ms': self.processing_time_ms,
            'error_message':      self.error_message,
        }

    def __repr__(self):
        return f'<Extraction {self.tender_id or self.id[:8]}>'
