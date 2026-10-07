# Authentication System Setup Guide

This guide covers the complete authentication system implementation in TDIS (Tender Document Information System).

## Overview

The TDIS application now includes a comprehensive authentication system with:
- User registration and login
- JWT token-based authentication
- Password hashing with bcrypt
- Role-based access control (Admin/User)
- User management for administrators
- Profile management for all users
- Protected routes and API endpoints

## Architecture

### Backend Components

1. **auth.py** - Core authentication module
   - Password hashing and verification (bcrypt)
   - JWT token generation and validation
   - User CRUD operations
   - Decorators: `@token_required`, `@admin_required`

2. **auth_routes.py** - Authentication API endpoints
   - `/api/auth/register` - User registration
   - `/api/auth/login` - User login
   - `/api/auth/validate-token` - Token validation
   - `/api/auth/me` - Get/update current user profile
   - `/api/auth/change-password` - Change password
   - `/api/auth/users` - User management (admin only)
   - `/api/auth/users/:id` - Individual user operations (admin only)

3. **models.py** - Updated User model
   - Fields: email, password_hash, name, is_active, is_admin, created_at, last_login
   - Flask-Login integration

### Frontend Components

1. **authService.js** - Auth API client
   - Token management (localStorage)
   - User authentication state
   - API calls for all auth endpoints

2. **Components**
   - `Login.js` - Login page
   - `Register.js` - Registration page
   - `Profile.js` - User profile and password change
   - `UserManagement.js` - Admin user management
   - `Navigation.js` - Header with user menu
   - `ProtectedRoute.js` - Route guard component

3. **Routing** - React Router v6
   - Public routes: `/login`, `/register`
   - Protected routes: `/`, `/profile`
   - Admin routes: `/users`

## Setup Instructions

### 1. Backend Setup

The backend is already configured. Key environment variables in `.env`:

```env
SECRET_KEY=<64-character-hex-secret>
JWT_SECRET_KEY=<uses-SECRET_KEY-if-not-set>
JWT_EXPIRATION_HOURS=24
```

### 2. Default Users

Six default users are created on first run:

**Administrators:**
- elsie@tia-solutions.co.za (Admin)
- mubva@tia-solutions.co.za (Admin)

**Regular Users:**
- boitumelo@tia-solutions.co.za
- dumisani@tia-solutions.co.za
- nhlanhla@tia-solutions.co.za
- keitumetse@tia-solutions.co.za

**Default Password for All:** `TempPass123!`

⚠️ **IMPORTANT:** Users should change their passwords immediately after first login.

### 3. Frontend Setup

The frontend routing is configured in `App.js`. No additional configuration needed.

### 4. Starting the Application

**Backend:**
```bash
# Activate virtual environment
.venv\Scripts\activate

# Start Flask server
python app.py
```

**Frontend:**
```bash
cd frontend
npm start
```

## Usage Guide

### First-Time Login

1. Navigate to `http://localhost:3000`
2. You'll be redirected to the login page
3. Use one of the default credentials:
   - Email: `elsie@tia-solutions.co.za`
   - Password: `TempPass123!`
4. After login, change your password from the Profile page

### User Registration

New users can register at `/register`:
- Email must be unique
- Password requirements:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one number
  - At least one special character

### User Management (Admin Only)

Administrators can:
1. View all users at `/users`
2. Activate/deactivate user accounts
3. Delete users
4. View user details

### Profile Management

All users can:
1. Update their name at `/profile`
2. Change their password
3. View their role and account creation date

## Security Features

### Password Security
- Passwords hashed with bcrypt (10 rounds)
- Strong password requirements enforced
- Secure password change workflow

### Token Security
- JWT tokens with configurable expiration (default: 24 hours)
- Tokens stored in localStorage
- Automatic token refresh on API calls
- Automatic logout on token expiration (401 responses)

### API Security
- All API endpoints (except `/api/health`) require authentication
- Authorization header: `Bearer <token>`
- Admin-only endpoints protected with `@admin_required` decorator
- User can only modify their own profile

