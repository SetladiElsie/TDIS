import React, { useState, useEffect, useCallback } from 'react';
import { listResults, deleteResult, exportResults, getResults } from '../services/api';
import { formatDate, getStatusColor, parseExtractionData } from '../utils/helpers';
import { toast } from 'react-toastify';
import '../styles/Results.css';

const Results = ({ data, refreshTrigger }) => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [expandedData, setExpandedData] = useState({});
  const [loadingId, setLoadingId] = useState(null);
  const [page, setPage] = useState(1);
  const [totalResults, setTotalResults] = useState(0);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const itemsPerPage = 10;

  const loadResults = useCallback(async () => {
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
  }, [page, search, statusFilter]);

  useEffect(() => {
    loadResults();
  }, [loadResults, refreshTrigger]);
    // Collapse if already open
    if (expandedId === extractionId) {
      setExpandedId(null);
      return;
    }

    setExpandedId(extractionId);

    // Use cached data if already fetched
    if (expandedData[extractionId]) return;

    setLoadingId(extractionId);
    try {
      const full = await getResults(extractionId);
      setExpandedData((prev) => ({ ...prev, [extractionId]: full }));
    } catch (error) {
      toast.error('Could not load extraction details.');
      setExpandedId(null);
    } finally {
      setLoadingId(null);
    }
  }

  async function handleDelete(extractionId, e) {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this result?')) {
      try {
        await deleteResult(extractionId);
        toast.success('Result deleted successfully');
        setExpandedId(null);
        setExpandedData((prev) => {
          const copy = { ...prev };
          delete copy[extractionId];
          return copy;
        });
        loadResults();
      } catch (error) {
        toast.error('Failed to delete result: ' + error.message);
      }
    }
  }

  async function handleExport(extractionId, format, e) {
    e.stopPropagation();
    try {
      await exportResults(extractionId, format);
      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Export failed: ' + error.message);
    }
  }

  const totalPages = Math.ceil(totalResults / itemsPerPage);

  return (
    <div className="results-container">
      <h2 className="section-title">📋 Extraction Results</h2>

      {/* Search and Filter */}
      <div className="search-filter-bar">
        <div className="search-input">
          <input
            type="text"
            placeholder="Search tender name or ID..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="form-control"
          />
        </div>
        <div className="filter-select">
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
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
            {results.map((result) => {
              const isOpen = expandedId === result.extraction_id;
              const isLoadingThis = loadingId === result.extraction_id;
              const full = expandedData[result.extraction_id];
              const parsedData = full ? parseExtractionData(full.extracted_data) : null;

              return (
                <div
                  key={result.extraction_id}
                  className={`result-item ${isOpen ? 'active' : ''}`}
                >
                  {/* Clickable row header */}
                  <div
                    className="result-row"
                    onClick={() => toggleExpand(result.extraction_id)}
                  >
                    <div className="result-header">
                      <h3 className="result-title truncate">{result.tender_name}</h3>
                      <div className="result-header-right">
                        <span className={`badge badge-${getStatusColor(result.status)}`}>
                          {result.status}
                        </span>
                        <span className={`accordion-arrow ${isOpen ? 'open' : ''}`}>▾</span>
                      </div>
                    </div>
                    <div className="result-meta">
                      <div className="meta-item">
                        <span className="meta-label">ID:</span>
                        <span className="meta-value">{result.extraction_id.slice(0, 8)}...</span>
                      </div>
                      <div className="meta-item">
                        <span className="meta-label">Closing:</span>
                        <span className="meta-value">{result.closing_date_formatted || result.closing_date || 'N/A'}</span>
                      </div>
                      <div className="meta-item">
                        <span className="meta-label">Created:</span>
                        <span className="meta-value">{formatDate(result.created_at)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Expandable details panel */}
                  {isOpen && (
                    <div className="accordion-panel">
                      {isLoadingThis ? (
                        <div className="flex-center p-3">
                          <div className="spinner"></div>
                          <span style={{ marginLeft: '0.5rem' }}>Loading details...</span>
                        </div>
                      ) : parsedData ? (
                        <>
                          {/* Action buttons */}
                          <div className="accordion-actions">
                            <button
                              className="btn btn-sm btn-outline"
                              onClick={(e) => handleExport(result.extraction_id, 'json', e)}
                            >
                              Download JSON
                            </button>
                            <button
                              className="btn btn-sm btn-outline"
                              onClick={(e) => handleExport(result.extraction_id, 'csv', e)}
                            >
                              Download CSV
                            </button>
                            <button
                              className="btn btn-sm btn-danger"
                              onClick={(e) => handleDelete(result.extraction_id, e)}
                            >
                              Delete
                            </button>
                          </div>

                          {/* Basic Information */}
                          <div className="detail-section">
                            <h3 className="detail-title">Basic Information</h3>
                            <div className="detail-grid">
                              <div className="detail-item">
                                <span className="detail-label">RFQ / Tender No</span>
                                <span className="detail-value">{parsedData.tender_id || '—'}</span>
                              </div>
                              <div className="detail-item">
                                <span className="detail-label">Description</span>
                                <span className="detail-value">{parsedData.tender_name || '—'}</span>
                              </div>
                              <div className="detail-item">
                                <span className="detail-label">Organisation</span>
                                <span className="detail-value">{parsedData.organization || '—'}</span>
                              </div>
                              <div className="detail-item">
                                <span className="detail-label">Closing Date</span>
                                <span className="detail-value text-danger">
                                  {parsedData.closing_date_formatted || '—'}
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* Briefing Session */}
                          {parsedData.briefing_session && (
                            <div className="detail-section">
                              <h3 className="detail-title">Briefing Session</h3>
                              <div className="detail-text">
                                {parsedData.briefing_session}
                              </div>
                            </div>
                          )}

                          {/* Scope of Work */}
                          <div className="detail-section">
                            <h3 className="detail-title">Scope of Work</h3>
                            <div className="detail-text scope-text">
                              {parsedData.scope_of_work
                                ? parsedData.scope_of_work.split('\n').map((line, idx) =>
                                    line.trim() === ''
                                      ? <br key={idx} />
                                      : <p key={idx} style={{ margin: '0 0 0.4rem 0' }}>{line}</p>
                                  )
                                : <span className="text-muted">Not found</span>
                              }
                            </div>
                          </div>

                          {/* Contact Information */}
                          <div className="detail-section">
                            <h3 className="detail-title">Contact Information</h3>
                            {parsedData.contact_persons && parsedData.contact_persons.length > 0 ? (
                              <div className="contact-persons-list">
                                {parsedData.contact_persons.map((person, idx) => (
                                  <div key={idx} className="contact-person-card">
                                    {person.name && (
                                      <div className="detail-item">
                                        <span className="detail-label">Name</span>
                                        <span className="detail-value">{person.name}</span>
                                      </div>
                                    )}
                                    {person.role && (
                                      <div className="detail-item">
                                        <span className="detail-label">Role</span>
                                        <span className="detail-value">{person.role}</span>
                                      </div>
                                    )}
                                    {person.email && (
                                      <div className="detail-item">
                                        <span className="detail-label">Email</span>
                                        <span className="detail-value">
                                          <a href={`mailto:${person.email}`}>{person.email}</a>
                                        </span>
                                      </div>
                                    )}
                                    {person.phone && (
                                      <div className="detail-item">
                                        <span className="detail-label">Phone</span>
                                        <span className="detail-value">
                                          <a href={`tel:${person.phone}`}>{person.phone}</a>
                                        </span>
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="detail-grid">
                                <div className="detail-item">
                                  <span className="detail-label">Email</span>
                                  <span className="detail-value">
                                    <a href={`mailto:${parsedData.contact_email}`}>{parsedData.contact_email}</a>
                                  </span>
                                </div>
                                <div className="detail-item">
                                  <span className="detail-label">Phone</span>
                                  <span className="detail-value">
                                    <a href={`tel:${parsedData.contact_phone}`}>{parsedData.contact_phone}</a>
                                  </span>
                                </div>
                              </div>
                            )}
                          </div>

                          {/* Submission Details */}
                          <div className="detail-section">
                            <h3 className="detail-title">Submission Details</h3>
                            {parsedData.submission_format ? (
                              <div className="detail-text">{parsedData.submission_format}</div>
                            ) : (
                              <span className="text-muted">Not found</span>
                            )}
                            {parsedData.address && (
                              <div className="detail-item" style={{ marginTop: '0.75rem' }}>
                                <span className="detail-label">Delivery / Physical Address</span>
                                <span className="detail-value">{parsedData.address}</span>
                              </div>
                            )}
                          </div>

                          {/* Mandatory Criteria */}
                          {parsedData.mandatory_criteria && parsedData.mandatory_criteria.length > 0 && (
                            <div className="detail-section">
                              <h3 className="detail-title">Mandatory Requirements</h3>
                              <ul className="detail-list">
                                {parsedData.mandatory_criteria.map((item, idx) => (
                                  <li key={idx}>{item}</li>
                                ))}
                              </ul>
                            </div>
                          )}

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
                        </>
                      ) : null}
                    </div>
                  )}
                </div>
              );
            })}
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
              <span className="page-info">Page {page} of {totalPages}</span>
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
  );
};

export default Results;
