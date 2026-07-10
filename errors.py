"""Custom exception classes"""


class TenderAPIError(Exception):
    """Base exception for Tender API"""
    
    def __init__(self, message, code='INTERNAL_ERROR', status_code=500, details=None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert exception to dictionary"""
        return {
            'error': self.message,
            'code': self.code,
            'details': self.details
        }


class ValidationError(TenderAPIError):
    """Raised when validation fails"""
    
    def __init__(self, message, details=None):
        super().__init__(
            message=message,
            code='VALIDATION_ERROR',
            status_code=400,
            details=details or {}
        )


class FileProcessingError(TenderAPIError):
    """Raised when file processing fails"""
    
    def __init__(self, message, details=None):
        super().__init__(
            message=message,
            code='FILE_PROCESSING_ERROR',
            status_code=400,
            details=details or {}
        )


class ExtractionError(TenderAPIError):
    """Raised when extraction fails"""
    
    def __init__(self, message, details=None):
        super().__init__(
            message=message,
            code='EXTRACTION_ERROR',
            status_code=400,
            details=details or {}
        )


class NotFoundError(TenderAPIError):
    """Raised when resource not found"""
    
    def __init__(self, message, details=None):
        super().__init__(
            message=message,
            code='NOT_FOUND',
            status_code=404,
            details=details or {}
        )


class UnauthorizedError(TenderAPIError):
    """Raised when authentication fails"""
    
    def __init__(self, message, details=None):
        super().__init__(
            message=message,
            code='UNAUTHORIZED',
            status_code=401,
            details=details or {}
        )


class ForbiddenError(TenderAPIError):
    """Raised when authorization fails"""
    
    def __init__(self, message, details=None):
        super().__init__(
            message=message,
            code='FORBIDDEN',
            status_code=403,
            details=details or {}
        )


class ConflictError(TenderAPIError):
    """Raised on resource conflicts"""
    
    def __init__(self, message, details=None):
        super().__init__(
            message=message,
            code='CONFLICT',
            status_code=409,
            details=details or {}
        )


class RateLimitError(TenderAPIError):
    """Raised when rate limit exceeded"""
    
    def __init__(self, message, retry_after=None, details=None):
        details = details or {}
        if retry_after:
            details['retry_after'] = retry_after
        super().__init__(
            message=message,
            code='RATE_LIMIT_EXCEEDED',
            status_code=429,
            details=details
        )


class DatabaseError(TenderAPIError):
    """Raised on database errors"""
    
    def __init__(self, message, details=None):
        super().__init__(
            message=message,
            code='DATABASE_ERROR',
            status_code=500,
            details=details or {}
        )


class WebhookError(TenderAPIError):
    """Raised on webhook failures"""
    
    def __init__(self, message, details=None):
        super().__init__(
            message=message,
            code='WEBHOOK_ERROR',
            status_code=500,
            details=details or {}
        )


class OCRError(TenderAPIError):
    """Raised on OCR processing failures"""
    
    def __init__(self, message, details=None):
        super().__init__(
            message=message,
            code='OCR_ERROR',
            status_code=400,
            details=details or {}
        )
