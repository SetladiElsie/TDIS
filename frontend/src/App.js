import React, { useState, useEffect } from 'react';
import Upload from './components/Upload';
import Results from './components/Results';
import { healthCheck } from './services/api';
import { toast } from 'react-toastify';
import './styles/App.css';
import './styles/index.css';

function App() {
  const [extractedData, setExtractedData] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [apiReady, setApiReady] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAPI();
  }, []);

  async function checkAPI() {
    try {
      const health = await healthCheck();
      setApiReady(true);
      setLoading(false);
    } catch (error) {
      setApiReady(false);
      setLoading(false);
      toast.error('❌ API is not running. Please start the backend server at http://localhost:5000');
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
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="container">
          <div className="header-content flex-between">
            <div>
              <h1 className="app-title">
                📄 Tender Document Extraction
              </h1>
              <p className="app-subtitle">
                Automatically extract key information from tender documents
              </p>
            </div>
            <div className="header-status">
              {apiReady ? (
                <div className="status-badge status-success">
                  <span className="status-dot"></span>
                  API Connected
                </div>
              ) : (
                <div className="status-badge status-error">
                  <span className="status-dot"></span>
                  API Offline
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="app-main">
        <div className="container">
          {/* API Error Message */}
          {!apiReady && (
            <div className="alert alert-danger mb-4">
              ⚠️ The API server is not available. Please ensure the backend is running:
              <br />
              <code>python app.py</code>
            </div>
          )}

          {/* Upload Section */}
          <section className="section">
            <Upload
              onExtractionStart={handleExtractionStart}
              onExtractComplete={handleExtractComplete}
            />
          </section>

          {/* Results Section */}
          {apiReady && (
            <section className="section">
              <Results data={extractedData} refreshTrigger={refreshTrigger} />
            </section>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-section">
              <h4>About</h4>
              <p>Tender Document Extraction Application v1.0.0</p>
            </div>
            <div className="footer-section">
              <h4>Supported Formats</h4>
              <p>PDF, DOCX, TXT, CSV, XLSX</p>
            </div>
            <div className="footer-section">
              <h4>Support</h4>
              <p>For issues, check the documentation or contact the development team</p>
            </div>
          </div>
          <div className="footer-divider"></div>
          <div className="footer-bottom">
            <p>&copy; 2026 Tender Document Extraction. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
