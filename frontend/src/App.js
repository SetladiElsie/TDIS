import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useSearchParams } from 'react-router-dom';
import UploadBatch from './components/UploadBatch';
import Results from './components/Results';
import ImportPanel from './components/ImportPanel';
import Login from './components/Login';
import Register from './components/Register';
import UserManagement from './components/UserManagement';
import Profile from './components/Profile';
import Navigation from './components/Navigation';
import ProtectedRoute from './components/ProtectedRoute';
import ChangePasswordPrompt from './components/ChangePasswordPrompt';
import { healthCheck } from './services/api';
import { isAuthenticated, getCurrentUser } from './services/authService';
import './styles/App.css';
import './styles/index.css';

function HomePage({ onTenderCountChange }) {
  const [extractedData, setExtractedData] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [apiReady, setApiReady] = useState(false);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState('');
  const [importUrl, setImportUrl] = useState(null);
  const [searchParams] = useSearchParams();

  useEffect(() => {
    checkAPI();
  }, []);

  useEffect(() => {
    const url = searchParams.get('downloadUrl') || searchParams.get('download_url');
    if (url) {
      setImportUrl(url);
    }
  }, [searchParams]);

  async function checkAPI() {
    try {
      await healthCheck();
      setApiReady(true);
      setLoading(false);
    } catch (error) {
      setApiReady(false);
      setApiError('❌ API is not running. Please start the backend server at http://localhost:5000');
      setLoading(false);
    }
  }

  function handleExtractionStart() {
    // Can be used to show loading state
  }

  function handleExtractComplete(results) {
    setExtractedData(results);
    // Refresh results list
    setRefreshTrigger((prev) => prev + 1);
  }

  if (loading) {
    return (
      <div className="flex-center" style={{ height: '100vh', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <div className="spinner" style={{ borderWidth: '3px', borderTopColor: 'white', width: '2rem', height: '2rem' }}></div>
      </div>
    );
  }

  return (
    <>
      {/* Main Content */}
      <main className="app-main">
        <div className="container">
          {/* API Error Message */}
          {!apiReady && apiError && (
            <div className="alert alert-danger mb-4">
              {apiError}
              <br />
              <code>python app.py</code>
            </div>
          )}

          {importUrl ? (
            <section className="section">
              <ImportPanel
                downloadUrl={importUrl}
                onExtractionStart={handleExtractionStart}
                onExtractComplete={handleExtractComplete}
              />
            </section>
          ) : (
            <section className="section">
              <UploadBatch
                onExtractionStart={handleExtractionStart}
                onExtractComplete={handleExtractComplete}
              />
            </section>
          )}

          {/* Results Section */}
          {apiReady && (
            <section className="section">
              <Results
                data={extractedData}
                refreshTrigger={refreshTrigger}
                onResultsCountChange={onTenderCountChange}
              />
            </section>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="container">
          <div className="footer-bottom">
            <p>&copy; 2026 Tender Extraction Portal. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </>
  );
}

function AppContent() {
  const [tenderCount, setTenderCount] = useState(0);
  const [mustChangePassword, setMustChangePassword] = useState(false);
  const authenticated = isAuthenticated();

  useEffect(() => {
    if (authenticated) {
      checkPasswordStatus();
    }
  }, [authenticated]);

  const checkPasswordStatus = async () => {
    try {
      const user = await getCurrentUser();
      setMustChangePassword(user.must_change_password || false);
    } catch (error) {
      console.error('Failed to check password status:', error);
    }
  };

  const handlePasswordChanged = () => {
    setMustChangePassword(false);
    window.location.reload(); // Reload to refresh user data
  };

  const handlePasswordCancel = () => {
    // User cancelled password change - just hide the prompt
    // They can logout and come back later
    setMustChangePassword(false);
  };

  return (
    <div className="app">
      {authenticated && <Navigation tenderCount={tenderCount} />}
      
      {/* Show password change prompt if required */}
      {authenticated && mustChangePassword && (
        <ChangePasswordPrompt 
          onPasswordChanged={handlePasswordChanged}
          onCancel={handlePasswordCancel}
        />
      )}
      
      <Routes>
        {/* Public Routes */}
        <Route 
          path="/login" 
          element={
            authenticated ? <Navigate to="/" replace /> : <Login />
          } 
        />
        <Route 
          path="/register" 
          element={
            authenticated ? <Navigate to="/" replace /> : <Register />
          } 
        />

        {/* Protected Routes */}
        <Route 
          path="/" 
          element={
            <ProtectedRoute>
              <HomePage onTenderCountChange={setTenderCount} />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/profile" 
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/users" 
          element={
            <ProtectedRoute requireAdmin={true}>
              <UserManagement />
            </ProtectedRoute>
          } 
        />

        {/* Catch all - redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
