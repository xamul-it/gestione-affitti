/**
 * ErrorMessage - Display error messages
 */

import React from 'react';
import './common.css';

/**
 * ErrorMessage component
 *
 * @param {Object} props
 * @param {string} props.message - Error message to display
 * @param {Function} props.onRetry - Retry callback
 * @param {Function} props.onDismiss - Dismiss callback
 * @param {string} props.variant - Variant: 'error' | 'warning' | 'info' (default: 'error')
 */
export function ErrorMessage({
  message,
  onRetry,
  onDismiss,
  variant = 'error',
}) {
  if (!message) return null;

  return (
    <div className={`core-error-message core-error-message--${variant}`}>
      <div className="core-error-message__content">
        <span className="core-error-message__icon">
          {variant === 'error' && '!'}
          {variant === 'warning' && '!'}
          {variant === 'info' && 'i'}
        </span>
        <p className="core-error-message__text">{message}</p>
      </div>
      <div className="core-error-message__actions">
        {onRetry && (
          <button
            type="button"
            className="core-error-message__retry"
            onClick={onRetry}
          >
            Riprova
          </button>
        )}
        {onDismiss && (
          <button
            type="button"
            className="core-error-message__dismiss"
            onClick={onDismiss}
            aria-label="Chiudi"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
}

export default ErrorMessage;
