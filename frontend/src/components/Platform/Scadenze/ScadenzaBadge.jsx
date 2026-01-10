/**
 * ScadenzaBadge Component
 *
 * Displays a badge with scadenze count and color-coded status.
 * Colors:
 * - Red: Overdue scadenze
 * - Yellow: High priority scadenze
 * - Green: Active scadenze (all good)
 *
 * Usage:
 *   <ScadenzaBadge autoLoad={true} onClick={() => openScadenzeModal()} />
 */
import React, { useEffect } from 'react';
import { useScadenze } from './hooks/useScadenze';
import './ScadenzaBadge.css';

const ScadenzaBadge = ({
  autoLoad = true,
  onClick = null,
  className = '',
  showTooltip = true,
}) => {
  const { badgeInfo, loadBadgeInfo, loading } = useScadenze({ autoLoad: false });

  useEffect(() => {
    if (autoLoad) {
      loadBadgeInfo();

      // Auto-refresh every 5 minutes
      const interval = setInterval(() => {
        loadBadgeInfo();
      }, 5 * 60 * 1000);

      return () => clearInterval(interval);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoLoad]);

  if (loading || !badgeInfo) {
    return (
      <div className={`scadenza-badge scadenza-badge--loading ${className}`}>
        <span className="scadenza-badge__icon">⏱️</span>
        <span className="scadenza-badge__count">-</span>
      </div>
    );
  }

  const { count_attive, count_scadute, count_alta_priorita, color, tooltip } = badgeInfo;
  const totalCount = count_attive + count_scadute;

  if (totalCount === 0) {
    return null; // Don't show badge if no scadenze
  }

  const getIcon = () => {
    if (count_scadute > 0) return '🔴';
    if (count_alta_priorita > 0) return '⚠️';
    return '📅';
  };

  const getBadgeClass = () => {
    return `scadenza-badge scadenza-badge--${color} ${className}`;
  };

  const handleClick = (e) => {
    if (onClick) {
      e.preventDefault();
      onClick();
    }
  };

  return (
    <div
      className={getBadgeClass()}
      onClick={handleClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
      title={showTooltip ? tooltip : ''}
    >
      <span className="scadenza-badge__icon">{getIcon()}</span>
      <span className="scadenza-badge__count">{totalCount}</span>
      {count_scadute > 0 && (
        <span className="scadenza-badge__overdue" title="Scadenze scadute">
          {count_scadute}
        </span>
      )}
    </div>
  );
};

export default ScadenzaBadge;
