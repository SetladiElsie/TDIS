import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
const API_TIMEOUT = parseInt(process.env.REACT_APP_API_TIMEOUT) || 30000;

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      return Promise.reject({
        status: error.response.status,
        message: error.response.data?.error || 'An error occurred',
        code: error.response.data?.code || 'UNKNOWN_ERROR',
        details: error.response.data?.details,
      });
    } else if (error.request) {
      // Request made but no response
      return Promise.reject({
        status: 0,
        message: 'No response from server. Please check if the API is running.',
        code: 'NO_RESPONSE',
      });
    } else {
      return Promise.reject({
        status: 0,
        message: error.message || 'An error occurred',
        code: 'ERROR',
      });
    }
  }
);

/**
 * Upload a tender document
 * @param {File} file - Document file to upload
 * @returns {Promise<Object>} Upload response with upload_id
 */
export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

/**
 * Extract information from uploaded document
 * @param {string} uploadId - Upload ID from uploadDocument
 * @returns {Promise<Object>} Extraction response with extraction_id
 */
export const extractInformation = async (uploadId) => {
  const response = await apiClient.post('/extract', {
    upload_id: uploadId,
  });

  return response.data;
};

/**
 * Get extraction results
 * @param {string} extractionId - Extraction ID
 * @returns {Promise<Object>} Extraction results
 */
export const getResults = async (extractionId) => {
  const response = await apiClient.get(`/results/${extractionId}`);
  return response.data;
};

/**
 * List all extraction results with pagination
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number (default: 1)
 * @param {number} params.limit - Items per page (default: 20)
 * @param {string} params.search - Search query
 * @param {string} params.status - Filter by status
 * @returns {Promise<Object>} Paginated results
 */
export const listResults = async (params = {}) => {
  const response = await apiClient.get('/results', { params });
  return response.data;
};

/**
 * Export results
 * @param {string} extractionId - Extraction ID
 * @param {string} format - Export format (json, csv)
 * @returns {Promise<Object|Blob>} Exported data
 */
export const exportResults = async (extractionId, format = 'json') => {
  const response = await apiClient.get(`/export/${extractionId}`, {
    params: { format },
    responseType: format === 'csv' ? 'blob' : 'json',
  });

  if (format === 'csv') {
    // Create blob and download
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `extraction_${extractionId}.csv`);
    document.body.appendChild(link);
    link.click();
    link.parentNode.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  return response.data;
};

/**
 * Delete extraction result
 * @param {string} extractionId - Extraction ID
 * @returns {Promise<void>}
 */
export const deleteResult = async (extractionId) => {
  await apiClient.delete(`/results/${extractionId}`);
};

/**
 * Health check
 * @returns {Promise<Object>} Health status
 */
export const healthCheck = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

export default apiClient;
