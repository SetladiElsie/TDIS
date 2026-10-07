import React, { useState, useEffect } from 'react';
import { getCurrentUser, updateProfile, changePassword } from '../services/authService';
import '../styles/Auth.css';

const Profile = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [profileForm, setProfileForm] = useState({
    name: '',
    email: '',
  });
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [message, setMessage] = useState({ type: '', text: '' });
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const userData = await getCurrentUser();
      setUser(userData);
      setProfileForm({
        name: userData.name || '',
        email: userData.email || '',
      });
      setLoading(false);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load profile' });
      setLoading(false);
    }
  };

  const handleProfileChange = (e) => {
    setProfileForm({
      ...profileForm,
      [e.target.name]: e.target.value,
    });
  };

  const handlePasswordChange = (e) => {
    setPasswordForm({
      ...passwordForm,
      [e.target.name]: e.target.value,
    });
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setUpdating(true);
    setMessage({ type: '', text: '' });

    try {
      await updateProfile(profileForm);
      setMessage({ type: 'success', text: 'Profile updated successfully' });
      await loadUser(); // Reload user data
    } catch (error) {
      setMessage({ type: 'error', text: error.message || 'Failed to update profile' });
    } finally {
      setUpdating(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setUpdating(true);
    setMessage({ type: '', text: '' });

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setMessage({ type: 'error', text: 'New passwords do not match' });
      setUpdating(false);
      return;
    }

    if (passwordForm.newPassword.length < 8) {
      setMessage({ type: 'error', text: 'Password must be at least 8 characters' });
      setUpdating(false);
      return;
    }

    try {
      await changePassword(passwordForm.currentPassword, passwordForm.newPassword);
      setMessage({ type: 'success', text: 'Password changed successfully' });
      setPasswordForm({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });
    } catch (error) {
      setMessage({ type: 'error', text: error.message || 'Failed to change password' });
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card" style={{ maxWidth: '600px' }}>
        <h2 className="auth-title">Profile Settings</h2>

        {message.text && (
          <div className={`alert alert-${message.type}`}>
            {message.text}
          </div>
        )}

        {/* Profile Information */}
        <div className="profile-section">
          <h3 className="section-title">Profile Information</h3>
          <form onSubmit={handleProfileSubmit}>
            <div className="form-group">
              <label htmlFor="name">Name</label>
              <input
                type="text"
                id="name"
                name="name"
                className="form-input"
                value={profileForm.name}
                onChange={handleProfileChange}
                placeholder="Your name"
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                className="form-input"
                value={profileForm.email}
                onChange={handleProfileChange}
                required
                disabled
                title="Email cannot be changed"
              />
              <small className="form-hint">Email cannot be changed</small>
            </div>

            <div className="form-group">
              <label>Role</label>
              <div className="role-badge">
                {user?.is_admin ? 'Administrator' : 'User'}
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-full"
              disabled={updating}
            >
              {updating ? 'Updating...' : 'Update Profile'}
            </button>
          </form>
        </div>

        {/* Change Password */}
        <div className="profile-section" style={{ marginTop: '2rem' }}>
          <h3 className="section-title">Change Password</h3>
          <form onSubmit={handlePasswordSubmit}>
            <div className="form-group">
              <label htmlFor="currentPassword">Current Password</label>
              <input
                type="password"
                id="currentPassword"
                name="currentPassword"
                className="form-input"
                value={passwordForm.currentPassword}
                onChange={handlePasswordChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="newPassword">New Password</label>
              <input
                type="password"
                id="newPassword"
                name="newPassword"
                className="form-input"
                value={passwordForm.newPassword}
                onChange={handlePasswordChange}
                required
                minLength={8}
              />
              <small className="form-hint">
                At least 8 characters with uppercase, lowercase, number, and special character
              </small>
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm New Password</label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                className="form-input"
                value={passwordForm.confirmPassword}
                onChange={handlePasswordChange}
                required
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-full"
              disabled={updating}
            >
              {updating ? 'Changing...' : 'Change Password'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Profile;
