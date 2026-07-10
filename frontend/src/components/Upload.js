import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadDocument, extractInformation } from '../services/api';
import { formatFileSize, isFileTypeAllowed } from '../utils/helpers';
import { ToastContainer, toast } from 'react-toastify';
import '../styles/Upload.css';

const Upload = ({ onExtractionStart, onExtractComplete }) => {
  const [uploading, setUploading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

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

  function handleDrop(acceptedFiles) {
    if (acceptedFiles.length > 0) {
      const droppedFile = acceptedFiles[0];
      if (isFileTypeAllowed(droppedFile, allowedFormats)) {
        setFile(droppedFile);
        toast.success(`File "${droppedFile.name}" selected successfully!`);
      } else {
        toast.error('File type not supported. Please upload a PDF, DOCX, TXT, CSV, or XLSX file.');
      }
    }
  }

  async function handleUpload() {
    if (!file) {
      toast.error('Please select a file first');
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
      const uploadResponse = await uploadDocument(file);
      clearInterval(progressInterval);
      setUploadProgress(100);

      toast.success('File uploaded successfully!');

      // Start extraction
      setExtracting(true);
      setTimeout(() => {
        handleExtract(uploadResponse.upload_id);
      }, 500);
    } catch (error) {
      toast.error(error.message || 'Upload failed. Please try again.');
      setUploading(false);
    }
  }

  async function handleExtract(uploadId) {
    try {
      if (onExtractionStart) {
        onExtractionStart();
      }

      const extractResponse = await extractInformation(uploadId);
      toast.success('Extraction started. Processing document...');

      // Poll for results
      pollForResults(extractResponse.extraction_id);
    } catch (error) {
      toast.error(error.message || 'Extraction failed. Please try again.');
      setExtracting(false);
    }
  }

  function pollForResults(extractionId, pollCount = 0, maxPolls = 30) {
    const pollInterval = setInterval(async () => {
      try {
        const resultsResponse = await fetch(
          `${process.env.REACT_APP_API_URL}/results/${extractionId}`
        );
        const results = await resultsResponse.json();

        if (results.status === 'completed') {
          clearInterval(pollInterval);
          setExtracting(false);
          setUploading(false);
          setFile(null);
          setUploadProgress(0);
          toast.success('Extraction completed successfully!');

          if (onExtractComplete) {
            onExtractComplete(results);
          }
        } else if (results.status === 'failed') {
          clearInterval(pollInterval);
          setExtracting(false);
          setUploading(false);
          toast.error(`Extraction failed: ${results.error_message}`);
        } else if (pollCount >= maxPolls) {
          clearInterval(pollInterval);
          setExtracting(false);
          setUploading(false);
          toast.error('Extraction timeout. Please try again later.');
        }
      } catch (error) {
        if (pollCount >= maxPolls) {
          clearInterval(pollInterval);
          setExtracting(false);
          setUploading(false);
          toast.error('Could not retrieve extraction results.');
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

      <ToastContainer
        position="bottom-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop={true}
      />
    </div>
  );
};

export default Upload;
