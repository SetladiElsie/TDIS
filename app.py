import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from functools import wraps

from config import config
from models import db
from routes import api
from logger import setup_logging, audit_logger, get_logger
from errors import TenderAPIError
from cache import CacheManager

# Load environment variables
load_dotenv()

logger = get_logger(__name__)


def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize logging first
    setup_logging(app)
    logger.info(f"Flask app created in {config_name} mode")
    
    # Initialize database
    db.init_app(app)
    
    # Initialize cache
    try:
        cache_manager = CacheManager(app.config.get('REDIS_URL', 'redis://localhost:6379/0'))
        app.cache = cache_manager
        logger.info("Cache initialized")
    except Exception as e:
        logger.warning(f"Cache initialization failed: {str(e)}")
        app.cache = None
    
    # Enable CORS with config
    CORS(
        app,
        resources={r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', ['*']),
            "methods": app.config.get('CORS_METHODS', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']),
            "allow_headers": app.config.get('CORS_ALLOW_HEADERS', ['Content-Type', 'Authorization']),
            "supports_credentials": True,
            "max_age": 3600
        }}
    )
    logger.info("CORS enabled")
    
    # Register blueprints
    app.register_blueprint(api, url_prefix=app.config.get('API_PREFIX', '/api'))
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
    
    # Add security headers middleware
    @app.after_request
    def add_security_headers(response):
        """Add security headers to responses"""
        for header, value in app.config.get('SECURITY_HEADERS', {}).items():
            if value:
                response.headers[header] = value
        return response
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        logger.warning(f"Bad request: {str(error)}")
        return jsonify({
            'error': 'Bad request',
            'code': 'BAD_REQUEST',
            'message': str(error.description) if hasattr(error, 'description') else 'Invalid request'
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"Not found: {request.path}")
        return jsonify({
            'error': 'Not found',
            'code': 'NOT_FOUND',
            'message': f'Endpoint {request.path} not found'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        logger.warning(f"Method not allowed: {request.method} {request.path}")
        return jsonify({
            'error': 'Method not allowed',
            'code': 'METHOD_NOT_ALLOWED',
            'message': f'{request.method} not allowed on {request.path}'
        }), 405
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        logger.warning(f"File too large: {request.remote_addr}")
        return jsonify({
            'error': 'File too large',
            'code': 'FILE_TOO_LARGE',
            'message': f'File exceeds maximum size of {app.config.get("MAX_CONTENT_LENGTH", 50*1024*1024) / (1024*1024):.0f}MB',
            'max_size': app.config.get('MAX_CONTENT_LENGTH')
        }), 413
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(TenderAPIError)
    def handle_tender_api_error(error):
        """Handle custom TenderAPI errors"""
        logger.warning(f"API Error ({error.code}): {error.message}")
        response = error.to_dict()
        return jsonify(response), error.status_code
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def index():
        """API information endpoint"""
        return jsonify({
            'name': app.config.get('API_TITLE', 'Tender Document Extraction API'),
            'version': app.config.get('API_VERSION', '1.0.0'),
            'status': 'running',
            'environment': config,
            'endpoints': {
                'upload': 'POST /api/upload',
                'extract': 'POST /api/extract',
                'get_result': 'GET /api/results/<extraction_id>',
                'list_results': 'GET /api/results',
                'export': 'GET /api/export/<extraction_id>',
                'delete': 'DELETE /api/results/<extraction_id>',
                'health': 'GET /api/health',
                'docs': 'GET /api/docs',
                'admin': 'GET /api/admin',
                'backups': 'GET /api/backups',
            },
            'features': {
                'async_processing': app.config.get('ENABLE_ASYNC', False),
                'webhooks': app.config.get('ENABLE_WEBHOOKS', False),
                'ocr_support': app.config.get('ENABLE_OCR', False),
                'ml_extraction': app.config.get('ENABLE_ML', False),
            }
        }), 200
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            # Check database
            db.session.execute('SELECT 1')
            db_status = 'connected'
        except Exception as e:
            logger.warning(f"Database health check failed: {str(e)}")
            db_status = 'disconnected'
        
        # Check cache
        cache_status = 'connected' if app.cache else 'unavailable'
        
        status = 'healthy' if db_status == 'connected' else 'degraded'
        
        return jsonify({
            'status': status,
            'timestamp': os.getenv('CURRENT_TIMESTAMP', 'N/A'),
            'database': db_status,
            'cache': cache_status,
            'version': app.config.get('API_VERSION')
        }), 200
    
    @app.route('/api/docs', methods=['GET'])
    def api_documentation():
        """API documentation endpoint"""
        return jsonify({
            'title': app.config.get('API_TITLE'),
            'version': app.config.get('API_VERSION'),
            'description': 'Tender Document Extraction API',
            'base_url': request.base_url.rstrip('/'),
            'endpoints': {
                'POST /api/upload': {
                    'description': 'Upload a tender document',
                    'required_params': ['file'],
                    'returns': 'upload_id'
                },
                'POST /api/extract': {
                    'description': 'Extract information from uploaded document',
                    'required_params': ['upload_id'],
                    'returns': 'extraction_id'
                },
                'GET /api/results/<extraction_id>': {
                    'description': 'Get extraction results',
                    'returns': 'extracted_data'
                },
                'GET /api/results': {
                    'description': 'List all results',
                    'optional_params': ['page', 'limit', 'search', 'status'],
                    'returns': 'paginated_results'
                },
                'GET /api/export/<extraction_id>': {
                    'description': 'Export results',
                    'optional_params': ['format'],
                    'returns': 'json_or_csv'
                },
                'DELETE /api/results/<extraction_id>': {
                    'description': 'Delete extraction result',
                    'returns': 'success_message'
                }
            }
        }), 200
    
    # Request/response logging
    @app.before_request
    def log_request():
        """Log incoming request"""
        if not request.path.startswith('/static'):
            logger.debug(f"{request.method} {request.path} from {request.remote_addr}")
    
    @app.after_request
    def log_response(response):
        """Log response"""
        if not request.path.startswith('/static'):
            logger.debug(f"Response: {response.status_code} for {request.method} {request.path}")
        return response
    
    logger.info(f"Application initialized successfully")
    
    return app


if __name__ == '__main__':
    app = create_app()

    # Create necessary directories
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
    os.makedirs(app.config.get('BACKUP_FOLDER', 'backups'), exist_ok=True)
    os.makedirs(app.config.get('LOGS_FOLDER', 'logs'), exist_ok=True)

    logger.info("Starting Flask development server")

    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_ENV', 'development') == 'development'
    )
       