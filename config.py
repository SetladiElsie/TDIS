import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False

    # ── Database ──────────────────────────────────────────────────────────────
    # Reads DATABASE_URL from .env — must be a PostgreSQL URI in production.
    # Falls back to SQLite only for local development when no .env is present.
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'tender.db').replace(chr(92), '/')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # PostgreSQL-optimised connection pool settings.
    # These are ignored by SQLite but are safe to define for all environments.
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,       # reconnect after idle timeout
        'pool_size': 10,             # persistent connections kept open
        'max_overflow': 20,          # extra connections allowed under load
        'pool_timeout': 30,          # seconds to wait for a connection
        'pool_recycle': 1800,        # recycle connections every 30 minutes
    }

    # ── File upload ───────────────────────────────────────────────────────────
    # IMPORTANT: Store uploads outside web root for security
    # Development: relative path (uploads/)
    # Production: absolute path outside application directory (/var/uploads/tdis/)
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads/')
    LOGS_FOLDER = os.getenv('LOGS_FOLDER', 'logs/')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE', 500 * 1024 * 1024))  # 500 MB (increased for batch uploads)
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'xlsx', 'csv', 'rtf', 'odt'}
    
    # ── File Security ─────────────────────────────────────────────────────────
    # Enable advanced file validation (MIME type checking, virus scanning)
    ENABLE_FILE_MIME_VALIDATION = os.getenv('ENABLE_FILE_MIME_VALIDATION', 'True').lower() == 'true'
    ENABLE_VIRUS_SCANNING = os.getenv('ENABLE_VIRUS_SCANNING', 'False').lower() == 'true'
    
    # Quarantine folder for suspicious files
    QUARANTINE_FOLDER = os.getenv('QUARANTINE_FOLDER', 'quarantine/')

    # ── Redis / Caching ───────────────────────────────────────────────────────
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = 3600

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    CORS_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization', 'Accept']

    # ── Email ─────────────────────────────────────────────────────────────────
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_FROM = (
        os.getenv('MAIL_FROM')
        or os.getenv('MAIL_SENDER')
        or 'tdis-no-reply@tia-solutions.co.za'
    )

    # ── API ───────────────────────────────────────────────────────────────────
    API_VERSION = '1.0.0'
    API_PREFIX = '/api'
    API_TITLE = 'Tender Document Extraction API'
    PAGINATION_DEFAULT_LIMIT = 20
    PAGINATION_MAX_LIMIT = 100

    # ── Feature flags ─────────────────────────────────────────────────────────
    ENABLE_ASYNC = os.getenv('ENABLE_ASYNC', 'False').lower() == 'true'
    ENABLE_OCR = os.getenv('ENABLE_OCR', 'False').lower() == 'true'
    ENABLE_ML = os.getenv('ENABLE_ML', 'False').lower() == 'true'

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_TO_STDOUT = os.getenv('LOG_TO_STDOUT', 'True').lower() == 'true'

    # ── Extraction ────────────────────────────────────────────────────────────
    EXTRACTION_TIMEOUT = int(os.getenv('EXTRACTION_TIMEOUT', 300))
    EXTRACTION_CONFIDENCE_THRESHOLD = float(
        os.getenv('EXTRACTION_CONFIDENCE_THRESHOLD', 0.7)
    )

    # ── Security headers ──────────────────────────────────────────────────────
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
    }


class DevelopmentConfig(Config):
    """Development — verbose logging, debug mode on."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production — stricter pool, no debug output."""
    DEBUG = False
    LOG_LEVEL = 'INFO'

    # Larger pool for production traffic
    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        'pool_size': 20,
        'max_overflow': 40,
    }


class TestingConfig(Config):
    """Testing — in-memory SQLite, no async."""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    ENABLE_ASYNC = False
    # Disable pool options for SQLite in-memory
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
