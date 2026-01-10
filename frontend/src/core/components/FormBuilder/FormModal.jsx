/**
 * FormModal - Modal wrapper for forms
 *
 * Provides a modal container for FormBuilder or custom forms.
 *
 * @example
 * <FormModal title="Nuovo Affittuario" onClose={handleClose}>
 *   <FormBuilder config={config} ... />
 * </FormModal>
 */

import React, { useEffect, useCallback } from 'react';
import './FormBuilder.css';

/**
 * FormModal component
 */
export function FormModal({
  title,
  children,
  onClose,
  size = 'medium', // small | medium | large | fullscreen
  closeOnBackdrop = true,
  closeOnEscape = true,
  showCloseButton = true,
}) {
  /**
   * Handle backdrop click
   */
  const handleBackdropClick = useCallback((e) => {
    if (closeOnBackdrop && e.target === e.currentTarget) {
      onClose?.();
    }
  }, [closeOnBackdrop, onClose]);

  /**
   * Handle escape key
   */
  useEffect(() => {
    if (!closeOnEscape) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [closeOnEscape, onClose]);

  /**
   * Prevent body scroll when modal is open
   */
  useEffect(() => {
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, []);

  return (
    <div
      className="core-form-modal__overlay"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className={`core-form-modal core-form-modal--${size}`}>
        {/* Header */}
        <div className="core-form-modal__header">
          <h2 id="modal-title" className="core-form-modal__title">
            {title}
          </h2>
          {showCloseButton && (
            <button
              type="button"
              className="core-form-modal__close"
              onClick={onClose}
              aria-label="Chiudi"
            >
              ×
            </button>
          )}
        </div>

        {/* Content */}
        <div className="core-form-modal__content">
          {children}
        </div>
      </div>
    </div>
  );
}

export default FormModal;
