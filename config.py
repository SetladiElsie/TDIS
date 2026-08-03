import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = False
    TESTING = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///tender.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
    }

    # File upload settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads/')
    LOGS_FOLDER = os.getenv('LOGS_FOLDER', 'logs/')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE', 50 * 1024 * 1024))  # 50MB
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'xlsx', 'csv', 'rtf', 'odt'}

    # Redis / Caching (optional)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = 3600

    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type']

    # API settings
    API_VERSION = '1.0.0'
    API_PREFIX = '/api'
    API_TITLE = 'Tender Document Extraction API'
    PAGINATION_DEFAULT_LIMIT = 20
    PAGINATION_MAX_LIMIT = 100

    # Feature flags
    ENABLE_ASYNC = os.getenv('ENABLE_ASYNC', 'False').lower() == 'true'
    ENABLE_OCR = os.getenv('ENABLE_OCR', 'False').lower() == 'true'
    ENABLE_ML = os.getenv('ENABLE_ML', 'False').lower() == 'true'

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_TO_STDOUT = os.getenv('LOG_TO_STDOUT', 'True').lower() == 'true'

    # Extraction settings
    EXTRACTION_TIMEOUT = int(os.getenv('EXTRACTION_TIMEOUT', 300))
    EXTRACTION_CONFIDENCE_THRESHOLD = float(os.getenv('EXTRACTION_CONFIDENCE_THRESHOLD', 0.7))

    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
    }


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'INFO'


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    ENABLE_ASYNC = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
