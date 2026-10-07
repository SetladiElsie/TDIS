"""
Authentication Module for TDIS
==============================

Provides user authentication, password hashing, JWT tokens, and login management.

Features:
- Password hashing with bcrypt
- JWT token generation and validation
- User registration and login
- Session management
- Role-based access control (admin/user)
"""

import jwt
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, current_user
from models import db, User
from logger import get_logger

logger = get_logger(__name__)

# Initialize Flask extensions
bcrypt = Bcrypt()
login_manager = LoginManager()


def init_auth(app):
    """Initialize authentication extensions with the Flask app"""
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'api.login'
    login_manager.login_message = 'Please log in to access this page.'
    logger.info("Authentication system initialized")


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(user_id)


# ─────────────────────────────────────────────────────────────────────────────
# Password Hashing
# ─────────────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return bcrypt.generate_password_hash(password).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        password: Plain text password
        password_hash: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.check_password_hash(password_hash, password)


# ─────────────────────────────────────────────────────────────────────────────
# JWT Token Management
# ─────────────────────────────────────────────────────────────────────────────

def generate_token(user: User, expires_in: int = 86400) -> str:
    """
    Generate JWT token for user
    
    Args:
        user: User object
        expires_in: Token expiration time in seconds (default: 24 hours)
        
    Returns:
        JWT token string
    """
    payload = {
        'user_id': user.id,
        'email': user.email,
        'name': user.name,
        'is_admin': user.is_admin,
        'exp': datetime.utcnow() + timedelta(seconds=expires_in),
        'iat': datetime.utcnow(),
    }
    
    token = jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    return token


