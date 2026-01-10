/**
 * Format API error for display
 * Handles Pydantic validation errors (array of objects) and string errors
 *
 * @param {Error} err - The error object from API call
 * @returns {string} Formatted error message
 */
export function formatApiError(err) {
  const detail = err.response?.data?.detail;

  // Handle Pydantic validation errors (array of error objects)
  if (Array.isArray(detail)) {
    const errorMessages = detail.map(e => {
      if (typeof e === 'string') return e;
      if (e.msg) return e.msg;
      return JSON.stringify(e);
    }).join(', ');
    return errorMessages;
  }

  // Handle string errors
  if (typeof detail === 'string') {
    return detail;
  }

  // Handle error objects with message
  if (detail && typeof detail === 'object' && detail.message) {
    return detail.message;
  }

  // Fallback to generic error message
  return err.message || 'Errore nel salvataggio';
}
