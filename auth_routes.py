"""
Authentication Routes for TDIS
==============================

Provides API endpoints for:
- User registration
- User login
- User management (CRUD)
- Password management
- Token validation
"""

from flask import Blueprint, request, jsonify, current_app
from models import db, User
from auth import (
    create_user, authenticate_user, update_user, delete_user, hard_delete_user,
    token_required, admin_required, validate_password_strength, generate_token
)
from validators import ValidationError
from logger import get_logger
from email_validator import validate_email, EmailNotValidError
from email_service import get_email_service

logger = get_logger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# Public Routes (No Authentication Required)
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    
    Request Body:
        {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "SecurePass123!",
            "is_admin": false  # optional, default false
        }
    
    Returns:
        201: User created successfully with token
        400: Validation error
        409: User already exists
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('name') or not data.get('email') or not data.get('password'):
            return jsonify({
                'error': 'Name, email, and password are required'
            }), 400
        
        name = data['name'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        is_admin = data.get('is_admin', False)
        
        # Validate email format
        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError as e:
            return jsonify({'error': f'Invalid email: {str(e)}'}), 400
        
        # Validate password strength
        is_valid, errors = validate_password_strength(password)
        if not is_valid:
            return jsonify({
                'error': 'Password does not meet requirements',
                'details': errors
            }), 400
        
        # Create user
        user = create_user(name, email, password, is_admin)
        
        # Generate token
        token = generate_token(user)
        
        logger.info(f"New user registered: {user.name} ({user.email})")
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'token': token
        }), 201
        
    except ValueError as e:
        logger.warning(f"Registration failed: {str(e)}")
        return jsonify({'error': str(e)}), 409
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login
    
    Request Body:
        {
            "email": "john@example.com",
            "password": "SecurePass123!"
        }
    
    Returns:
        200: Login successful with token
        400: Missing credentials
        401: Invalid credentials
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'error': 'Email and password are required'
            }), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Authenticate user
        user, token = authenticate_user(email, password)
        
        if not user:
            return jsonify({
                'error': 'Invalid email or password'
            }), 401
        
        logger.info(f"User logged in: {user.name} ({user.email})")
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'token': token
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500


@auth_bp.route('/validate-token', methods=['POST'])
def validate_token():
    """
    Validate a JWT token
    
    Request Body:
        {
            "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
        }
    
    Returns:
        200: Token is valid
        400: Missing token
        401: Invalid or expired token
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('token'):
            return jsonify({'error': 'Token is required'}), 400
        
        from auth import decode_token
        
        try:
            payload = decode_token(data['token'])
            user = User.query.get(payload['user_id'])
            
            if not user or not user.is_active:
                return jsonify({'error': 'User not found or inactive'}), 401
            
            return jsonify({
                'valid': True,
                'user': user.to_dict()
            }), 200
            
        except Exception as e:
            return jsonify({
                'valid': False,
                'error': str(e)
            }), 401
            
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return jsonify({'error': 'Validation failed'}), 500


# ─────────────────────────────────────────────────────────────────────────────
# Protected Routes (Authentication Required)
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """
    Get current user profile
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: Current user information
        401: Unauthorized
    """
    return jsonify({
        'user': current_user.to_dict()
    }), 200


@auth_bp.route('/me', methods=['PUT'])
@token_required
def update_current_user(current_user):
    """
    Update current user profile
    
    Headers:
        Authorization: Bearer <token>
    
    Request Body:
        {
            "name": "New Name",          # optional
            "email": "new@example.com",  # optional
            "password": "NewPass123!"    # optional
        }
    
    Returns:
        200: Profile updated successfully
        400: Validation error
        401: Unauthorized
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate email if provided
        if 'email' in data and data['email']:
            try:
                valid = validate_email(data['email'].strip().lower())
                data['email'] = valid.email
            except EmailNotValidError as e:
                return jsonify({'error': f'Invalid email: {str(e)}'}), 400
        
        # Validate password if provided
        if 'password' in data and data['password']:
            is_valid, errors = validate_password_strength(data['password'])
            if not is_valid:
                return jsonify({
                    'error': 'Password does not meet requirements',
                    'details': errors
                }), 400
        
        # Update user
        updated_user = update_user(current_user.id, **data)
        
        # Generate new token
        token = generate_token(updated_user)
        
        logger.info(f"User updated profile: {updated_user.name}")
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': updated_user.to_dict(),
            'token': token
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        return jsonify({'error': 'Update failed'}), 500


