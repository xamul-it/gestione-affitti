/**
 * Toast - Toast notification component
 *
 * Displays toast notifications with animations.
 * Managed globally via useToast hook.
 */

import React, { useState, useEffect } from 'react';
import { subscribeToToasts } from '../../hooks/useToast';
import './Toast.css';

/**
 * Single toast notification
 */
function ToastItem({ toast, onDismiss }) {
  const { id, type, message, action } = toast;

  useEffect(() => {
    // Add entrance animation
    const timer = setTimeout(() => {
      const element = document.getElementById(`toast-${id}`);
      if (element) {
        element.classList.add('toast--visible');
      }
    }, 10);

    return () => clearTimeout(timer);
  }, [id]);

  const handleDismiss = () => {
    const element = document.getElementById(`toast-${id}`);
    if (element) {
      element.classList.remove('toast--visible');
      element.classList.add('toast--exit');
      setTimeout(() => onDismiss(id), 150);
    }
  };

  const getIcon = () => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✕';
      case 'warning':
        return '⚠';
      case 'info':
      default:
        return 'ℹ';
    }
  };

  return (
    <div id={`toast-${id}`} className={`toast toast--${type}`} role="alert">
      <div className="toast__icon">{getIcon()}</div>
      <div className="toast__content">
        <p className="toast__message">{message}</p>
        {action && (
          <button
            type="button"
            className="toast__action"
            onClick={() => {
              action.onClick();
              handleDismiss();
            }}
          >
            {action.label}
          </button>
        )}
      </div>
      <button
        type="button"
        className="toast__close"
        onClick={handleDismiss}
        aria-label="Chiudi notifica"
      >
        ×
      </button>
    </div>
  );
}

/**
 * Toast container component
 */
export function ToastContainer() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    const unsubscribe = subscribeToToasts((toast) => {
      if (toast.dismissed) {
        setToasts((prev) => prev.filter((t) => t.id !== toast.id));
      } else {
        setToasts((prev) => [...prev, toast]);
      }
    });

    return unsubscribe;
  }, []);

  const handleDismiss = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={handleDismiss} />
      ))}
    </div>
  );
}

export default ToastContainer;
