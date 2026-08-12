import React, { useState, useEffect, useCallback } from 'react';
import { listResults, getResults, updateResult } from '../services/api';
import { parseExtractionData, formatSouthAfricanPhone } from '../utils/helpers';
import '../styles/Results.css';

const Results = ({ data, refreshTrigger }) => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [expandedData, setExpandedData] = useState({});
  const [loadingId, setLoadingId] = useState(null);
  const [loadError, setLoadError] = useState('');
  const [statusUpdateError, setStatusUpdateError] = useState('');
  const [page, setPage] = useState(1);
  const [totalResults, setTotalResults] = useState(0);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const itemsPerPage = 10;

  const loadResults = useCallback(async () => {
    setLoading(true);
    setLoadError('');
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
      setLoadError('Failed to load results: ' + error.message);
    } finally {
      setLoading(false);
    }
  }, [page, search, statusFilter]);

  useEffect(() => {
    loadResults();
  }, [loadResults, refreshTrigger]);

  async function toggleExpand(extractionId) {
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
      setLoadError('Could not load extraction details.');
      setExpandedId(null);
    } finally {
      setLoadingId(null);
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
      ) : loadError ? (
        <div className="alert alert-danger mb-4">{loadError}</div>
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
                      <div className="result-title-group">
                        <h3 className="result-title truncate">{result.tender_name}</h3>
                        <div className="result-meta">
                          <div className="meta-item">
                            <span className="meta-label">Assigned</span>
                            <span className="meta-value">{result.assigned_user_name || 'Unassigned'}</span>
                          </div>
                        </div>
                      </div>
                      <div className="result-header-right">
                        <div className={`form-control result-status status-${result.status}`}>
                          {result.status}
                        </div>
                        <span className={`accordion-arrow ${isOpen ? 'open' : ''}`}>▾</span>
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
                                <span className="detail-value">{parsedData.description || '—'}</span>
                              </div>
                              <div className="detail-item">
                                <span className="detail-label">Organisation</span>
                                <span className="detail-value">{parsedData.organization || '—'}</span>
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
                            <div className="detail-text scope-text" style={{ whiteSpace: 'pre-wrap' }}>
                              {parsedData.scope_of_work || 'Not found'}
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
                                          <a href={`tel:${formatSouthAfricanPhone(person.phone)}`}>
                                            {formatSouthAfricanPhone(person.phone)}
                                          </a>
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
                                    <a href={`tel:${formatSouthAfricanPhone(parsedData.contact_phone)}`}>
                                      {formatSouthAfricanPhone(parsedData.contact_phone)}
                                    </a>
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

                          <div className="detail-section">
                            <h3 className="detail-title">Assignment</h3>
                            <div className="detail-grid">
                              <div className="detail-item">
                                <span className="detail-label">Assigned User</span>
                                <span className="detail-value">{full.assigned_user?.name || 'Unassigned'}</span>
                              </div>
                              <div className="detail-item">
                                <span className="detail-label">Current Status</span>
                                <span className="detail-value">{full.status}</span>
                              </div>
                            </div>
                          </div>

                          <div className="detail-section">
                            <h3 className="detail-title">Update Status</h3>
                            <div className="detail-grid">
                              <div className="detail-item">
                                <select
                                  className="form-control"
                                  value={full.status}
                                  onChange={async (e) => {
                                    setStatusUpdateError('');
                                    const nextStatus = e.target.value;
                                    if (!full.assigned_user?.id) {
                                      setStatusUpdateError('Status can only be updated once a user is assigned.');
                                      return;
                                    }
                                    try {
                                      const updated = await updateResult(full.extraction_id, {
                                        status: nextStatus,
                                      });
                                      setExpandedData((prev) => ({
                                        ...prev,
                                        [full.extraction_id]: updated,
                                      }));
                                      setResults((prev) => prev.map((item) => item.extraction_id === full.extraction_id ? {
                                        ...item,
                                        status: updated.status,
                                      } : item));
                                    } catch (err) {
                                      setStatusUpdateError(err.message || 'Could not update status.');
                                    }
                                  }}
                                  disabled={!full.assigned_user?.id}
                                >
                                  <option value="processing">processing</option>
                                  <option value="completed">completed</option>
                                  <option value="failed">failed</option>
                                </select>
                              </div>
                            </div>
                            {statusUpdateError && (
                              <div className="alert alert-danger mt-2">
                                {statusUpdateError}
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

                          {/* Minimum Requirements */}
                          {parsedData.minimum_requirements.length > 0 && (
                            <div className="detail-section">
                              <h3 className="detail-title">Minimum Requirements</h3>
                              <ul className="detail-list">
                                {parsedData.minimum_requirements.map((item, idx) => (
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
