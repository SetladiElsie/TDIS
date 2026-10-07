/**
 * Authentication Service
 * Handles user authentication, registration, and token management
 */

import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
const AUTH_URL = `${API_URL}/auth`;

// Token storage key
const TOKEN_KEY = 'tdis_auth_token';
const USER_KEY = 'tdis_user';

/**
 * Get stored authentication token
 */
export const getToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Get stored user information
 */
export const getUser = () => {
  const userStr = localStorage.getItem(USER_KEY);
  if (userStr) {
    try {
      return JSON.parse(userStr);
    } catch (e) {
      return null;
    }
  }
  return null;
};

/**
 * Store authentication token and user info
 */
export const setAuth = (token, user) => {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};

/**
 * Clear authentication data
 */
export const clearAuth = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = () => {
  const token = getToken();
  return !!token;
};

/**
 * Check if user is admin
 */
export const isAdmin = () => {
  const user = getUser();
  return user && user.is_admin;
};

/**
 * Check if user has a specific role
 * @param {string} role - Role to check ('admin' or 'user')
 */
export const hasRole = (role) => {
  const user = getUser();
  if (!user) return false;
  
  if (role === 'admin') {
    return user.is_admin === true;
  }
  
  // All authenticated users have 'user' role
  if (role === 'user') {
    return true;
  }
  
  return false;
};

/**
 * Get authorization header for API requests
 */
export const getAuthHeader = () => {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

/**
 * Register a new user
 */
export const register = async (name, email, password) => {
  const response = await axios.post(`${AUTH_URL}/register`, {
    name,
    email,
    password,
  });
  
  if (response.data.token && response.data.user) {
    setAuth(response.data.token, response.data.user);
  }
  
  return response.data;
};

/**
 * Login user
 */
export const login = async (email, password) => {
  const response = await axios.post(`${AUTH_URL}/login`, {
    email,
    password,
  });
  
  if (response.data.token && response.data.user) {
    setAuth(response.data.token, response.data.user);
  }
  
  return response.data;
};

/**
 * Logout user
 */
export const logout = () => {
  clearAuth();
  window.location.href = '/login';
};

/**
 * Get current user profile
 */
export const getCurrentUser = async () => {
  const response = await axios.get(`${AUTH_URL}/me`, {
    headers: getAuthHeader(),
  });
  
  // Update stored user data
  if (response.data.user) {
    localStorage.setItem(USER_KEY, JSON.stringify(response.data.user));
  }
  
  return response.data.user;
};

/**
 * Update current user profile
 */
export const updateProfile = async (data) => {
  const response = await axios.put(`${AUTH_URL}/me`, data, {
    headers: getAuthHeader(),
  });
  
  if (response.data.user) {
    localStorage.setItem(USER_KEY, JSON.stringify(response.data.user));
  }
  if (response.data.token) {
    localStorage.setItem(TOKEN_KEY, response.data.token);
  }
  
  return response.data;
};

/**
 * Change password
 */
export const changePassword = async (currentPassword, newPassword) => {
  const payload = {
    new_password: newPassword,
  };
  
  // Only include current password if provided (not required for temp password users)
  if (currentPassword) {
    payload.current_password = currentPassword;
  }
  
  const response = await axios.post(
    `${AUTH_URL}/change-password`,
    payload,
    {
      headers: getAuthHeader(),
    }
  );
  
  return response.data;
};

/**
 * List all users (requires authentication)
 */
export const listUsers = async (includeInactive = false, page = 1, limit = 50) => {
  const response = await axios.get(`${AUTH_URL}/users`, {
    headers: getAuthHeader(),
    params: { include_inactive: includeInactive, page, limit },
  });
  
  return response.data;
};

/**
 * Create new user (admin only)
 */
export const createUserByAdmin = async (name, email, password, isAdmin = false) => {
  const payload = {
    name,
    email,
    is_admin: isAdmin,
  };
  
  // Only include password if provided (otherwise backend generates temp password)
  if (password) {
    payload.password = password;
  }
  
  const response = await axios.post(
    `${AUTH_URL}/users`,
    payload,
    {
      headers: getAuthHeader(),
    }
  );
  
  return response.data;
};

/**
 * Get user by ID
 */
export const getUserById = async (userId) => {
  const response = await axios.get(`${AUTH_URL}/users/${userId}`, {
    headers: getAuthHeader(),
  });
  
  return response.data.user;
};

/**
 * Update user (admin only)
 */
export const updateUser = async (userId, data) => {
  const response = await axios.put(`${AUTH_URL}/users/${userId}`, data, {
    headers: getAuthHeader(),
  });
  
  return response.data;
};

/**
 * Delete user (admin only)
 */
export const deleteUser = async (userId, hard = false) => {
  const response = await axios.delete(`${AUTH_URL}/users/${userId}`, {
    headers: getAuthHeader(),
    params: { hard },
  });
  
  return response.data;
};

/**
 * Activate user (admin only)
 */
export const activateUser = async (userId) => {
  const response = await axios.post(
    `${AUTH_URL}/users/${userId}/activate`,
    {},
    {
      headers: getAuthHeader(),
    }
  );
  
  return response.data;
};

/**
 * Reset user password and generate new temporary password (admin only)
 */
export const resetUserPassword = async (userId) => {
  const response = await axios.post(
    `${AUTH_URL}/users/${userId}/reset-password`,
    {},
    {
      headers: getAuthHeader(),
    }
  );
  
  return response.data;
};

/**
 * Validate token
 */
export const validateToken = async (token) => {
  try {
    const response = await axios.post(`${AUTH_URL}/validate-token`, { token });
    return response.data.valid;
  } catch (error) {
    return false;
  }
};

/**
 * Setup axios interceptor to handle 401 errors
 */
export const setupAuthInterceptor = () => {
  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response && error.response.status === 401) {
        // Token expired or invalid
        clearAuth();
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
      return Promise.reject(error);
    }
  );
};

// Initialize interceptor
setupAuthInterceptor();
