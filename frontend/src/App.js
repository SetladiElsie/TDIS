import React, { useState, useEffect } from 'react';
import Upload from './components/Upload';
import Results from './components/Results';
import ImportPanel from './components/ImportPanel';
import { healthCheck } from './services/api';
import './styles/App.css';
import './styles/index.css';

function App() {
  const [extractedData, setExtractedData] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [apiReady, setApiReady] = useState(false);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState('');
  const [importUrl, setImportUrl] = useState(null);

  useEffect(() => {
    checkAPI();
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const url = params.get('downloadUrl') || params.get('download_url');
    if (url) {
      setImportUrl(url);
    }
  }, []);

  async function checkAPI() {
    try {
      const health = await healthCheck();
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
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="container">
          <div className="header-content flex-between">
            <div>
              <h1 className="app-title">
                TIA-SOLUTIONS Tender Document Reader
              </h1>
            </div>
          </div>
        </div>
      </header>

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

          {/* Upload Section */}
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
              <Upload
                onExtractionStart={handleExtractionStart}
                onExtractComplete={handleExtractComplete}
              />
            </section>
          )}

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
