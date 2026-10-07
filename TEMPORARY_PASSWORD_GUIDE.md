# Temporary Password System - Testing Guide

## Overview
The Temporary Password System allows administrators to create user accounts with auto-generated secure temporary passwords. Users are required to change these passwords upon first login.

## Features

### 1. Secure Password Generation
- **Auto-generated passwords**: 12-character passwords with format `Temp[random]1!`
- **Character composition**: Includes uppercase, lowercase, digits, and special characters
- **One-time display**: Password is shown only once in a modal after user creation
- **Copy functionality**: One-click copy to clipboard

### 2. Password Change Enforcement
- **Mandatory change**: Users with temporary passwords cannot access the application until they change their password
- **Modal prompt**: Non-dismissible modal overlay that blocks all application access
- **Password validation**: Requires minimum 8 characters with uppercase, lowercase, digit, and special character
- **Secure process**: Requires current temporary password + new password confirmation

### 3. Admin Controls
- **Optional generation**: Checkbox in user creation form to enable/disable temporary password generation
- **Manual override**: Admins can still manually set passwords if needed
- **User feedback**: Clear display of generated password with copy button

## Database Schema

### New Column: `must_change_password`
```sql
ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT 0
```

- **Type**: Boolean
- **Default**: `0` (False)
- **Purpose**: Flags users who must change their password before accessing the application

## API Changes

### Create User Endpoint
**Endpoint**: `POST /api/auth/admin/users`

**Request Body** (with temporary password):
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "is_admin": false,
  "generate_temp_password": true
}
```

**Request Body** (with manual password):
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "password": "ManualPass123!",
  "is_admin": false
}
```

**Response** (with temporary password):
```json
{
  "message": "User created successfully",
  "user": {
    "id": "uuid",
    "name": "John Doe",
    "email": "john@example.com",
    "is_admin": false,
    "is_active": true,
    "must_change_password": true,
    "created_at": "2026-10-06T12:00:00Z"
  },
  "temporary_password": "TempaBc123Xyz!1!"
}
```

### Login Response
```json
{
  "token": "jwt_token",
  "user": {
    "id": "uuid",
    "name": "John Doe",
    "email": "john@example.com",
    "is_admin": false,
    "must_change_password": true
  }
}
```

### Change Password Endpoint
**Endpoint**: `POST /api/auth/change-password`

**Request Body**:
```json
{
  "current_password": "TempaBc123Xyz!1!",
  "new_password": "MyNewSecurePass123!"
}
```

**Response**:
```json
{
  "message": "Password changed successfully"
}
```

## Testing Steps

### Test 1: Create User with Temporary Password

1. **Login as Admin**
   - Navigate to: http://localhost:3000/login
   - Login with admin credentials

2. **Access User Management**
   - Click hamburger menu (☰) next to the logo
   - Select "User Management"

3. **Create New User**
   - Click "Create New User" button
   - Fill in user details:
     - Name: Test User
     - Email: test@example.com
   - Check the "Generate temporary password" checkbox
   - Click "Create User"

4. **Copy Temporary Password**
   - A modal will appear with the generated password
   - Click "Copy to Clipboard" button
   - **IMPORTANT**: Save this password - it won't be shown again!
   - Close the modal

### Test 2: User First Login with Password Change

1. **Logout from Admin Account**
   - Click hamburger menu (☰)
   - Click "Logout"

2. **Login with New User**
   - Navigate to: http://localhost:3000/login
   - Email: test@example.com
   - Password: [paste the temporary password]
   - Click "Login"

3. **Password Change Prompt**
   - You should see a modal titled "Change Your Password"
   - This modal cannot be dismissed - you must change the password
   - Fill in:
     - Current Password: [temporary password]
     - New Password: YourNewPassword123!
     - Confirm New Password: YourNewPassword123!
   - Click "Change Password"

4. **Verify Access**
   - After successful password change, the modal should close
   - You should now have full access to the application
   - The hamburger menu should show your name

### Test 3: Verify Password Change Persists

1. **Logout**
   - Click hamburger menu
   - Click "Logout"

2. **Login Again**
   - Email: test@example.com
   - Password: YourNewPassword123! (the new password)
   - Click "Login"

