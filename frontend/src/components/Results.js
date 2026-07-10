import React, { useState, useEffect } from 'react';
import { listResults, deleteResult, exportResults } from '../services/api';
import { formatDate, formatCurrency, truncateText, getStatusColor, parseExtractionData } from '../utils/helpers';
import { toast } from 'react-toastify';
import '../styles/Results.css';

const Results = ({ data, refreshTrigger }) => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedResult, setSelectedResult] = useState(data || null);
  const [page, setPage] = useState(1);
  const [totalResults, setTotalResults] = useState(0);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const itemsPerPage = 10;

  useEffect(() => {
    loadResults();
  }, [page, search, statusFilter, refreshTrigger]);

  async function loadResults() {
    setLoading(true);
    try {
      const params = {
        page,
        limit: itemsPerPage,
        search: search || undefined,
        status: statusFilter || undefined,
      };

      const response = await listResults(params);
      setResults(response.results || []);
      setTotalResults(response.total || 0);
    } catch (error) {
      toast.error('Failed to load results: ' + error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(extractionId) {
    if (window.confirm('Are you sure you want to delete this result?')) {
      try {
        await deleteResult(extractionId);
        toast.success('Result deleted successfully');
        setSelectedResult(null);
        loadResults();
      } catch (error) {
        toast.error('Failed to delete result: ' + error.message);
      }
    }
  }

  async function handleExport(extractionId, format) {
    try {
      await exportResults(extractionId, format);
      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Export failed: ' + error.message);
    }
  }

  const totalPages = Math.ceil(totalResults / itemsPerPage);
  const parsedData = selectedResult ? parseExtractionData(selectedResult.extracted_data) : null;

  return (
    <div className="results-container">
      <div className="results-section">
        <h2 className="section-title">📋 Extraction Results</h2>

        {/* Search and Filter */}
        <div className="search-filter-bar">
          <div className="search-input">
            <input
              type="text"
              placeholder="Search tender name or ID..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="form-control"
            />
          </div>

          <div className="filter-select">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="form-control"
            >
              <option value="">All Status</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>

        {/* Results List */}
        {loading ? (
          <div className="flex-center p-4">
            <div className="spinner"></div>
            <span>Loading results...</span>
          </div>
        ) : results.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <p>No results found</p>
            <small>Upload and extract a tender document to see results here</small>
          </div>
        ) : (
          <>
            <div className="results-list">
              {results.map((result) => (
                <div
                  key={result.extraction_id}
                  className={`result-item ${selectedResult?.extraction_id === result.extraction_id ? 'active' : ''}`}
                  onClick={() => setSelectedResult(result)}
                >
                  <div className="result-header">
                    <h3 className="result-title truncate">{result.tender_name}</h3>
                    <span className={`badge badge-${getStatusColor(result.status)}`}>
                      {result.status}
                    </span>
                  </div>
                  <div className="result-meta">
                    <div className="meta-item">
                      <span className="meta-label">ID:</span>
                      <span className="meta-value">{result.extraction_id.slice(0, 8)}...</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">Closing:</span>
                      <span className="meta-value">{result.closing_date || 'N/A'}</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">Created:</span>
                      <span className="meta-value">{formatDate(result.created_at)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="pagination">
                <button
                  className="btn btn-sm btn-outline"
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                >
                  ← Previous
                </button>
                <span className="page-info">
                  Page {page} of {totalPages}
                </span>
                <button
                  className="btn btn-sm btn-outline"
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                >
                  Next →
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Details View */}
      {selectedResult && parsedData && (
        <div className="details-section">
          <div className="card">
            <div className="card-header flex-between">
              <h2>📊 Tender Details</h2>
              <div className="detail-actions">
                <button
                  className="btn btn-sm btn-outline"
                  onClick={() => handleExport(selectedResult.extraction_id, 'json')}
                >
                  Download JSON
                </button>
                <button
                  className="btn btn-sm btn-outline"
                  onClick={() => handleExport(selectedResult.extraction_id, 'csv')}
                >
                  Download CSV
                </button>
                <button
                  className="btn btn-sm btn-danger"
                  onClick={() => handleDelete(selectedResult.extraction_id)}
                >
                  Delete
                </button>
              </div>
            </div>

            <div className="card-body p-3">
              {/* Basic Information */}
              <div className="detail-section">
                <h3 className="detail-title">Basic Information</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <span className="detail-label">Tender ID</span>
                    <span className="detail-value">{parsedData.tender_id}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Tender Name</span>
                    <span className="detail-value">{parsedData.tender_name}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Organization</span>
                    <span className="detail-value">{parsedData.organization}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Document Type</span>
                    <span className="detail-value">{parsedData.document_type}</span>
                  </div>
                </div>
              </div>

              {/* Key Dates & Budget */}
              <div className="detail-section">
                <h3 className="detail-title">Key Information</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <span className="detail-label">Closing Date</span>
                    <span className="detail-value text-danger">
                      {parsedData.closing_date_formatted}
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Budget</span>
                    <span className="detail-value">
                      {formatCurrency(parsedData.budget.amount, parsedData.budget.currency)}
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Location</span>
                    <span className="detail-value">{parsedData.location}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Duration</span>
                    <span className="detail-value">{parsedData.estimated_duration}</span>
                  </div>
                </div>
              </div>

              {/* Scope of Work */}
              <div className="detail-section">
                <h3 className="detail-title">Scope of Work</h3>
                <p className="detail-text">{parsedData.scope_of_work}</p>
              </div>

              {/* Contact Information */}
              <div className="detail-section">
                <h3 className="detail-title">Contact Information</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <span className="detail-label">Email</span>
                    <span className="detail-value">
                      <a href={`mailto:${parsedData.contact_email}`}>
                        {parsedData.contact_email}
                      </a>
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Phone</span>
                    <span className="detail-value">
                      <a href={`tel:${parsedData.contact_phone}`}>
                        {parsedData.contact_phone}
                      </a>
                    </span>
                  </div>
                </div>
              </div>

              {/* Submission Details */}
              <div className="detail-section">
                <h3 className="detail-title">Submission Details</h3>
                <div className="detail-item">
                  <span className="detail-label">Submission Format</span>
                  <span className="detail-value">{parsedData.submission_format}</span>
                </div>
              </div>

              {/* Evaluation Criteria */}
              {parsedData.evaluation_criteria.length > 0 && (
                <div className="detail-section">
                  <h3 className="detail-title">Evaluation Criteria</h3>
                  <ul className="detail-list">
                    {parsedData.evaluation_criteria.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Deliverables */}
              {parsedData.deliverables.length > 0 && (
                <div className="detail-section">
                  <h3 className="detail-title">Deliverables</h3>
                  <ul className="detail-list">
                    {parsedData.deliverables.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Compulsory Documents */}
              {parsedData.compulsory_documents.length > 0 && (
                <div className="detail-section">
                  <h3 className="detail-title">Compulsory Documents Required</h3>
                  <ul className="detail-list">
                    {parsedData.compulsory_documents.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Key Requirements */}
              {parsedData.key_requirements.length > 0 && (
                <div className="detail-section">
                  <h3 className="detail-title">Key Requirements</h3>
                  <ul className="detail-list">
                    {parsedData.key_requirements.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Results;
