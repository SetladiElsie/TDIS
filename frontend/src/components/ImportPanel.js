import React, { useEffect, useState } from 'react';
import { importDocument, extractInformation, getResults } from '../services/api';
import '../styles/Upload.css';

const ImportPanel = ({ downloadUrl, onExtractionStart, onExtractComplete }) => {
  const [status, setStatus] = useState('starting');
  const [downloadInfo, setDownloadInfo] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function importAndExtract() {
      try {
        setStatus('importing');
        const importResponse = await importDocument(downloadUrl);
        setDownloadInfo(importResponse);

        if (onExtractionStart) {
          onExtractionStart();
        }

        setStatus('extracting');
        const extractResponse = await extractInformation(importResponse.upload_id);
        await pollForResults(extractResponse.extraction_id);
      } catch (err) {
        setError(err.message || 'Import failed');
        setStatus('failed');
      }
    }

    importAndExtract();
  }, [downloadUrl]);

  async function pollForResults(extractionId) {
    const maxPolls = 60;
    let pollCount = 0;

    return new Promise((resolve, reject) => {
      const pollInterval = setInterval(async () => {
        pollCount += 1;

        try {
          const results = await getResults(extractionId);

          if (results.status === 'completed') {
            clearInterval(pollInterval);
            setStatus('completed');
            if (onExtractComplete) {
              onExtractComplete(results);
            }
            resolve(results);
          } else if (results.status === 'failed') {
            clearInterval(pollInterval);
            setStatus('failed');
            setError(results.error_message || 'Extraction failed');
            reject(new Error(results.error_message || 'Extraction failed'));
          } else if (pollCount >= maxPolls) {
            clearInterval(pollInterval);
            setStatus('timed_out');
            setError('Extraction timed out. Please try again.');
            reject(new Error('Extraction timed out'));
          }
        } catch (err) {
          if (pollCount >= maxPolls) {
            clearInterval(pollInterval);
            setStatus('timed_out');
            setError('Could not retrieve extraction results.');
            reject(new Error('Could not retrieve extraction results'));
          }
        }
      }, 1000);
    });
  }

  return (
    <div className="upload-container">
      <div className="card">
        <div className="card-header">Import Tender Document</div>
        <div className="card-body p-3">
          <p>This page will fetch the tender document from the tracker link and start extraction.</p>
          <p><strong>Source URL:</strong> <a href={downloadUrl} target="_blank" rel="noreferrer">{downloadUrl}</a></p>
          {status === 'starting' && <p>Preparing import...</p>}
          {status === 'importing' && <p>Downloading document...</p>}
          {status === 'extracting' && <p>Document downloaded. Extracting now...</p>}
          {status === 'completed' && <p>Extraction completed successfully.</p>}
          {status === 'failed' && <p className="text-danger">Import failed: {error}</p>}
          {status === 'timed_out' && <p className="text-warning">Extraction timed out. Please try again later.</p>}
        </div>
      </div>
    </div>
  );
};

export default ImportPanel;
