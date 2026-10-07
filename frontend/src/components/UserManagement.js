import React, { useState, useEffect } from 'react';
import {
  listUsers,
  deleteUser,
  activateUser,
  resetUserPassword,
  isAdmin,
  createUserByAdmin,
} from '../services/authService';
import '../styles/UserManagement.css';

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [adminUser, setAdminUser] = useState(false);
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [expandedUserId, setExpandedUserId] = useState(null);
  const [newUser, setNewUser] = useState({
    name: '',
    email: '',
    password: '',
    is_admin: false,
    generate_temp_password: true,
  });
  const [addingUser, setAddingUser] = useState(false);
  const [createdUserPassword, setCreatedUserPassword] = useState(null);
  const [userPasswords, setUserPasswords] = useState({});  // Store temp passwords by user email

  useEffect(() => {
    setAdminUser(isAdmin());
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await listUsers(true); // Always include inactive users
      setUsers(response.users || []);
    } catch (err) {
      setError('Failed to load users: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleDeactivate = async (userId, userName) => {
    if (!window.confirm(`Are you sure you want to deactivate ${userName}?`)) {
      return;
    }

    try {
      await deleteUser(userId, false);
      await loadUsers();
    } catch (err) {
      setError('Failed to deactivate user: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleActivate = async (userId, userName) => {
    try {
      await activateUser(userId);
      await loadUsers();
    } catch (err) {
      setError('Failed to activate user: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleDelete = async (userId, userName) => {
    if (!window.confirm(
      `Are you sure you want to PERMANENTLY delete ${userName}?\n\nThis action cannot be undone!`
    )) {
      return;
    }

    try {
      await deleteUser(userId, true);
      await loadUsers();
    } catch (err) {
      setError('Failed to delete user: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleResetPassword = async (userId, userName, userEmail) => {
    if (!window.confirm(
      `Reset password for ${userName}?\n\nA new temporary password will be generated.`
    )) {
      return;
    }

    try {
      setError('');
      setSuccess('');
      const result = await resetUserPassword(userId);
      
      // Store the new temporary password
      setUserPasswords(prev => ({
        ...prev,
        [userEmail]: result.temporary_password
      }));
      
      // Show password in modal
      setCreatedUserPassword({
        email: userEmail,
        password: result.temporary_password,
        isReset: true
      });
      
      setSuccess(`Password reset for ${userName}. New temporary password generated.`);
      await loadUsers();
    } catch (err) {
      setError('Failed to reset password: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    setAddingUser(true);
    setError('');
    setSuccess('');
    setCreatedUserPassword(null);

    try {
      // Use admin endpoint to create user
      const password = newUser.generate_temp_password ? null : newUser.password;
      const result = await createUserByAdmin(newUser.name, newUser.email, password, newUser.is_admin);
      
      // Check if temporary password was generated
      if (result.temporary_password) {
        // Store password for this user
        setUserPasswords(prev => ({
          ...prev,
          [newUser.email]: result.temporary_password
        }));
        
        setCreatedUserPassword({
          email: newUser.email,
          password: result.temporary_password
        });
        setSuccess(`User ${newUser.name} created successfully with temporary password!`);
      } else {
        setSuccess(`User ${newUser.name} created successfully!`);
      }
      
      setShowAddUserModal(false);
      setNewUser({ name: '', email: '', password: '', is_admin: false, generate_temp_password: true });
      await loadUsers();
    } catch (err) {
      setError('Failed to create user: ' + (err.response?.data?.error || err.message));
    } finally {
      setAddingUser(false);
    }
  };

  const validatePassword = (password) => {
    if (password.length < 8) return false;
    if (!/[A-Z]/.test(password)) return false;
    if (!/[a-z]/.test(password)) return false;
    if (!/[0-9]/.test(password)) return false;
    if (!/[^A-Za-z0-9]/.test(password)) return false;
    return true;
  };

  if (!adminUser) {
    return (
      <div className="user-management-container">
        <div className="alert alert-danger">
          You do not have permission to manage users. Admin access required.
        </div>
      </div>
    );
  }

  return (
    <div className="user-management-container">
      <div className="user-management-header">
        <h2 className="section-title">👥 User Management</h2>
        <div className="header-actions">
          <button
            className="btn btn-primary"
            onClick={() => setShowAddUserModal(true)}
          >
            + Add User
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger mb-3">
          {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success mb-3">
          {success}
        </div>
      )}

      {loading ? (
        <div className="flex-center p-4">
          <div className="spinner"></div>
          <span>Loading users...</span>
        </div>
      ) : users.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">👥</div>
          <p>No users found</p>
        </div>
      ) : (
        <div className="users-table-container">
          <table className="users-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <React.Fragment key={user.id}>
                  <tr 
                    className={`user-row ${!user.is_active ? 'inactive-user' : ''} ${expandedUserId === user.id ? 'expanded' : ''}`}
                    onClick={() => setExpandedUserId(expandedUserId === user.id ? null : user.id)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td>
                      <div className="user-name">
                        {user.name}
                        {user.is_admin && (
                          <span className="badge badge-admin">Admin</span>
                        )}
                        {!user.is_active && (
                          <span className="badge badge-inactive">Inactive</span>
                        )}
                        {user.must_change_password && (
                          <span className="badge badge-warning" title="User has temporary password">
                            🔑 Temp Password
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {user.email}
                        {userPasswords[user.email] && (
                          <button
                            className="btn btn-sm btn-link"
                            onClick={(e) => {
                              e.stopPropagation();
                              setCreatedUserPassword({
                                email: user.email,
                                password: userPasswords[user.email],
                                userName: user.name
                              });
                            }}
                            title="View temporary password"
                            style={{ padding: '0.25rem 0.5rem', fontSize: '0.875rem' }}
                          >
                            🔑 View Password
                          </button>
                        )}
                      </div>
                    </td>
                    <td>
                      {user.created_at
                        ? new Date(user.created_at).toLocaleDateString()
                        : '—'}
                    </td>
                  </tr>
                  {expandedUserId === user.id && (
                    <tr className="action-row">
                      <td colSpan="3">
                        <div className="action-buttons">
                          <button
                            className="btn btn-sm btn-info"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleResetPassword(user.id, user.name, user.email);
                            }}
                            title="Reset password and generate new temporary password"
                          >
                            🔄 Reset Password
                          </button>
                          {user.is_active ? (
                            <button
                              className="btn btn-sm btn-warning"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeactivate(user.id, user.name);
                              }}
                              title="Deactivate user"
                            >
                              Deactivate
                            </button>
                          ) : (
                            <button
                              className="btn btn-sm btn-success"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleActivate(user.id, user.name);
                              }}
                              title="Activate user"
                            >
                              Activate
                            </button>
                          )}
                          <button
                            className="btn btn-sm btn-danger"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(user.id, user.name);
                            }}
                            title="Permanently delete user"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add User Modal */}
      {showAddUserModal && (
        <div className="modal-overlay" onClick={() => setShowAddUserModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add New User</h3>
              <button
                className="modal-close"
                onClick={() => setShowAddUserModal(false)}
              >
                ×
              </button>
            </div>
            <form onSubmit={handleAddUser}>
              <div className="form-group">
                <label htmlFor="name">Name</label>
                <input
                  type="text"
                  id="name"
                  className="form-control"
                  value={newUser.name}
                  onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  type="email"
                  id="email"
                  className="form-control"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={newUser.generate_temp_password}
                    onChange={(e) => setNewUser({ ...newUser, generate_temp_password: e.target.checked })}
                  />
                  <span>Generate temporary password (user must change on first login)</span>
                </label>
              </div>

              {!newUser.generate_temp_password && (
                <div className="form-group">
                  <label htmlFor="password">Password</label>
                  <input
                    type="password"
                    id="password"
                    className="form-control"
                    value={newUser.password}
                    onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                    required={!newUser.generate_temp_password}
                    minLength={8}
                  />
                  <small className="form-text">
                    At least 8 characters with uppercase, lowercase, number, and special character
                  </small>
                  {newUser.password && !validatePassword(newUser.password) && (
                    <small className="form-text text-danger">
                      Password does not meet requirements
                    </small>
                  )}
                </div>
              )}

              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={newUser.is_admin}
                    onChange={(e) => setNewUser({ ...newUser, is_admin: e.target.checked })}
                  />
                  <span>Make this user an administrator</span>
                </label>
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowAddUserModal(false)}
                  disabled={addingUser}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={addingUser || (!newUser.generate_temp_password && !validatePassword(newUser.password))}
                >
                  {addingUser ? 'Creating...' : 'Create User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Temporary Password Modal */}
      {createdUserPassword && (
        <div className="modal-overlay" onClick={() => setCreatedUserPassword(null)}>
          <div className="modal-content temp-password-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>🔑 {createdUserPassword.isReset ? 'Password Reset' : 'Temporary Password'}</h3>
              <button
                className="modal-close"
                onClick={() => setCreatedUserPassword(null)}
              >
                ×
              </button>
            </div>
            <div className="temp-password-content">
              <p className="temp-password-warning">
                <strong>Important:</strong> {createdUserPassword.userName ? `Save this password for ${createdUserPassword.userName}.` : 'Save this password now!'} 
                {!createdUserPassword.isReset && ' You can view it again from the user list.'}
              </p>
              <div className="temp-password-details">
                <div className="detail-row">
                  <label>Email:</label>
                  <div className="detail-value">{createdUserPassword.email}</div>
                </div>
                <div className="detail-row">
                  <label>Temporary Password:</label>
                  <div className="detail-value password-value" style={{ 
                    fontFamily: 'monospace', 
                    fontSize: '1.1rem',
                    fontWeight: 'bold',
                    color: '#764ba2',
                    padding: '0.75rem',
                    background: '#f3f4f6',
                    borderRadius: '4px',
                    border: '2px dashed #667eea'
                  }}>
                    {createdUserPassword.password}
                  </div>
                </div>
              </div>
              <p className="temp-password-note">
                The user will be required to change this password on first login.
              </p>
              <button
                className="btn btn-primary btn-block"
                onClick={() => {
                  navigator.clipboard.writeText(createdUserPassword.password);
                  alert('Password copied to clipboard!');
                }}
              >
                📋 Copy Password to Clipboard
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
