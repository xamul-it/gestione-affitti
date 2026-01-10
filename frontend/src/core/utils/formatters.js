/**
 * Core Formatters - Utility functions for formatting values
 *
 * These formatters are used throughout the core components for
 * consistent display of dates, currencies, numbers, etc.
 */

/**
 * Format a date string to Italian locale format
 * @param {string|Date} dateValue - Date to format
 * @param {Object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted date string
 */
export function formatDate(dateValue, options = {}) {
  if (!dateValue) return '-';

  try {
    const date = dateValue instanceof Date ? dateValue : new Date(dateValue);
    if (isNaN(date.getTime())) return '-';

    const defaultOptions = {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      ...options,
    };

    return new Intl.DateTimeFormat('it-IT', defaultOptions).format(date);
  } catch {
    return '-';
  }
}

/**
 * Format a date string to datetime format
 * @param {string|Date} dateValue - Date to format
 * @returns {string} Formatted datetime string
 */
export function formatDateTime(dateValue) {
  return formatDate(dateValue, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format a number as currency
 * @param {number|string} value - Value to format
 * @param {string} currency - Currency code (default: EUR)
 * @returns {string} Formatted currency string
 */
export function formatCurrency(value, currency = 'EUR') {
  if (value === null || value === undefined || value === '') return '-';

  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(numValue)) return '-';

  return new Intl.NumberFormat('it-IT', {
    style: 'currency',
    currency,
  }).format(numValue);
}

/**
 * Format a number with locale formatting
 * @param {number|string} value - Value to format
 * @param {Object} options - Intl.NumberFormat options
 * @returns {string} Formatted number string
 */
export function formatNumber(value, options = {}) {
  if (value === null || value === undefined || value === '') return '-';

  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(numValue)) return '-';

  return new Intl.NumberFormat('it-IT', options).format(numValue);
}

/**
 * Format a number as percentage
 * @param {number|string} value - Value to format (0-100 or 0-1)
 * @param {boolean} isDecimal - If true, value is treated as decimal (0-1)
 * @returns {string} Formatted percentage string
 */
export function formatPercent(value, isDecimal = false) {
  if (value === null || value === undefined || value === '') return '-';

  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(numValue)) return '-';

  const displayValue = isDecimal ? numValue : numValue / 100;

  return new Intl.NumberFormat('it-IT', {
    style: 'percent',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(displayValue);
}

/**
 * Format a boolean value to Italian string
 * @param {boolean} value - Boolean value
 * @param {Object} labels - Custom labels { true: '', false: '' }
 * @returns {string} Formatted string
 */
export function formatBoolean(value, labels = {}) {
  const { true: trueLabel = 'Si', false: falseLabel = 'No' } = labels;
  if (value === null || value === undefined) return '-';
  return value ? trueLabel : falseLabel;
}

/**
 * Format a phone number
 * @param {string} value - Phone number
 * @returns {string} Formatted phone number
 */
export function formatPhone(value) {
  if (!value) return '-';
  // Remove non-digits
  const cleaned = value.replace(/\D/g, '');
  // Format Italian phone numbers
  if (cleaned.length === 10) {
    return `${cleaned.slice(0, 3)} ${cleaned.slice(3, 6)} ${cleaned.slice(6)}`;
  }
  return value;
}

/**
 * Format file size in bytes to human readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
export function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const size = (bytes / Math.pow(1024, i)).toFixed(2);

  return `${size} ${units[i]}`;
}

/**
 * Truncate text to specified length with ellipsis
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
export function truncate(text, maxLength = 50) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return `${text.substring(0, maxLength)}...`;
}

/**
 * Get nested object value by path
 * @param {Object} obj - Object to traverse
 * @param {string} path - Dot-separated path (e.g., 'user.address.city')
 * @param {*} defaultValue - Default value if path not found
 * @returns {*} Value at path or default
 */
export function getNestedValue(obj, path, defaultValue = null) {
  if (!obj || !path) return defaultValue;

  const keys = path.split('.');
  let current = obj;

  for (const key of keys) {
    if (current === null || current === undefined) {
      return defaultValue;
    }
    current = current[key];
  }

  return current !== undefined ? current : defaultValue;
}

/**
 * Format value based on type
 * @param {*} value - Value to format
 * @param {string} type - Type of formatting
 * @param {Object} options - Additional options
 * @returns {string} Formatted value
 */
export function formatValue(value, type = 'text', options = {}) {
  switch (type) {
    case 'date':
      return formatDate(value, options);
    case 'datetime':
      return formatDateTime(value);
    case 'currency':
      return formatCurrency(value, options.currency);
    case 'number':
      return formatNumber(value, options);
    case 'percent':
      return formatPercent(value, options.isDecimal);
    case 'boolean':
      return formatBoolean(value, options);
    case 'phone':
      return formatPhone(value);
    case 'filesize':
      return formatFileSize(value);
    case 'text':
    default:
      if (value === null || value === undefined || value === '') return '-';
      return String(value);
  }
}

export default {
  formatDate,
  formatDateTime,
  formatCurrency,
  formatNumber,
  formatPercent,
  formatBoolean,
  formatPhone,
  formatFileSize,
  truncate,
  getNestedValue,
  formatValue,
};