def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload dict
        
    Raises:
        jwt.ExpiredSignatureError: Token has expired
        jwt.InvalidTokenError: Token is invalid
    """
    return jwt.decode(
        token,
        current_app.config['SECRET_KEY'],
        algorithms=['HS256']
    )


# ─────────────────────────────────────────────────────────────────────────────
# User Management
# ─────────────────────────────────────────────────────────────────────────────

def create_user(name: str, email: str, password: str, is_admin: bool = False, must_change_password: bool = False) -> User:
    """
    Create a new user
    
    Args:
        name: User's full name
        email: User's email address
        password: Plain text password
        is_admin: Whether user has admin privileges
        must_change_password: Whether user must change password on first login
        
    Returns:
        Created User object
        
    Raises:
        ValueError: If user already exists or validation fails
    """
    # Validate inputs
    if not name or not email or not password:
        raise ValueError("Name, email, and password are required")
    
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    
    # Check if user already exists
    existing_user = User.query.filter(
        (User.email == email) | (User.name == name)
    ).first()
    
    if existing_user:
        if existing_user.email == email:
            raise ValueError(f"User with email {email} already exists")
        else:
            raise ValueError(f"User with name {name} already exists")
    
    # Create user
    user = User(
        id=str(uuid.uuid4()),
        name=name,
        email=email,
        password_hash=hash_password(password),
        is_admin=is_admin,
        is_active=True,
        must_change_password=must_change_password,
        created_at=datetime.utcnow()
    )
    
    db.session.add(user)
    db.session.commit()
    
    logger.info(f"User created: {name} ({email}), must_change_password={must_change_password}")
    return user


def authenticate_user(email: str, password: str) -> tuple:
    """
    Authenticate user with email and password
    
    Args:
        email: User's email
        password: Plain text password
        
    Returns:
        Tuple of (user, token) if successful, (None, None) if failed
    """
    user = User.query.filter_by(email=email).first()
    
    if not user:
        logger.warning(f"Login attempt with non-existent email: {email}")
        return None, None
    
    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {email}")
        return None, None
    
    if not verify_password(password, user.password_hash):
        logger.warning(f"Failed login attempt for user: {email}")
        return None, None
    
    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Generate token
    token = generate_token(user)
    
    logger.info(f"User logged in: {user.name} ({user.email})")
    return user, token


def update_user(user_id: str, **kwargs) -> User:
    """
    Update user information
    
    Args:
        user_id: User ID
        **kwargs: Fields to update (name, email, password, is_active, is_admin)
        
    Returns:
        Updated User object
        
    Raises:
        ValueError: If user not found or validation fails
    """
    user = User.query.get(user_id)
    if not user:
        raise ValueError(f"User not found: {user_id}")
    
    # Update allowed fields
    if 'name' in kwargs and kwargs['name']:
        # Check if name is already taken by another user
        existing = User.query.filter(
            User.name == kwargs['name'],
            User.id != user_id
        ).first()
        if existing:
            raise ValueError(f"Name {kwargs['name']} is already taken")
        user.name = kwargs['name']
    
    if 'email' in kwargs and kwargs['email']:
        # Check if email is already taken by another user
        existing = User.query.filter(
            User.email == kwargs['email'],
            User.id != user_id
        ).first()
        if existing:
            raise ValueError(f"Email {kwargs['email']} is already taken")
        user.email = kwargs['email']
    
    if 'password' in kwargs and kwargs['password']:
        if len(kwargs['password']) < 8:
            raise ValueError("Password must be at least 8 characters long")
        user.password_hash = hash_password(kwargs['password'])
    
    if 'is_active' in kwargs:
        user.is_active = kwargs['is_active']
    
    if 'is_admin' in kwargs:
        user.is_admin = kwargs['is_admin']
    
    db.session.commit()
    logger.info(f"User updated: {user.name} ({user.email})")
    return user


def delete_user(user_id: str) -> bool:
    """
    Delete a user (soft delete by deactivating)
    
    Args:
        user_id: User ID to delete
        
    Returns:
        True if successful
        
    Raises:
        ValueError: If user not found
    """
    user = User.query.get(user_id)
    if not user:
        raise ValueError(f"User not found: {user_id}")
    
    # Soft delete (deactivate)
    user.is_active = False
    db.session.commit()
    
    logger.info(f"User deactivated: {user.name} ({user.email})")
    return True


def hard_delete_user(user_id: str) -> bool:
    """
    Permanently delete a user from database
    
    Args:
        user_id: User ID to delete
        
    Returns:
        True if successful
        
    Raises:
        ValueError: If user not found
    """
    user = User.query.get(user_id)
    if not user:
        raise ValueError(f"User not found: {user_id}")
    
    name = user.name
    email = user.email
    
    db.session.delete(user)
    db.session.commit()
    
    logger.warning(f"User permanently deleted: {name} ({email})")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Decorators for Route Protection
# ─────────────────────────────────────────────────────────────────────────────

def token_required(f):
    """
    Decorator to protect routes with JWT token authentication
    
    Usage:
        @app.route('/protected')
        @token_required
        def protected_route(current_user):
            return {'message': f'Hello {current_user.name}'}
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Authentication token is missing'}), 401
        
        try:
            # Decode token
            payload = decode_token(token)
            user_id = payload['user_id']
            
            # Load user
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return jsonify({'error': 'User not found or inactive'}), 401
            
            # Pass user to the route
            return f(user, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401
    
    return decorated


def admin_required(f):
    """
    Decorator to protect routes requiring admin privileges
    
    Usage:
        @app.route('/admin')
        @admin_required
        def admin_route(current_user):
            return {'message': 'Admin access granted'}
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        @token_required
        def check_admin(user, *args, **kwargs):
            if not user.is_admin:
                return jsonify({'error': 'Admin privileges required'}), 403
            return f(user, *args, **kwargs)
        
        return check_admin(*args, **kwargs)
    
    return decorated


# ─────────────────────────────────────────────────────────────────────────────
# Session Management (Optional - for web interface)
# ─────────────────────────────────────────────────────────────────────────────

def login_user_session(user: User, remember: bool = False) -> bool:
    """
    Log in user with Flask-Login session
    
    Args:
        user: User object
        remember: Whether to remember user across sessions
        
    Returns:
        True if successful
    """
    user.last_login = datetime.utcnow()
    db.session.commit()
    return login_user(user, remember=remember)


def logout_user_session() -> None:
    """Log out current user from Flask-Login session"""
    logout_user()


# ─────────────────────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────────────────────

def get_current_user_from_token() -> User:
    """
    Get current user from JWT token in request headers
    
    Returns:
        User object or None if not authenticated
    """
    token = None
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return None
    
    if not token:
        return None
    
    try:
        payload = decode_token(token)
        user = User.query.get(payload['user_id'])
        return user if user and user.is_active else None
    except Exception:
        return None


def validate_password_strength(password: str) -> tuple:
    """
    Validate password strength
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid: bool, errors: list)
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors
