/**
 * EmptyState - Display when no data is available
 */

import React from 'react';
import './common.css';

/**
 * EmptyState component
 *
 * @param {Object} props
 * @param {string} props.icon - Icon to display
 * @param {string} props.title - Title message
 * @param {string} props.message - Description message
 * @param {React.ReactNode} props.action - Action button or element
 * @param {string} props.variant - Variant: 'default' | 'compact' (default: 'default')
 */
export function EmptyState({
  icon,
  title = 'Nessun dato trovato',
  message,
  action,
  variant = 'default',
}) {
  return (
    <div className={`core-empty-state core-empty-state--${variant}`}>
      {icon && (
        <div className="core-empty-state__icon">
          {typeof icon === 'string' ? icon : icon}
        </div>
      )}
      <h3 className="core-empty-state__title">{title}</h3>
      {message && (
        <p className="core-empty-state__message">{message}</p>
      )}
      {action && (
        <div className="core-empty-state__action">
          {action}
        </div>
      )}
    </div>
  );
}

export default EmptyState;
