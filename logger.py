"""Logging configuration for the application"""

import logging
import logging.handlers
import os
from datetime import datetime
from pythonjsonlogger import jsonlogger

def setup_logging(app, log_level=None):
    """Configure application logging"""
    
    if log_level is None:
        log_level = logging.DEBUG if app.debug else logging.INFO
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Remove default handler
    app.logger.handlers.clear()
    
    # JSON formatter for structured logging
    json_formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        timestamp=True
    )
    
    # File handler for errors
    error_file = logging.handlers.RotatingFileHandler(
        'logs/error.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    error_file.setLevel(logging.ERROR)
    error_file.setFormatter(json_formatter)
    
    # File handler for all logs
    all_file = logging.handlers.RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    all_file.setLevel(log_level)
    all_file.setFormatter(json_formatter)
    
    # Console handler
    console = logging.StreamHandler()
    console.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console.setFormatter(console_formatter)
    
    # Add handlers to app logger
    app.logger.addHandler(error_file)
    app.logger.addHandler(all_file)
    app.logger.addHandler(console)
    app.logger.setLevel(log_level)
    
    # Configure other loggers
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    
    app.logger.info(f"Logging initialized at level {logging.getLevelName(log_level)}")
    
    return app.logger


def get_logger(name):
    """Get a logger instance"""
    return logging.getLogger(name)


class AuditLogger:
    """Audit logging for important operations"""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
    
    def log_upload(self, user_id, filename, file_size):
        """Log file upload"""
        self.logger.info(
            f"File uploaded: user={user_id}, filename={filename}, size={file_size}",
            extra={'action': 'UPLOAD', 'user_id': user_id}
        )
    
    def log_extraction(self, extraction_id, upload_id, status):
        """Log extraction"""
        self.logger.info(
            f"Extraction: id={extraction_id}, upload_id={upload_id}, status={status}",
            extra={'action': 'EXTRACTION', 'extraction_id': extraction_id}
        )
    
    def log_export(self, user_id, extraction_id, format_type):
        """Log export"""
        self.logger.info(
            f"Export: user={user_id}, extraction={extraction_id}, format={format_type}",
            extra={'action': 'EXPORT', 'user_id': user_id}
        )
    
    def log_delete(self, user_id, extraction_id):
        """Log deletion"""
        self.logger.warning(
            f"Deletion: user={user_id}, extraction={extraction_id}",
            extra={'action': 'DELETE', 'user_id': user_id}
        )

    def log_error(self, error_type, message, context=None):
        """Log errors"""
        self.logger.error(
            f"Error: type={error_type}, message={message}, context={context}",
            extra={'action': 'ERROR', 'error_type': error_type}
        )


audit_logger = AuditLogger()