@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """
    Change current user password
    
    Headers:
        Authorization: Bearer <token>
    
    Request Body:
        {
            "current_password": "OldPass123!",  # optional for temp password users
            "new_password": "NewPass123!"
        }
    
    Returns:
        200: Password changed successfully
        400: Validation error
        401: Current password incorrect
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('new_password'):
            return jsonify({
                'error': 'New password is required'
            }), 400
        
        from auth import verify_password
        
        # If user has must_change_password flag, allow password change without current password
        if not current_user.must_change_password:
            # For normal password changes, require current password
            if not data.get('current_password'):
                return jsonify({
                    'error': 'Current password is required'
                }), 400
            
            # Verify current password
            if not verify_password(data['current_password'], current_user.password_hash):
                return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Validate new password
        is_valid, errors = validate_password_strength(data['new_password'])
        if not is_valid:
            return jsonify({
                'error': 'New password does not meet requirements',
                'details': errors
            }), 400
        
        # Update password and clear must_change_password flag
        update_user(current_user.id, password=data['new_password'], must_change_password=False)
        
        logger.info(f"User changed password: {current_user.name}")
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        return jsonify({'error': 'Password change failed'}), 500


# ─────────────────────────────────────────────────────────────────────────────
# Admin Routes (Admin Privileges Required)
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route('/users', methods=['GET'])
@token_required
def list_users(current_user):
    """
    List all users
    
    Headers:
        Authorization: Bearer <token>
    
    Query Parameters:
        include_inactive: Include inactive users (default: false)
        page: Page number (default: 1)
        limit: Items per page (default: 50)
    
    Returns:
        200: List of users
        401: Unauthorized
    """
    try:
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)
        
        query = User.query
        
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        users = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=limit, error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'total': users.total,
            'page': page,
            'pages': users.pages
        }), 200
        
    except Exception as e:
        logger.error(f"List users error: {str(e)}")
        return jsonify({'error': 'Failed to list users'}), 500


@auth_bp.route('/users', methods=['POST'])
@admin_required
def create_user_by_admin(current_user):
    """
    Create a new user (admin only)
    
    Headers:
        Authorization: Bearer <token>
    
    Request Body:
        {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "SecurePass123!",  # optional - if not provided, temp password generated
            "is_admin": false,  # optional, default false
            "must_change_password": true  # optional, default true for auto-generated passwords
        }
    
    Returns:
        201: User created successfully with temporary password (if generated)
        400: Validation error
        409: User already exists
        403: Not admin
    """
    try:
        import secrets
        import string
        
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('name') or not data.get('email'):
            return jsonify({
                'error': 'Name and email are required'
            }), 400
        
        name = data['name'].strip()
        email = data['email'].strip().lower()
        is_admin = data.get('is_admin', False)
        
        # Generate temporary password if not provided
        temp_password_generated = False
        if not data.get('password'):
            # Generate a secure temporary password
            alphabet = string.ascii_letters + string.digits + "!@#$%"
            password = ''.join(secrets.choice(alphabet) for i in range(12))
            # Ensure it meets requirements
            password = 'Temp' + password + '1!'
            temp_password_generated = True
            must_change_password = True
        else:
            password = data['password']
            must_change_password = data.get('must_change_password', False)
        
        # Validate email format
        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError as e:
            return jsonify({'error': f'Invalid email: {str(e)}'}), 400
        
        # Validate password strength (only if manually provided)
        if not temp_password_generated:
            is_valid, errors = validate_password_strength(password)
            if not is_valid:
                return jsonify({
                    'error': 'Password does not meet requirements',
                    'details': errors
                }), 400
        
        # Create user with must_change_password flag
        user = create_user(name, email, password, is_admin, must_change_password)
        
        logger.info(f"Admin {current_user.email} created new user: {user.name} ({user.email})")
        
        # Send email notification if temporary password was generated
        if temp_password_generated:
            try:
                email_service = get_email_service()
                if email_service and email_service.enabled:
                    email_service.send_temporary_password_email(
                        user_name=user.name,
                        user_email=user.email,
                        temporary_password=password,
                        admin_name=current_user.name
                    )
                    logger.info(f"Temporary password email sent to {user.email}")
                else:
                    logger.warning(f"Email service not configured - temporary password not sent to {user.email}")
            except Exception as e:
                logger.error(f"Failed to send temporary password email: {str(e)}")
                # Don't fail user creation if email fails
        
        response_data = {
            'message': 'User created successfully',
            'user': user.to_dict()
        }
        
        # Include temporary password in response if generated
        if temp_password_generated:
            response_data['temporary_password'] = password
            response_data['message'] = 'User created successfully with temporary password'
        
        return jsonify(response_data), 201
        
    except ValueError as e:
        logger.warning(f"User creation failed: {str(e)}")
        return jsonify({'error': str(e)}), 409
    except Exception as e:
        logger.error(f"User creation error: {str(e)}")
        return jsonify({'error': 'User creation failed'}), 500


@auth_bp.route('/users/<user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
    """
    Get user by ID
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: User information
        404: User not found
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        return jsonify({'error': 'Failed to get user'}), 500


