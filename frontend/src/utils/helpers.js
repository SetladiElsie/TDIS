import { formatDistanceToNow, format, isPast } from 'date-fns';

/**
 * Format date string to readable format
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    return format(new Date(dateString), 'MMM dd, yyyy HH:mm');
  } catch {
    return dateString;
  }
};

/**
 * Format date to relative time (e.g., "2 hours ago")
 * @param {string} dateString - ISO date string
 * @returns {string} Relative time
 */
export const formatDateRelative = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    return formatDistanceToNow(new Date(dateString), { addSuffix: true });
  } catch {
    return dateString;
  }
};

/**
 * Check if closing date has passed
 * @param {string} dateString - ISO date string
 * @returns {boolean} True if date has passed
 */
export const isClosingDatePassed = (dateString) => {
  if (!dateString) return false;
  try {
    return isPast(new Date(dateString));
  } catch {
    return false;
  }
};

/**
 * Format currency
 * @param {number} amount - Amount to format
 * @param {string} currency - Currency code (default: USD)
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (amount, currency = 'USD') => {
  if (!amount) return `${currency} 0`;
  
  const currencySymbols = {
    USD: '$',
    EUR: '€',
    GBP: '£',
    INR: '₹',
    JPY: '¥',
  };

  const symbol = currencySymbols[currency] || currency;
  return `${symbol} ${parseFloat(amount).toLocaleString()}`;
};

/**
 * Truncate text to specified length
 * @param {string} text - Text to truncate
 * @param {number} length - Max length (default: 100)
 * @returns {string} Truncated text with ellipsis
 */
export const truncateText = (text, length = 100) => {
  if (!text) return '';
  if (text.length <= length) return text;
  return text.substring(0, length) + '...';
};

/**
 * Format file size
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
export const formatFileSize = (bytes) => {
  if (!bytes) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

/**
 * Get status badge color
 * @param {string} status - Status value
 * @returns {string} CSS class for status
 */
export const getStatusColor = (status) => {
  const statusColors = {
    completed: 'success',
    processing: 'info',
    failed: 'danger',
    uploaded: 'warning',
  };
  return statusColors[status] || 'secondary';
};

/**
 * Get status icon
 * @param {string} status - Status value
 * @returns {string} Icon name
 */
export const getStatusIcon = (status) => {
  const statusIcons = {
    completed: '✓',
    processing: '⟳',
    failed: '✕',
    uploaded: '↑',
  };
  return statusIcons[status] || '?';
};

/**
 * Download JSON data as file
 * @param {Object} data - Data to download
 * @param {string} filename - Output filename
 */
export const downloadJSON = (data, filename = 'data.json') => {
  const dataStr = JSON.stringify(data, null, 2);
  const dataBlob = new Blob([dataStr], { type: 'application/json' });
  const url = window.URL.createObjectURL(dataBlob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.parentNode.removeChild(link);
  window.URL.revokeObjectURL(url);
};

/**
 * Validate file type
 * @param {File} file - File to validate
 * @param {Array} allowedTypes - Allowed MIME types
 * @returns {boolean} True if file type is allowed
 */
export const isFileTypeAllowed = (file, allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']) => {
  return allowedTypes.includes(file.type);
};

/**
 * Get confidence percentage display
 * @param {number} score - Confidence score (0-1)
 * @returns {Object} Display object with percentage and color
 */
export const getConfidenceDisplay = (score) => {
  if (!score) return { percentage: 0, color: 'gray', label: 'N/A' };
  
  const percentage = Math.round(score * 100);
  let color = 'red';
  
  if (percentage >= 90) color = 'green';
  else if (percentage >= 70) color = 'yellow';
  else if (percentage >= 50) color = 'orange';
  
  return {
    percentage,
    color,
    label: `${percentage}%`,
  };
};

/**
 * Parse extraction data safely
 * @param {Object} data - Extraction data
 * @returns {Object} Parsed data with defaults
 */
export const parseExtractionData = (data) => {
  return {
    tender_id: data?.tender_id || 'N/A',
    tender_name: data?.tender_name || 'Unknown Tender',
    organization: data?.organization || 'N/A',
    scope_of_work: data?.scope_of_work || 'No scope provided',
    closing_date: data?.closing_date || null,
    closing_date_formatted: data?.closing_date_formatted || 'N/A',
    budget: data?.budget || { amount: null, currency: 'USD' },
    contact_email: data?.contact_email || 'N/A',
    contact_phone: data?.contact_phone || 'N/A',
    location: data?.location || 'N/A',
    document_type: data?.document_type || 'N/A',
    estimated_duration: data?.estimated_duration || 'N/A',
    submission_format: data?.submission_format || 'N/A',
    key_requirements: Array.isArray(data?.key_requirements) ? data.key_requirements : [],
    evaluation_criteria: Array.isArray(data?.evaluation_criteria) ? data.evaluation_criteria : [],
    deliverables: Array.isArray(data?.deliverables) ? data.deliverables : [],
    compulsory_documents: Array.isArray(data?.compulsory_documents) ? data.compulsory_documents : [],
  };
};
