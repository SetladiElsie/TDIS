import React, { useState, useEffect, useCallback } from 'react';
import { listResults, getResults, updateResult, getUsers, uploadSupportingDocuments, deleteSupportingDocument, deleteResult } from '../services/api';
import { parseExtractionData, formatSouthAfricanPhone } from '../utils/helpers';
import '../styles/Results.css';

const Results = ({ data, refreshTrigger, onResultsCountChange }) => {
  const [results, setResults] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [expandedData, setExpandedData] = useState({});
  const [loadingId, setLoadingId] = useState(null);
  const [loadError, setLoadError] = useState('');
  const [statusUpdateError, setStatusUpdateError] = useState('');
  const [userUpdateError, setUserUpdateError] = useState('');
  const [page, setPage] = useState(1);
  const [totalResults, setTotalResults] = useState(0);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [userFilter, setUserFilter] = useState('');
  const [contextMenu, setContextMenu] = useState({ visible: false, x: 0, y: 0, extractionId: null, status: null });

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
        assigned_user_id: userFilter || undefined,
      };
      const response = await listResults(params);
      const nextResults = response.results || [];
      const nextTotal = response.total || 0;

      setResults(nextResults);
      setTotalResults(nextTotal);
      if (onResultsCountChange) {
        onResultsCountChange(nextTotal);
      }
    } catch (error) {
      setLoadError('Failed to load results: ' + error.message);
    } finally {
      setLoading(false);
    }
  }, [page, search, statusFilter, userFilter, onResultsCountChange]);

  const loadUsers = useCallback(async () => {
    try {
      const availableUsers = await getUsers();
      setUsers(availableUsers || []);
    } catch (error) {
      setUsers([]);
    }
  }, []);

  useEffect(() => {
    loadResults();
    loadUsers();
  }, [loadResults, loadUsers, refreshTrigger]);

  useEffect(() => {
    const handleGlobalClick = () => setContextMenu({ visible: false, x: 0, y: 0, extractionId: null, status: null });

    window.addEventListener('click', handleGlobalClick);
    return () => {
      window.removeEventListener('click', handleGlobalClick);
    };
  }, []);

  const openContextMenu = (event, extractionId, status) => {
    event.preventDefault();
    event.stopPropagation();
    setContextMenu({
      visible: true,
      x: event.clientX,
      y: event.clientY,
      extractionId,
      status,
    });
  };

  const handleRestoreTender = async (extractionId) => {
    try {
      const updated = await updateResult(extractionId, { status: 'processing' });
      setResults((prev) => prev.filter((item) => item.extraction_id !== extractionId));
      setExpandedData((prev) => ({
        ...prev,
        [extractionId]: { ...(prev[extractionId] || {}), status: updated.status },
      }));
      setContextMenu({ visible: false, x: 0, y: 0, extractionId: null, status: null });
    } catch (err) {
      setStatusUpdateError(err.message || 'Could not restore tender.');
    }
  };

  const handleArchiveTender = async (extractionId) => {
    try {
      const updated = await updateResult(extractionId, { status: 'archived' });
      setResults((prev) => prev.filter((item) => item.extraction_id !== extractionId));
      setExpandedData((prev) => ({
        ...prev,
        [extractionId]: { ...(prev[extractionId] || {}), status: updated.status },
      }));
      setContextMenu({ visible: false, x: 0, y: 0, extractionId: null, status: null });
    } catch (err) {
      setStatusUpdateError(err.message || 'Could not archive tender.');
    }
  };

  const handleDeleteTender = async (extractionId) => {
    try {
      await deleteResult(extractionId);
      setResults((prev) => prev.filter((item) => item.extraction_id !== extractionId));
      setExpandedData((prev) => {
        const next = { ...prev };
        delete next[extractionId];
        return next;
      });
      setContextMenu({ visible: false, x: 0, y: 0, extractionId: null, status: null });
    } catch (err) {
      setStatusUpdateError(err.message || 'Could not delete tender.');
    }
  };

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

  const handleSupportingDocumentUpload = async (event, extractionId) => {
    const files = Array.from(event.target.files || []);
    if (!files.length) return;

    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    try {
      const response = await uploadSupportingDocuments(extractionId, formData);
      const savedDocs = response.supporting_documents || [];

      setExpandedData((prev) => ({
        ...prev,
        [extractionId]: { ...(prev[extractionId] || {}), supporting_documents: savedDocs },
      }));
    } catch (error) {
      setStatusUpdateError(error.message || 'Could not upload supporting documents.');
    } finally {
      event.target.value = '';
    }
  };

  const handleDeleteSupportingDocument = async (extractionId, documentId) => {
    try {
      const response = await deleteSupportingDocument(extractionId, documentId);
      const savedDocs = response.supporting_documents || [];

      setExpandedData((prev) => ({
        ...prev,
        [extractionId]: { ...(prev[extractionId] || {}), supporting_documents: savedDocs },
      }));
    } catch (error) {
      setStatusUpdateError(error.message || 'Could not delete supporting document.');
    }
  };

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
            <option value="archived">Archived</option>
            <option value="deleted">Deleted</option>
          </select>
        </div>
        <div className="filter-select">
          <select
            value={userFilter}
            onChange={(e) => { setUserFilter(e.target.value); setPage(1); }}
            className="form-control"
          >
            <option value="">All Users</option>
            <option value="unassigned">Unassigned</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>{user.name}</option>
            ))}
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
          {contextMenu.visible && (
            <div
              className="result-context-menu"
              style={{ left: contextMenu.x, top: contextMenu.y }}
              onClick={(event) => event.stopPropagation()}
            >
              {contextMenu.status === 'archived' || contextMenu.status === 'deleted' ? (
                <button type="button" className="context-menu-item" onClick={() => handleRestoreTender(contextMenu.extractionId)}>
                  Restore
                </button>
              ) : (
                <>
                  <button type="button" className="context-menu-item" onClick={() => handleArchiveTender(contextMenu.extractionId)}>
                    Archive
                  </button>
                  <button type="button" className="context-menu-item" onClick={() => handleDeleteTender(contextMenu.extractionId)}>
                    Delete
                  </button>
                </>
              )}
            </div>
          )}

          <div className="results-list">
            {results.map((result) => {
              const isOpen = expandedId === result.extraction_id;
              const isLoadingThis = loadingId === result.extraction_id;
              const full = expandedData[result.extraction_id];
              const parsedData = full ? parseExtractionData(full.extracted_data) : null;

              const tenderDocumentUrl = result.upload_id
                ? `${(process.env.REACT_APP_API_URL || 'http://localhost:5000/api').replace(/\/+$/, '')}/uploads/${result.upload_id}/file`
                : '';

              return (
                <div
                  key={result.extraction_id}
                  className={`result-item ${isOpen ? 'active' : ''}`}
                >
                  {/* Clickable row header */}
                  <div
                    className="result-row"
                    onClick={() => toggleExpand(result.extraction_id)}
                    onContextMenu={(event) => openContextMenu(event, result.extraction_id, result.status)}
                  >
                    <div className="result-header">
                      <div className="result-title-group">
                        <h3 className="result-title">{result.tender_name}</h3>
                        <div className="result-meta">
                          <div className="meta-item">
                            <span className="meta-label">Assigned</span>
                            <span className="meta-value">{result.assigned_user_name || 'Unassigned'}</span>
                          </div>
                          {result.upload_id && (
                            <div className="meta-item">
                              <span className="meta-label">Tender Document</span>
                              <a
                                className="result-original-document"
                                href={tenderDocumentUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(event) => event.stopPropagation()}
                              >
                                📄 {result.filename || 'Original Tender'}
                              </a>
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="result-header-right">
                        <div className="result-status-stack">
                          <div className={`form-control result-status status-${result.status}`}>
                            {result.status}
                          </div>
                          <div className="result-total-bid-price">
                            {result.total_bid_price ? `Bid: ${result.total_bid_price}` : 'Bid: —'}
                          </div>
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
                              <div className="detail-item">
                                <span className="detail-label">Closing Date</span>
                                <span className="detail-value">{parsedData.closing_date_formatted || parsedData.closing_date || '—'}</span>
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
                                <select
                                  className="form-control"
                                  value={full.assigned_user_id || full.assigned_user?.id || ''}
                                  onChange={async (e) => {
                                    const nextUserId = e.target.value;
                                    setUserUpdateError('');
                                    setStatusUpdateError('');
                                    if (!nextUserId) {
                                      setUserUpdateError('Please select a user before assigning this tender.');
                                      return;
                                    }

                                    try {
                                      const updated = await updateResult(full.extraction_id, {
                                        assigned_user_id: nextUserId,
                                      });
                                      setExpandedData((prev) => ({
                                        ...prev,
                                        [full.extraction_id]: updated,
                                      }));
                                      setResults((prev) => prev.map((item) => item.extraction_id === full.extraction_id ? {
                                        ...item,
                                        assigned_user_id: updated.assigned_user_id,
                                        assigned_user_name: updated.assigned_user_name || updated.assigned_user?.name,
                                      } : item));
                                    } catch (err) {
                                      setUserUpdateError(err.message || 'Could not assign user.');
                                    }
                                  }}
                                >
                                  <option value="">Unassigned</option>
                                  {users.map((user) => (
                                    <option key={user.id} value={user.id}>
                                      {user.name}
                                    </option>
                                  ))}
                                </select>
                              </div>
                              <div className="detail-item">
                                <span className="detail-label">Current Status</span>
                                <span className="detail-value">{full.status}</span>
                              </div>
                            </div>
                            {userUpdateError && (
                              <div className="alert alert-danger mt-2">
                                {userUpdateError}
                              </div>
                            )}
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
                                    try {
                                      if (nextStatus === 'deleted') {
                                        await deleteResult(full.extraction_id);
                                        setResults((prev) => prev.filter((item) => item.extraction_id !== full.extraction_id));
                                        setExpandedData((prev) => {
                                          const next = { ...prev };
                                          delete next[full.extraction_id];
                                          return next;
                                        });
                                        setExpandedId(null);
                                        return;
                                      }

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
                                >
                                  <option value="processing">processing</option>
                                  <option value="completed">completed</option>
                                  <option value="failed">failed</option>
                                  <option value="archived">archived</option>
                                  <option value="deleted">deleted</option>
                                </select>
                              </div>
                            </div>
                            <div className="detail-grid mt-3">
                              <div className="detail-item">
                                <label className="detail-label" htmlFor={`total-bid-price-${full.extraction_id}`}>
                                  Total Bid Price
                                </label>
                                <input
                                  id={`total-bid-price-${full.extraction_id}`}
                                  className="form-control"
                                  value={full.total_bid_price || ''}
                                  placeholder="e.g. R 125000.00"
                                  onChange={async (e) => {
                                    const nextValue = e.target.value;
                                    setExpandedData((prev) => ({
                                      ...prev,
                                      [full.extraction_id]: { ...prev[full.extraction_id], total_bid_price: nextValue },
                                    }));
                                    try {
                                      const updated = await updateResult(full.extraction_id, {
                                        total_bid_price: nextValue,
                                      });
                                      setExpandedData((prev) => ({
                                        ...prev,
                                        [full.extraction_id]: updated,
                                      }));
                                      setResults((prev) => prev.map((item) => item.extraction_id === full.extraction_id ? {
                                        ...item,
                                        total_bid_price: updated.total_bid_price || '',
                                      } : item));
                                    } catch (err) {
                                      setStatusUpdateError(err.message || 'Could not update total bid price.');
                                    }
                                  }}
                                />
                              </div>
                            </div>
                            <div className="detail-item mt-3">
                              <label className="detail-label" htmlFor={`comment-${full.extraction_id}`}>
                                Comment
                              </label>
                              <textarea
                                id={`comment-${full.extraction_id}`}
                                className="form-control"
                                rows={3}
                                value={full.comment || ''}
                                placeholder="Add a comment about this tender..."
                                onChange={async (e) => {
                                  const nextComment = e.target.value;
                                  setExpandedData((prev) => ({
                                    ...prev,
                                    [full.extraction_id]: { ...prev[full.extraction_id], comment: nextComment },
                                  }));
                                  try {
                                    const updated = await updateResult(full.extraction_id, {
                                      comment: nextComment,
                                    });
                                    setExpandedData((prev) => ({
                                      ...prev,
                                      [full.extraction_id]: updated,
                                    }));
                                    setResults((prev) => prev.map((item) => item.extraction_id === full.extraction_id ? {
                                      ...item,
                                      comment: updated.comment || '',
                                    } : item));
                                  } catch (err) {
                                    setStatusUpdateError(err.message || 'Could not update comment.');
                                  }
                                }}
                              />
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

                          <div className="detail-section">
                            <h3 className="detail-title">Supporting Documents</h3>
                            <div className="detail-item">
                              <label className="detail-label" htmlFor={`supporting-documents-${full.extraction_id}`}>
                                Upload supporting documents
                              </label>
                              <input
                                id={`supporting-documents-${full.extraction_id}`}
                                className="form-control"
                                type="file"
                                accept=".pdf,.doc,.docx,.txt,.csv,.xlsx,.xls"
                                multiple
                                onChange={(event) => handleSupportingDocumentUpload(event, full.extraction_id)}
                              />
                              {(full.supporting_documents || []).length > 0 ? (
                                <ul className="detail-list mt-2">
                                  {(full.supporting_documents || []).map((doc, index) => (
                                    <li key={`${doc.id || index}-${doc.name}`} className="supporting-document-row">
                                      <a
                                        className="supporting-document-link"
                                        href={`${process.env.REACT_APP_API_URL || 'http://localhost:5000/api'}/results/${full.extraction_id}/supporting-documents/${doc.id}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                      >
                                        <span aria-hidden="true" className="supporting-document-icon">⬇</span>
                                        {doc.name}
                                      </a>
                                      <button
                                        type="button"
                                        className="supporting-document-delete"
                                        onClick={(event) => {
                                          event.stopPropagation();
                                          handleDeleteSupportingDocument(full.extraction_id, doc.id);
                                        }}
                                      >
                                        Delete
                                      </button>
                                    </li>
                                  ))}
                                </ul>
                              ) : (
                                <small className="text-muted">No supporting documents uploaded yet.</small>
                              )}
                            </div>
                          </div>
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