@auth_bp.route('/users/<user_id>', methods=['PUT'])
@admin_required
def update_user_by_admin(current_user, user_id):
    """
    Update user (admin only)
    
    Headers:
        Authorization: Bearer <token>
    
    Request Body:
        {
            "name": "New Name",       # optional
            "email": "new@email.com", # optional
            "password": "NewPass",    # optional
            "is_active": true,        # optional
            "is_admin": false         # optional
        }
    
    Returns:
        200: User updated successfully
        400: Validation error
        403: Forbidden (not admin)
        404: User not found
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate email if provided
        if 'email' in data and data['email']:
            try:
                valid = validate_email(data['email'].strip().lower())
                data['email'] = valid.email
            except EmailNotValidError as e:
                return jsonify({'error': f'Invalid email: {str(e)}'}), 400
        
        # Validate password if provided
        if 'password' in data and data['password']:
            is_valid, errors = validate_password_strength(data['password'])
            if not is_valid:
                return jsonify({
                    'error': 'Password does not meet requirements',
                    'details': errors
                }), 400
        
        # Update user
        updated_user = update_user(user_id, **data)
        
        logger.info(f"Admin {current_user.name} updated user: {updated_user.name}")
        
        return jsonify({
            'message': 'User updated successfully',
            'user': updated_user.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        return jsonify({'error': 'Failed to update user'}), 500


@auth_bp.route('/users/<user_id>', methods=['DELETE'])
@admin_required
def delete_user_by_admin(current_user, user_id):
    """
    Delete user (admin only) - soft delete by deactivating
    
    Headers:
        Authorization: Bearer <token>
    
    Query Parameters:
        hard: Permanently delete user (default: false)
    
    Returns:
        200: User deleted successfully
        403: Forbidden (not admin or trying to delete self)
        404: User not found
    """
    try:
        if user_id == current_user.id:
            return jsonify({'error': 'Cannot delete your own account'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        hard = request.args.get('hard', 'false').lower() == 'true'
        
        if hard:
            hard_delete_user(user_id)
            message = 'User permanently deleted'
            logger.warning(f"Admin {current_user.name} permanently deleted user: {user.name}")
        else:
            delete_user(user_id)
            message = 'User deactivated'
            logger.info(f"Admin {current_user.name} deactivated user: {user.name}")
        
        return jsonify({
            'message': message
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        return jsonify({'error': 'Failed to delete user'}), 500


@auth_bp.route('/users/<user_id>/activate', methods=['POST'])
@admin_required
def activate_user(current_user, user_id):
    """
    Activate a deactivated user (admin only)
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: User activated successfully
        403: Forbidden (not admin)
        404: User not found
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.is_active = True
        db.session.commit()
        
        logger.info(f"Admin {current_user.name} activated user: {user.name}")
        
        return jsonify({
            'message': 'User activated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Activate user error: {str(e)}")
        return jsonify({'error': 'Failed to activate user'}), 500


@auth_bp.route('/users/<user_id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(current_user, user_id):
    """
    Reset user password and generate new temporary password (admin only)
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        200: Password reset with new temporary password
        403: Forbidden (not admin)
        404: User not found
    """
    try:
        import secrets
        import string
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Generate a new secure temporary password
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        temp_password = ''.join(secrets.choice(alphabet) for i in range(12))
        temp_password = 'Temp' + temp_password + '1!'
        
        # Update user password and set must_change_password flag
        update_user(user_id, password=temp_password, must_change_password=True)
        
        logger.info(f"Admin {current_user.name} reset password for user: {user.name}")
        
        # Send email notification for password reset
        try:
            email_service = get_email_service()
            if email_service and email_service.enabled:
                email_service.send_password_reset_email(
                    user_name=user.name,
                    user_email=user.email,
                    new_temporary_password=temp_password,
                    admin_name=current_user.name
                )
                logger.info(f"Password reset email sent to {user.email}")
            else:
                logger.warning(f"Email service not configured - password reset notification not sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            # Don't fail password reset if email fails
        
        return jsonify({
            'message': 'Password reset successfully',
            'temporary_password': temp_password,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        return jsonify({'error': 'Failed to reset password'}), 500