3. **Verify No Prompt**
   - You should NOT see the password change prompt
   - You should have immediate access to the application

### Test 4: Create User with Manual Password

1. **Login as Admin**
   - Use your admin credentials

2. **Create User Without Temporary Password**
   - Go to User Management
   - Click "Create New User"
   - Fill in:
     - Name: Manual User
     - Email: manual@example.com
     - Password: ManualPassword123!
   - **UNCHECK** "Generate temporary password"
   - Click "Create User"

3. **Verify No Temporary Password Modal**
   - No password display modal should appear
   - User should be created normally

4. **Test Login**
   - Logout and login as manual@example.com
   - Use password: ManualPassword123!
   - Should NOT see password change prompt
   - Should have immediate access

## Security Features

### Password Generation
- Uses `secrets` module (cryptographically secure random)
- Minimum 12 characters
- Guaranteed complexity: `Temp[8-random-chars]1!`
- Cannot be predicted or brute-forced easily

### Password Validation
- Minimum 8 characters
- Must contain:
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character
- Confirmed by re-entering

### Session Management
- Password change clears `must_change_password` flag
- JWT token remains valid after password change
- User data refreshed after password change

## User Experience Flow

```
Admin Creates User (temp password)
         ↓
Admin Sees Password Once (with copy button)
         ↓
Admin Shares Password Securely with User
         ↓
User Logs In with Temporary Password
         ↓
Mandatory Password Change Modal (cannot dismiss)
         ↓
User Changes Password Successfully
         ↓
User Has Full Application Access
         ↓
Future Logins: Use New Password (no prompt)
```

## Troubleshooting

### Issue: Password Change Modal Doesn't Appear
- **Check**: User's `must_change_password` flag in database
- **Solution**: Verify login response includes `must_change_password: true`

### Issue: "Current Password Incorrect"
- **Check**: Ensure you're using the temporary password (not the new one)
- **Solution**: Request password reset if temporary password is lost

### Issue: "Password does not meet requirements"
- **Check**: New password has all required character types
- **Solution**: Include uppercase, lowercase, digit, and special character

### Issue: Modal Can't Be Closed
- **Expected Behavior**: This is intentional security feature
- **Solution**: Complete the password change to proceed

## Files Modified

### Backend
- `models.py`: Added `must_change_password` column to User model
- `auth.py`: Updated `create_user()` function signature
- `auth_routes.py`: Modified user creation endpoint to generate temporary passwords

### Frontend
- `UserManagement.js`: Added temporary password checkbox and display modal
- `App.js`: Added password change prompt check on mount
- `ChangePasswordPrompt.js`: New component for password change modal
- `authService.js`: Updated `createUserByAdmin()` function

### Database
- `check_db.py`: Script to add `must_change_password` column (migration helper)

## Production Considerations

1. **Email Integration**: Consider sending temporary passwords via email instead of displaying them
2. **Password Expiry**: Add expiration time for temporary passwords (e.g., 24 hours)
3. **Audit Logging**: Log all password changes for security auditing
4. **Password History**: Prevent reusing recent passwords
5. **Account Lockout**: Implement failed login attempt tracking
6. **Password Strength Meter**: Add visual indicator in password change form
7. **2FA Integration**: Consider two-factor authentication for admin accounts

## API Reference Summary

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/api/auth/admin/users` | POST | Create user | Yes (Admin) |
| `/api/auth/login` | POST | User login | No |
| `/api/auth/change-password` | POST | Change password | Yes |
| `/api/auth/me` | GET | Get current user | Yes |

## Success Criteria

✅ Admin can create users with auto-generated temporary passwords  
✅ Temporary passwords are displayed once with copy functionality  
✅ Users must change password on first login  
✅ Password change modal blocks all application access  
✅ New passwords meet security requirements  
✅ After password change, users have normal access  
✅ Subsequent logins use new password without prompt  
✅ Admin can still manually set passwords if needed  

## Next Steps

- Test the complete workflow as described above
- Verify database schema includes `must_change_password` column
- Ensure frontend and backend are running on correct ports
- Check browser console for any JavaScript errors
- Verify API endpoints return correct data structure
