/**
 * LoadingSpinner - Reusable loading indicator
 */

import React from 'react';
import './common.css';

/**
 * LoadingSpinner component
 *
 * @param {Object} props
 * @param {string} props.size - Size: 'small' | 'medium' | 'large' (default: 'medium')
 * @param {string} props.message - Optional loading message
 * @param {boolean} props.overlay - Show as overlay (default: false)
 * @param {boolean} props.inline - Inline display (default: false)
 */
export function LoadingSpinner({
  size = 'medium',
  message = 'Caricamento...',
  overlay = false,
  inline = false,
}) {
  const spinner = (
    <div className={`core-loading-spinner core-loading-spinner--${size} ${inline ? 'core-loading-spinner--inline' : ''}`}>
      <div className="core-loading-spinner__circle"></div>
      {message && !inline && (
        <p className="core-loading-spinner__message">{message}</p>
      )}
    </div>
  );

  if (overlay) {
    return (
      <div className="core-loading-overlay">
        {spinner}
      </div>
    );
  }

  return spinner;
}

export default LoadingSpinner;
