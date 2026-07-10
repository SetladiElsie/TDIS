"""Authentication and API key management"""

import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
import jwt
from flask import request, current_app, jsonify
from errors import UnauthorizedError, ForbiddenError
from logger import get_logger, audit_logger
from sqlalchemy import Column, String, DateTime, Boolean, Integer

logger = get_logger(__name__)


class APIKey:
    """API Key model - add to models.py"""
    
    def __init__(self, user_id, name, key, secret):
        self.user_id = user_id
        self.name = name
        self.key = key
        self.secret = secret
        self.created_at = datetime.utcnow()
        self.last_used = None
        self.is_active = True
        self.request_count = 0
    
    @staticmethod
    def generate_key():
        """Generate secure API key"""
        return 'sk_' + secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_secret():
        """Generate secure API secret"""
        return secrets.token_urlsafe(32)
    
    def mark_used(self):
        """Mark key as used"""
        self.last_used = datetime.utcnow()
        self.request_count += 1


def generate_jwt_token(user_id, expires_in=None):
    """Generate JWT token"""
    if expires_in is None:
        expires_in = current_app.config.get('JWT_EXPIRATION_HOURS', 24)
    
    payload = {
        'user_id': user_id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=expires_in)
    }
    
    token = jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    return token


def verify_jwt_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError('Token has expired')
    except jwt.InvalidTokenError:
        raise UnauthorizedError('Invalid token')


def require_auth(f):
    """Decorator to require authentication via JWT or API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        api_key = request.headers.get('X-API-Key')
        
        user_id = None
        
        if auth_header:
            # JWT authentication
            try:
                parts = auth_header.split()
                if len(parts) != 2 or parts[0].lower() != 'bearer':
                    raise UnauthorizedError('Invalid authorization header format')
                
                token = parts[1]
                payload = verify_jwt_token(token)
                user_id = payload.get('user_id')
                
                if not user_id:
                    raise UnauthorizedError('Invalid token payload')
                
                audit_logger.log_auth_attempt(user_id, True)
            except UnauthorizedError:
                raise
            except Exception as e:
                logger.error(f"JWT verification failed: {str(e)}")
                audit_logger.log_auth_attempt('unknown', False)
                raise UnauthorizedError('Authentication failed')
        
        elif api_key:
            # API key authentication
            # This would verify against database in real implementation
            # For now, just check format
            if not api_key.startswith('sk_'):
                audit_logger.log_auth_attempt('unknown', False)
                raise UnauthorizedError('Invalid API key format')
            
            # In production, lookup key in database
            # from models import db, APIKeyModel
            # key_record = db.session.query(APIKeyModel).filter_by(key=api_key).first()
            # if not key_record or not key_record.is_active:
            #     raise UnauthorizedError('Invalid or inactive API key')
            # user_id = key_record.user_id
            # key_record.mark_used()
            # db.session.commit()
            
            user_id = 'api_key_user'
            audit_logger.log_auth_attempt(user_id, True)
        
        else:
            raise UnauthorizedError('Missing authentication credentials')
        
        # Store user_id in request context
        request.user_id = user_id
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_role(role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'user_id'):
                raise UnauthorizedError('Not authenticated')
            
            # In production, check user role from database
            # For now, just a placeholder
            user_role = 'user'  # Get from database in production
            
            if user_role != role:
                raise ForbiddenError(f'This operation requires {role} role')
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def hash_password(password):
    """Hash password for storage"""
    from werkzeug.security import generate_password_hash
    return generate_password_hash(password)


def verify_password(password_hash, password):
    """Verify password against hash"""
    from werkzeug.security import check_password_hash
    return check_password_hash(password_hash, password)


def create_user_token(user_id, expires_in=24):
    """Create token for user"""
    token = generate_jwt_token(user_id, expires_in)
    logger.info(f"Token created for user {user_id}")
    return token


def revoke_token(token):
    """Revoke a token (add to blacklist in production)"""
    # In production, add to Redis blacklist
    logger.info(f"Token revoked")


class JWTConfig:
    """JWT configuration"""
    ALGORITHM = 'HS256'
    EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))
    REFRESH_EXPIRATION_DAYS = int(os.getenv('JWT_REFRESH_EXPIRATION_DAYS', 7))
