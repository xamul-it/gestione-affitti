/**
 * useToast - Toast notification hook
 *
 * Provides methods to show toast notifications for user feedback.
 * Uses a global toast manager to display messages.
 *
 * @example
 * const toast = useToast();
 *
 * const handleSave = async () => {
 *   try {
 *     await saveData();
 *     toast.success('Dati salvati con successo!');
 *   } catch (err) {
 *     toast.error('Errore durante il salvataggio');
 *   }
 * };
 */

import { useCallback } from 'react';

// Global toast state (simple implementation)
let toastListeners = [];
let toastId = 0;

/**
 * Show a toast notification
 */
function showToast({ type, message, duration = 4000, action }) {
  const id = ++toastId;
  const toast = { id, type, message, duration, action };

  toastListeners.forEach((listener) => listener(toast));

  // Auto-dismiss after duration
  if (duration > 0) {
    setTimeout(() => {
      dismissToast(id);
    }, duration);
  }

  return id;
}

/**
 * Dismiss a toast by ID
 */
function dismissToast(id) {
  toastListeners.forEach((listener) => listener({ id, dismissed: true }));
}

/**
 * Subscribe to toast events
 */
export function subscribeToToasts(listener) {
  toastListeners.push(listener);
  return () => {
    toastListeners = toastListeners.filter((l) => l !== listener);
  };
}

/**
 * useToast hook
 */
export function useToast() {
  const success = useCallback((message, options = {}) => {
    return showToast({ type: 'success', message, ...options });
  }, []);

  const error = useCallback((message, options = {}) => {
    return showToast({ type: 'error', message, duration: 6000, ...options });
  }, []);

  const info = useCallback((message, options = {}) => {
    return showToast({ type: 'info', message, ...options });
  }, []);

  const warning = useCallback((message, options = {}) => {
    return showToast({ type: 'warning', message, ...options });
  }, []);

  const dismiss = useCallback((id) => {
    dismissToast(id);
  }, []);

  return {
    success,
    error,
    info,
    warning,
    dismiss,
  };
}

export default useToast;