### Route Security
- Frontend routes protected with `ProtectedRoute` component
- Automatic redirect to `/login` for unauthenticated users
- Admin routes require admin role
- Non-admins redirected to home if accessing admin routes

## API Authentication

All API requests (except health check) must include the JWT token:

```javascript
// Automatically handled by api.js
// Token from localStorage is included in all requests

// Example manual call:
fetch('http://localhost:5000/api/results', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
})
```

## Common Operations

### Check if User is Authenticated

```javascript
import { isAuthenticated } from './services/authService';

if (isAuthenticated()) {
  // User is logged in
}
```

### Check User Role

```javascript
import { hasRole } from './services/authService';

if (hasRole('admin')) {
  // User is an administrator
}
```

### Get Current User

```javascript
import { getCurrentUser } from './services/authService';

const user = await getCurrentUser();
console.log(user.email, user.name, user.is_admin);
```

### Logout

```javascript
import { logout } from './services/authService';

logout(); // Clears token and user from localStorage
window.location.href = '/login';
```

## Troubleshooting

### Issue: "Token expired" or frequent logouts
**Solution:** Increase JWT expiration in `.env`:
```env
JWT_EXPIRATION_HOURS=48
```

### Issue: "Invalid token" errors
**Solution:** 
1. Clear browser localStorage
2. Restart backend server
3. Login again

### Issue: Cannot access admin routes
**Solution:** 
1. Verify user has `is_admin=True` in database
2. Check browser console for role verification
3. Re-login to refresh token

### Issue: API returns 401 Unauthorized
**Solution:**
1. Check token exists in localStorage
2. Verify SECRET_KEY hasn't changed
3. Check token expiration
4. Login again

## Production Considerations

### Before Deploying

1. **Change Default Passwords**
   - All default users must change passwords
   - Or delete default users and create new ones

2. **Secure SECRET_KEY**
   - Use environment-specific secrets
   - Never commit `.env` to version control
   - Use secrets management (Azure Key Vault, AWS Secrets Manager)

3. **HTTPS Only**
   - Enable HTTPS for production
   - Set secure cookie flags
   - Enable HSTS headers

4. **Token Configuration**
   - Adjust JWT expiration based on security requirements
   - Consider refresh token implementation
   - Implement token revocation if needed

5. **Password Policy**
   - Enforce password changes every 90 days
   - Implement password history (prevent reuse)
   - Add account lockout after failed attempts

6. **Monitoring**
   - Log authentication attempts
   - Monitor for brute force attacks
   - Track suspicious activity

## API Reference

### POST /api/auth/register
Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "John Doe"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "is_admin": false
  }
}
```

### POST /api/auth/login
Authenticate user and receive token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "is_admin": false
  }
}
```

### GET /api/auth/me
Get current user profile.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "is_admin": false,
  "is_active": true,
  "created_at": "2026-08-03T10:00:00Z",
  "last_login": "2026-08-03T14:30:00Z"
}
```

### PUT /api/auth/me
Update current user profile.

**Request:**
```json
{
  "name": "Jane Doe"
}
```

### POST /api/auth/change-password
Change user password.

**Request:**
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

### GET /api/auth/users (Admin Only)
List all users.

**Response:**
```json
{
  "users": [
    {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "is_admin": false,
      "is_active": true
    }
  ]
}
```

### DELETE /api/auth/users/:id (Admin Only)
Delete a user.

### POST /api/auth/users/:id/activate (Admin Only)
Activate or deactivate a user.

**Request:**
```json
{
  "is_active": false
}
```

## Support

For issues or questions:
1. Check the logs: `logs/app.log` and `logs/error.log`
2. Review browser console for frontend errors
3. Verify backend is running: `http://localhost:5000/api/health`
4. Check database: `instance/tender.db`

---

**Last Updated:** August 3, 2026  
**Version:** 1.0.0
