/**
 * Badge - Status and label badge component
 */

import React from 'react';
import './common.css';

/**
 * Badge component
 *
 * @param {Object} props
 * @param {React.ReactNode} props.children - Badge content
 * @param {string} props.variant - Variant: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info'
 * @param {string} props.size - Size: 'small' | 'medium' | 'large'
 * @param {boolean} props.pill - Pill shape (rounded)
 */
export function Badge({
  children,
  variant = 'default',
  size = 'medium',
  pill = false,
  className = '',
}) {
  return (
    <span
      className={`core-badge core-badge--${variant} core-badge--${size} ${pill ? 'core-badge--pill' : ''} ${className}`}
    >
      {children}
    </span>
  );
}

/**
 * StatusBadge - Badge with predefined status mappings
 *
 * @param {Object} props
 * @param {string} props.status - Status value
 * @param {Object} props.statusMap - Map of status to { label, variant }
 */
export function StatusBadge({ status, statusMap = {} }) {
  const defaultStatusMap = {
    'ATTIVO': { label: 'Attivo', variant: 'success' },
    'INATTIVO': { label: 'Inattivo', variant: 'secondary' },
    'SCADUTO': { label: 'Scaduto', variant: 'danger' },
    'DISDETTO': { label: 'Disdetto', variant: 'warning' },
    'TERMINATO': { label: 'Terminato', variant: 'secondary' },
    'BOZZA': { label: 'Bozza', variant: 'info' },
    'PAGATO': { label: 'Pagato', variant: 'success' },
    'DA_PAGARE': { label: 'Da Pagare', variant: 'warning' },
    'IN_RITARDO': { label: 'In Ritardo', variant: 'danger' },
    true: { label: 'Si', variant: 'success' },
    false: { label: 'No', variant: 'secondary' },
  };

  const mergedMap = { ...defaultStatusMap, ...statusMap };
  const statusConfig = mergedMap[status] || { label: status || '-', variant: 'default' };

  return (
    <Badge variant={statusConfig.variant}>
      {statusConfig.label}
    </Badge>
  );
}

export default Badge;
