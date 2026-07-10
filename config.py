import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production-' + os.urandom(24).hex())
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://localhost:5432/tender_db' if os.getenv('USE_POSTGRES') 
        else 'sqlite:///tender.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20,
    }
    
    # File upload settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads/')
    BACKUP_FOLDER = os.getenv('BACKUP_FOLDER', 'backups/')
    LOGS_FOLDER = os.getenv('LOGS_FOLDER', 'logs/')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE', 50 * 1024 * 1024))  # 50MB
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'xlsx', 'csv', 'rtf', 'odt', 'odp'}
    
    # Celery settings
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'UTC'
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
    
    # Redis/Caching
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TYPE = 'redis'
    CACHE_DEFAULT_TIMEOUT = 3600  # 1 hour
    
    # JWT
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))
    JWT_REFRESH_EXPIRATION_DAYS = int(os.getenv('JWT_REFRESH_EXPIRATION_DAYS', 7))
    
    # CORS settings
    CORS_HEADERS = 'Content-Type'
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization', 'X-API-Key']
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # API settings
    API_VERSION = '1.0.0'
    API_PREFIX = '/api'
    API_TITLE = 'Tender Document Extraction API'
    PAGINATION_DEFAULT_LIMIT = 20
    PAGINATION_MAX_LIMIT = 100
    
    # Feature flags
    ENABLE_ASYNC = os.getenv('ENABLE_ASYNC', 'True').lower() == 'true'
    ENABLE_WEBHOOKS = os.getenv('ENABLE_WEBHOOKS', 'True').lower() == 'true'
    ENABLE_OCR = os.getenv('ENABLE_OCR', 'False').lower() == 'true'
    ENABLE_ML = os.getenv('ENABLE_ML', 'False').lower() == 'true'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = 'json'
    LOG_TO_STDOUT = os.getenv('LOG_TO_STDOUT', 'True').lower() == 'true'
    
    # Sentry (error tracking)
    SENTRY_DSN = os.getenv('SENTRY_DSN', None)
    
    # Email settings
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@tender-extraction.com')
    
    # Extraction settings
    EXTRACTION_TIMEOUT = int(os.getenv('EXTRACTION_TIMEOUT', 300))  # 5 minutes
    EXTRACTION_CONFIDENCE_THRESHOLD = float(os.getenv('EXTRACTION_CONFIDENCE_THRESHOLD', 0.7))
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains' if SESSION_COOKIE_SECURE else None
    }


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    LOG_LEVEL = 'DEBUG'
    
    # Disable some production features
    ENABLE_WEBHOOKS = True
    ENABLE_ASYNC = False  # Run sync for easier debugging


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Require secure settings
    if not os.getenv('SECRET_KEY'):
        raise ValueError('SECRET_KEY environment variable must be set in production')
    
    SESSION_COOKIE_SECURE = True
    LOG_LEVEL = 'INFO'
    
    # Enable all features
    ENABLE_ASYNC = True
    ENABLE_WEBHOOKS = True


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    ENABLE_ASYNC = False
    ENABLE_WEBHOOKS = False
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
