import React, { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadDocument, extractInformation, getResults, getUsers } from '../services/api';
import { formatFileSize, isFileTypeAllowed } from '../utils/helpers';
import '../styles/Upload.css';

const Upload = ({ onExtractionStart, onExtractComplete }) => {
  const [uploading, setUploading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [users, setUsers] = useState([]);
  const [assignedUserId, setAssignedUserId] = useState('');
  const [error, setError] = useState(null);

  const allowedFormats = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'text/plain',
    'text/csv',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  ];

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleDrop,
    maxSize: 50 * 1024 * 1024, // 50MB
    noClick: false,
  });

  useEffect(() => {
    async function loadUsers() {
      try {
        const list = await getUsers();
        setUsers(list || []);
      } catch (err) {
        console.warn('Failed to load users', err);
      }
    }

    loadUsers();
  }, []);

  function handleDrop(acceptedFiles) {
    if (acceptedFiles.length > 0) {
      const droppedFile = acceptedFiles[0];
      if (isFileTypeAllowed(droppedFile, allowedFormats)) {
        setFile(droppedFile);
        setError(null);
      } else {
        setError('File type not supported. Please upload a PDF, DOCX, TXT, CSV, or XLSX file.');
      }
    }
  }

  async function handleUpload() {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev < 90) return prev + Math.random() * 30;
          return prev;
        });
      }, 200);

      // Upload the file
      const uploadResponse = await uploadDocument(file, assignedUserId);
      clearInterval(progressInterval);
      setUploadProgress(100);

      // Start extraction
      setExtracting(true);
      setTimeout(() => {
        handleExtract(uploadResponse.upload_id);
      }, 500);
    } catch (error) {
      setError(error.message || 'Upload failed. Please try again.');
      setUploading(false);
    }
  }

  async function handleExtract(uploadId) {
    try {
      if (onExtractionStart) {
        onExtractionStart();
      }

      const extractResponse = await extractInformation(uploadId);
      // Poll for results
      pollForResults(extractResponse.extraction_id);
    } catch (error) {
      setError(error.message || 'Extraction failed. Please try again.');
      setExtracting(false);
    }
  }

  function pollForResults(extractionId) {
    const maxPolls = 60; // 60 seconds max
    let pollCount = 0;

    const pollInterval = setInterval(async () => {
      pollCount += 1;

      try {
        // Use the api service (correct base URL, interceptors) instead of raw fetch
        const results = await getResults(extractionId);

        if (results.status === 'completed') {
          clearInterval(pollInterval);
          setExtracting(false);
          setUploading(false);
          setFile(null);
          setUploadProgress(0);

          if (onExtractComplete) {
            onExtractComplete(results);
          }
        } else if (results.status === 'failed') {
          clearInterval(pollInterval);
          setExtracting(false);
          setUploading(false);
          setError(results.error_message || 'Extraction failed.');
        } else if (pollCount >= maxPolls) {
          clearInterval(pollInterval);
          setExtracting(false);
          setUploading(false);
          setError('Extraction timed out. Please try again.');
        }
      } catch (error) {
        if (pollCount >= maxPolls) {
          clearInterval(pollInterval);
          setExtracting(false);
          setUploading(false);
          setError('Could not retrieve extraction results.');
        }
      }
    }, 1000);
  }

  function handleClear() {
    setFile(null);
    setUploadProgress(0);
  }

  return (
    <div className="upload-container">
      <div className="card">
        <div className="card-header">
          📄 Upload Tender Document
        </div>

        <div className="card-body p-3">
          <div
            {...getRootProps()}
            className={`dropzone ${isDragActive ? 'active' : ''} ${
              uploading || extracting ? 'disabled' : ''
            }`}
          >
            <input {...getInputProps()} disabled={uploading || extracting} />
            <div className="dropzone-content">
              <div className="dropzone-icon">📁</div>
              <p className="dropzone-title">
                {isDragActive
                  ? 'Drop your file here'
                  : 'Drag and drop your tender document here'}
              </p>
              <p className="dropzone-subtitle">or click to select a file</p>
              <p className="dropzone-formats">
                Supported formats: PDF, DOCX, TXT, CSV, XLSX (Max 50MB)
              </p>
            </div>
          </div>

          {file && (
            <div className="file-preview mt-3">
              <div className="file-preview-item">
                <div className="file-icon">📄</div>
                <div className="file-info">
                  <div className="file-name">{file.name}</div>
                  <div className="file-size">{formatFileSize(file.size)}</div>
                </div>
                {!uploading && !extracting && (
                  <button
                    className="btn btn-outline btn-sm"
                    onClick={handleClear}
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>
          )}

          {uploadProgress > 0 && (
            <div className="progress mt-3">
              <div
                className="progress-bar"
                style={{ width: `${uploadProgress}%` }}
              >
                <span className="progress-text">{Math.round(uploadProgress)}%</span>
              </div>
            </div>
          )}

          <div className="mb-3">
            <label htmlFor="assignedUser" className="form-label">
              Assign tender to user
            </label>
            <select
              id="assignedUser"
              value={assignedUserId}
              onChange={(e) => setAssignedUserId(e.target.value)}
              className="form-control"
              disabled={uploading || extracting}
            >
              <option value="">Select user</option>
              {users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.name}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <div className="alert alert-danger mt-2">
              {error}
            </div>
          )}

          <div className="mt-3">
            {uploading && (
              <div className="upload-status flex-center gap-2">
                <div className="spinner"></div>
                <span>Uploading and extracting...</span>
              </div>
            )}

            {extracting && (
              <div className="extract-status flex-center gap-2">
                <div className="spinner"></div>
                <span>Processing tender document...</span>
              </div>
            )}

            {!uploading && !extracting && (
              <button
                className="btn btn-primary btn-lg"
                onClick={handleUpload}
                disabled={!file}
                style={{ width: '100%' }}
              >
                Upload & Extract
              </button>
            )}
          </div>
        </div>
      </div>

    </div>
  );
};

export default Upload;
