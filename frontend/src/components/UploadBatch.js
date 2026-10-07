import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadBatchDocuments, extractBatch, getResults } from '../services/api';
import { formatFileSize, isFileTypeAllowed } from '../utils/helpers';
import '../styles/Upload.css';

const UploadBatch = ({ onExtractionStart, onExtractComplete }) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [fileStatus, setFileStatus] = useState({});
  const [error, setError] = useState(null);
  const [completed, setCompleted] = useState(0);

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
    maxSize: 100 * 1024 * 1024, // 100MB per file
    noClick: false,
    multiple: true,
    maxFiles: undefined, // No limit on number of files
  });

  function handleDrop(acceptedFiles) {
    const validFiles = acceptedFiles.filter(f => isFileTypeAllowed(f, allowedFormats));
    if (validFiles.length > 0) {
      setFiles(prev => [...prev, ...validFiles]);
      setError(null);
    }
    if (validFiles.length < acceptedFiles.length) {
      setError(`${acceptedFiles.length - validFiles.length} file(s) skipped (unsupported format)`);
    }
  }

  function handleRemoveFile(index) {
    setFiles(prev => prev.filter((_, i) => i !== index));
  }

  function handleClearAll() {
    setFiles([]);
    setFileStatus({});
    setError(null);
    setCompleted(0);
  }

  async function handleBatchUpload() {
    if (files.length === 0) {
      setError('Please select at least one file');
      return;
    }

    console.log('Starting batch upload with files:', files);
    setUploading(true);
    setError(null);

    // Initialize status for all files
    const initialStatus = {};
    files.forEach((file, idx) => {
      initialStatus[idx] = { status: 'uploading', filename: file.name };
    });
    setFileStatus(initialStatus);

    try {
      console.log('Calling uploadBatchDocuments API...');
      // Upload all files
      const response = await uploadBatchDocuments(files);
      console.log('Upload response:', response);
      
      if (response.uploaded && response.uploaded.length > 0) {
        console.log(`Successfully uploaded ${response.uploaded.length} files`);
        
        // Update status for uploaded files
        const newStatus = { ...initialStatus };
        response.uploaded.forEach((uploadedFile, idx) => {
          newStatus[idx] = { 
            ...newStatus[idx],
            status: 'uploaded',
            upload_id: uploadedFile.upload_id
          };
        });
        response.skipped.forEach((skipped, idx) => {
          const fileIdx = files.findIndex(f => f.name === skipped.filename);
          if (fileIdx >= 0) {
            newStatus[fileIdx] = { 
              ...newStatus[fileIdx],
              status: 'failed',
              error: skipped.reason
            };
          }
        });
        setFileStatus(newStatus);
        setUploading(false);

        // Remove successfully uploaded files from the list
        const uploadedFilenames = response.uploaded.map(u => u.filename);
        setFiles(prev => prev.filter(file => !uploadedFilenames.includes(file.name)));

        // Start extraction for all uploaded files
        const uploadIds = response.uploaded.map(u => u.upload_id);
        console.log('Starting extraction for upload IDs:', uploadIds);
        if (uploadIds.length > 0) {
          handleBatchExtract(uploadIds, newStatus);
        }
      } else {
        console.error('No files uploaded:', response);
        setError('No files were uploaded successfully');
        setUploading(false);
      }
    } catch (err) {
      console.error('Upload failed:', err);
      setError(err.message || 'Upload failed. Please try again.');
      setUploading(false);
    }
  }

  async function handleBatchExtract(uploadIds, currentStatus) {
    setExtracting(true);
    if (onExtractionStart) {
      onExtractionStart();
    }

    try {
      const response = await extractBatch(uploadIds);
      console.log('Batch extraction response:', response);
      
      if (response.extraction_id) {
        console.log('Single extraction created for batch:', response.extraction_id);
        
        // Update all files to show they're being extracted together
        const newStatus = { ...currentStatus };
        Object.keys(newStatus).forEach(idx => {
          if (newStatus[idx].upload_id) {
            newStatus[idx] = {
              ...newStatus[idx],
              status: 'extracting',
              extraction_id: response.extraction_id
            };
          }
        });
        setFileStatus(newStatus);

        // Poll for the single extraction
        pollForBatchResults(response.extraction_id, Object.keys(newStatus).length);
      }
    } catch (err) {
      console.error('Batch extraction failed:', err);
      setError(err.message || 'Extraction failed. Please try again.');
      setExtracting(false);
    }
  }

  function pollForBatchResults(extractionId, totalFiles) {
    const maxPolls = 120; // 2 minutes max
    let pollCount = 0;

    const pollInterval = setInterval(async () => {
      pollCount += 1;

      try {
        const results = await getResults(extractionId);

        if (results.status === 'completed' || results.status === 'failed') {
          clearInterval(pollInterval);

          // Update all files to completed/failed
          setFileStatus(prev => {
            const newStatus = { ...prev };
            Object.keys(newStatus).forEach(idx => {
              if (newStatus[idx].extraction_id === extractionId) {
                newStatus[idx] = {
                  ...newStatus[idx],
                  status: results.status,
                  error: results.error_message
                };
              }
            });
            return newStatus;
          });

          setCompleted(totalFiles);
          setExtracting(false);
          
          if (onExtractComplete) {
            onExtractComplete();
          }
        } else if (pollCount >= maxPolls) {
          clearInterval(pollInterval);
          setFileStatus(prev => {
            const newStatus = { ...prev };
            Object.keys(newStatus).forEach(idx => {
              if (newStatus[idx].extraction_id === extractionId) {
                newStatus[idx] = {
                  ...newStatus[idx],
                  status: 'failed',
                  error: 'Extraction timed out'
                };
              }
            });
            return newStatus;
          });
          setExtracting(false);
        }
      } catch (error) {
        if (pollCount >= maxPolls) {
          clearInterval(pollInterval);
          setExtracting(false);
        }
      }
    }, 2000); // Poll every 2 seconds
  }

  const totalFiles = files.length;
  const uploadedCount = Object.values(fileStatus).filter(s => s.status !== 'uploading').length;

  return (
    <div className="upload-container">
      <div className="card">
        <div className="card-header">
          <div className="flex-between">
            <span>Upload Documents</span>
            {files.length > 0 && (
              <span className="badge">{files.length} file(s)</span>
            )}
          </div>
        </div>

        <div className="card-body">
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
                  ? 'Drop your files here'
                  : 'Upload Multiple Documents'}
              </p>
              <p className="dropzone-subtitle">Drag and drop or click to browse</p>
              <p className="dropzone-formats">
                PDF, DOCX, TXT, CSV, XLSX (Max 50MB each)
              </p>
            </div>
          </div>

          {files.length > 0 && (
            <div className="file-list mt-3">
              {files.map((file, idx) => {
                const status = fileStatus[idx];
                return (
                  <div key={idx} className="file-list-item">
                    <div className="file-icon">📄</div>
                    <div className="file-info">
                      <div className="file-name">{file.name}</div>
                      <div className="file-size">{formatFileSize(file.size)}</div>
                    </div>
                    <div className="file-status">
                      {status?.status === 'uploading' && <span className="status-badge uploading">Uploading...</span>}
                      {status?.status === 'uploaded' && <span className="status-badge uploaded">Uploaded</span>}
                      {status?.status === 'extracting' && <span className="status-badge extracting">Extracting...</span>}
                      {status?.status === 'completed' && <span className="status-badge completed">✓ Done</span>}
                      {status?.status === 'failed' && <span className="status-badge failed">✗ Failed</span>}
                    </div>
                    {!uploading && !extracting && (
                      <button
                        className="btn-icon"
                        onClick={() => handleRemoveFile(idx)}
                        title="Remove"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {error && (
            <div className="alert alert-danger mt-2">
              {error}
            </div>
          )}

          {(uploading || extracting) && (
            <div className="batch-progress mt-3">
              <div className="progress-info">
                <span>
                  {uploading ? 'Uploading...' : `Extracting... ${completed} of ${totalFiles} completed`}
                </span>
              </div>
            </div>
          )}

          <div className="mt-3 flex-between">
            {files.length > 0 && !uploading && !extracting && (
              <button
                className="btn btn-outline"
                onClick={handleClearAll}
              >
                Clear All
              </button>
            )}
            {!uploading && !extracting && (
              <button
                className="btn btn-primary btn-lg"
                onClick={handleBatchUpload}
                disabled={files.length === 0}
                style={{ marginLeft: 'auto' }}
              >
                Upload & Extract All ({files.length})
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadBatch;
