import React from 'react';
import { Navigate } from 'react-router-dom';
import { isAuthenticated, hasRole } from '../services/authService';

/**
 * Protected Route Component
 * Wraps routes that require authentication
 */
const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const authenticated = isAuthenticated();
  
  if (!authenticated) {
    // Redirect to login if not authenticated
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && !hasRole('admin')) {
    // Redirect to home if admin required but user is not admin
    return <Navigate to="/" replace />;
  }

  return children;
};

export default ProtectedRoute;
