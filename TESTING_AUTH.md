# Authentication System Testing Guide

## Quick Start Testing

### 1. Access the Application

1. **Backend is running** at: http://127.0.0.1:5000
2. **Frontend is running** at: http://localhost:3000
3. Navigate to: http://localhost:3000

### 2. Test Login Flow

When you access http://localhost:3000, you should be automatically redirected to the login page.

**Test Credentials:**
- Email: `elsie@tia-solutions.co.za`
- Password: `TempPass123!`

or

- Email: `mubva@tia-solutions.co.za`
- Password: `TempPass123!`

### 3. Test Registration

1. Click "Create an account" on the login page
2. Fill in the registration form:
   - **Email:** yourname@tia-solutions.co.za
   - **Password:** YourPass123!
   - **Name:** Your Name
3. Click "Register"
4. You should be redirected to login
5. Login with your new credentials

### 4. Test Profile Management

After logging in:
1. Click on your avatar/name in the top right corner
2. Select "Profile" from the dropdown menu
3. Update your name
4. Test changing your password

### 5. Test User Management (Admin Only)

If logged in as admin (elsie or mubva):
1. Click "User Management" in the navigation bar
2. View all users
3. Test activating/deactivating a user
4. Test deleting a user (be careful!)

### 6. Test Logout

1. Click on your avatar/name in the top right
2. Select "Logout"
3. You should be redirected to the login page
4. Try accessing http://localhost:3000 - should redirect to login

## Testing Checklist

### Authentication Flow
- [ ] Accessing homepage redirects to login when not authenticated
- [ ] Login with valid credentials succeeds
- [ ] Login with invalid credentials shows error
- [ ] Login with inactive user account shows error
- [ ] Logout clears session and redirects to login

### Registration
- [ ] Register with valid data creates account
- [ ] Register with existing email shows error
- [ ] Register with weak password shows validation errors
- [ ] Newly registered user can login

### Protected Routes
- [ ] `/` (home) requires authentication
- [ ] `/profile` requires authentication
- [ ] `/users` requires admin role
- [ ] Non-admin accessing `/users` redirects to home
- [ ] Unauthenticated user accessing any protected route redirects to login

### Profile Management
- [ ] User can view their profile
- [ ] User can update their name
- [ ] User cannot change their email
- [ ] User can change their password with correct current password
- [ ] Changing password with wrong current password shows error
- [ ] Weak new password shows validation error

### User Management (Admin)
- [ ] Admin can view all users
- [ ] Admin can activate/deactivate users
- [ ] Admin can delete users
- [ ] Admin cannot delete themselves
- [ ] Regular user cannot access user management

### Token Handling
- [ ] Token is included in all API requests
- [ ] Expired token triggers logout
- [ ] Invalid token triggers logout
- [ ] Token persists across page refreshes

### UI/UX
- [ ] Navigation shows user name and avatar
- [ ] User menu shows current user info and role badge
- [ ] Active navigation item is highlighted
- [ ] Admin sees "User Management" link in navigation
- [ ] Regular user does not see "User Management" link

## Test Scenarios

### Scenario 1: First-Time User
1. Access application
2. Register new account
3. Login with new credentials
4. Update profile information
5. Change password
6. Logout and login with new password

### Scenario 2: Admin Workflow
1. Login as admin (elsie or mubva)
2. Navigate to User Management
3. View all users
4. Create a new user via registration page
5. Return to User Management
6. Deactivate the new user
7. Try to login as deactivated user (should fail)
8. Reactivate the user
9. Login as that user (should succeed)

### Scenario 3: Security Testing
1. Try accessing `/users` without logging in → Should redirect to login
2. Login as regular user
3. Try accessing `/users` → Should redirect to home
4. Copy token from localStorage
5. Logout
6. Try manually setting token in localStorage → Should work until token expires
7. Modify token slightly → Should trigger logout on next API call

### Scenario 4: Password Security
1. Try registering with password "password" → Should fail (weak password)
2. Try registering with password "Pass123!" → Should fail (no lowercase? Check requirements)
3. Try registering with password "Password123!" → Should succeed
4. Login and try changing password with wrong current password → Should fail
5. Change password successfully → Should succeed and require new password on next login

## Known Issues to Watch For

### Issue: Token Not Included in Requests
**Symptoms:** 401 errors on all API calls after login
**Check:** Browser console → Network tab → Request headers → Should see `Authorization: Bearer <token>`

### Issue: Infinite Redirect Loop
**Symptoms:** Page keeps redirecting between login and home
**Check:** 
1. Browser console for errors
2. localStorage for token
3. Backend logs for authentication errors

### Issue: Cannot Access Admin Routes
**Symptoms:** Admin user redirected from `/users`
**Check:**
1. User's `is_admin` field in database
2. Token contains correct role
3. Browser console for role check errors

### Issue: Profile Updates Not Saving
**Symptoms:** Profile form submits but data doesn't change
**Check:**
1. Network tab for API response
2. Backend logs for errors
3. Database for actual values

## Debugging

### Check Authentication State
Open browser console and run:
```javascript
// Check if authenticated
console.log('Token:', localStorage.getItem('token'));
console.log('User:', localStorage.getItem('user'));

// Check user details
import { getCurrentUser, isAuthenticated, hasRole } from './services/authService';
console.log('Is authenticated:', isAuthenticated());
console.log('Is admin:', hasRole('admin'));
getCurrentUser().then(user => console.log('Current user:', user));
```

### Check API Requests
Network tab → Filter by "XHR" → Look for:
- `/api/auth/login` - Should return token
- `/api/auth/me` - Should return user data
- `/api/results` - Should include Authorization header

### Check Backend
Backend logs at: `logs/app.log` and `logs/error.log`

Look for:
- Authentication attempts
- Token validation errors
- Database errors

## Expected Behavior

### Successful Login Response
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "elsie@tia-solutions.co.za",
    "name": "Elsie",
    "is_admin": true,
    "is_active": true
  }
}
```

### Successful API Request with Auth
Request headers should include:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Failed Authentication Response
```json
{
  "error": "Invalid credentials",
  "code": "INVALID_CREDENTIALS"
}
```

## Performance Checks

- [ ] Login completes in < 2 seconds
- [ ] Profile page loads in < 1 second
- [ ] User management page loads in < 2 seconds
- [ ] Password change completes in < 2 seconds
- [ ] No visible lag when navigating between pages

## Security Checks

- [ ] Passwords are never visible in network requests
- [ ] Passwords are never logged to console
- [ ] Token is never visible in URL
- [ ] Token is included only in Authorization header
- [ ] Inactive users cannot login
- [ ] Deleted users cannot login

## Next Steps After Testing

1. **Change all default passwords**
2. **Create real user accounts**
3. **Delete or deactivate test accounts**
4. **Review logs for any errors**
5. **Test with multiple browsers**
6. **Test on mobile devices**
7. **Verify HTTPS in production**

---

**Happy Testing!** 🎉

If you encounter any issues, check:
1. Browser console (F12)
2. Network tab for API responses
3. Backend logs: `logs/app.log`
4. Database: `instance/tender.db`
