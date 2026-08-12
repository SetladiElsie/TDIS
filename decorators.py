"""Custom decorators for Flask routes"""

import time
import functools
import json
from flask import jsonify, request
from logger import get_logger

logger = get_logger(__name__)


def timing_decorator(f):
    """Measure function execution time"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug(f"{f.__name__} took {elapsed:.3f} seconds")
        return result
    return decorated_function


def error_handler_decorator(f):
    """Generic error handling decorator"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({
                'error': 'Internal server error',
                'code': 'INTERNAL_ERROR',
                'message': str(e) if str(e) else 'An error occurred'
            }), 500
    return decorated_function


def validate_json(f):
    """Validate request contains JSON"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({
                'error': 'Invalid content type',
                'code': 'INVALID_CONTENT_TYPE'
            }), 400
        return f(*args, **kwargs)
    return decorated_function


def require_params(*params):
    """Require specific request parameters"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            missing = []
            data = request.get_json() if request.is_json else request.args

            for param in params:
                if param not in data:
                    missing.append(param)

            if missing:
                return jsonify({
                    'error': 'Missing required parameters',
                    'code': 'MISSING_PARAMETERS',
                    'details': {'missing': missing}
                }), 400

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def paginated(f):
    """Pagination helper decorator"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)

        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20

        kwargs['page'] = page
        kwargs['limit'] = limit

        return f(*args, **kwargs)

    return decorated_function


def log_request_response(f):
    """Log request and response details"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"Request: {request.method} {request.path}")
        if request.is_json:
            logger.debug(f"Body: {request.get_json()}")

        response = f(*args, **kwargs)

        status_code = response[1] if isinstance(response, tuple) else 200
        logger.info(f"Response: {status_code}")

        return response

    return decorated_function


def require_file():
    """Require file upload in request"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if 'file' not in request.files:
                return jsonify({
                    'error': 'No file provided',
                    'code': 'NO_FILE'
                }), 400

            file = request.files['file']
            if file.filename == '':
                return jsonify({
                    'error': 'No file selected',
                    'code': 'EMPTY_FILE'
                }), 400

            return f(*args, **kwargs)

        return decorated_function
    return decorator
