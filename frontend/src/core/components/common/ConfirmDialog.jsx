/**
 * ConfirmDialog - Confirmation dialog component
 */

import React from 'react';
import './common.css';

/**
 * ConfirmDialog component
 *
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether dialog is open
 * @param {string} props.title - Dialog title
 * @param {string} props.message - Dialog message
 * @param {string} props.confirmLabel - Confirm button label (default: 'Conferma')
 * @param {string} props.cancelLabel - Cancel button label (default: 'Annulla')
 * @param {string} props.variant - Variant: 'default' | 'danger' (default: 'default')
 * @param {Function} props.onConfirm - Confirm callback
 * @param {Function} props.onCancel - Cancel callback
 * @param {boolean} props.loading - Loading state
 */
export function ConfirmDialog({
  isOpen,
  title = 'Conferma',
  message,
  confirmLabel = 'Conferma',
  cancelLabel = 'Annulla',
  variant = 'default',
  onConfirm,
  onCancel,
  loading = false,
}) {
  if (!isOpen) return null;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget && !loading) {
      onCancel?.();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape' && !loading) {
      onCancel?.();
    }
  };

  React.useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, loading]);

  return (
    <div
      className="core-confirm-dialog__overlay"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
    >
      <div className="core-confirm-dialog">
        <h3 id="confirm-dialog-title" className="core-confirm-dialog__title">
          {title}
        </h3>
        {message && (
          <p className="core-confirm-dialog__message">{message}</p>
        )}
        <div className="core-confirm-dialog__actions">
          <button
            type="button"
            className="core-confirm-dialog__cancel"
            onClick={onCancel}
            disabled={loading}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className={`core-confirm-dialog__confirm core-confirm-dialog__confirm--${variant}`}
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? 'Attendere...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmDialog;
