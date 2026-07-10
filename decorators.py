"""Custom decorators for Flask routes"""

import time
import functools
from flask import jsonify, request
from logger import get_logger
from cache import cache
import json

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


def cache_route(expire=3600):
    """Cache route responses"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Build cache key from path and params
            cache_key = f"route:{request.path}:{json.dumps(request.args, sort_keys=True)}"
            
            # Check cache
            cached = cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for route {request.path}")
                return cached
            
            # Execute function
            response = f(*args, **kwargs)
            
            # Cache if successful
            if isinstance(response, tuple) and response[1] == 200:
                cache.set(cache_key, response[0], expire)
            elif not isinstance(response, tuple):
                cache.set(cache_key, response, expire)
            
            return response
        
        return decorated_function
    return decorator


def paginated(f):
    """Pagination helper decorator"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # Validate pagination
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20
        
        kwargs['page'] = page
        kwargs['limit'] = limit
        
        return f(*args, **kwargs)
    
    return decorated_function


def async_task(task_func):
    """Decorator to run function as async task"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Try to queue as async task
                task = task_func.delay(*args, **kwargs)
                return jsonify({
                    'status': 'queued',
                    'task_id': task.id,
                    'message': 'Task queued for processing'
                }), 202
            except Exception as e:
                logger.warning(f"Async queueing failed, running sync: {str(e)}")
                # Fallback to sync execution
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def log_request_response(f):
    """Log request and response details"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"Request: {request.method} {request.path}")
        logger.debug(f"Headers: {dict(request.headers)}")
        if request.is_json:
            logger.debug(f"Body: {request.get_json()}")
        
        response = f(*args, **kwargs)
        
        status_code = response[1] if isinstance(response, tuple) else 200
        logger.info(f"Response: {status_code}")
        
        return response
    
    return decorated_function


def handle_cors(f):
    """Add CORS headers to response"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        if isinstance(response, tuple):
            response_obj = response[0]
            status = response[1] if len(response) > 1 else 200
            headers = response[2] if len(response) > 2 else {}
        else:
            response_obj = response
            status = 200
            headers = {}
        
        headers.update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key'
        })
        
        return response_obj, status, headers
    
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


def rate_limit(calls_per_minute=60):
    """Rate limiting decorator (placeholder - real rate limiting in config)"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Placeholder for rate limiting logic
            # Real implementation should use cache or dedicated service
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
