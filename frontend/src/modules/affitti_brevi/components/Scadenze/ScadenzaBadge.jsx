import { useState, useEffect } from 'react';
import { scadenzeAPI } from '../../services/affittiBreviAPI';
import './ScadenzaBadge.css';

/**
 * ScadenzaBadge - Notification badge for deadline counts
 *
 * Usage:
 * <ScadenzaBadge /> - Shows total upcoming/overdue count
 * <ScadenzaBadge tipo="COMUNICAZIONE_POLIZIA" /> - Shows count for specific type
 * <ScadenzaBadge detailed /> - Shows breakdown by type
 */
function ScadenzaBadge({ tipo = null, detailed = false, refreshInterval = 300000 }) {
  const [badgeInfo, setBadgeInfo] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchBadgeInfo();

    // Auto-refresh every 5 minutes (or custom interval)
    const interval = setInterval(fetchBadgeInfo, refreshInterval);
    return () => clearInterval(interval);
  }, [tipo, refreshInterval]);

  const fetchBadgeInfo = async () => {
    try {
      const response = await scadenzeAPI.getBadgeInfo();
      setBadgeInfo(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento badge scadenze');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getTotalCount = () => {
    if (tipo) {
      const info = badgeInfo.find(b => b.tipo_scadenza === tipo);
      return info ? info.count : 0;
    }
    return badgeInfo.reduce((sum, b) => sum + b.count, 0);
  };

  const getOverdueCount = () => {
    if (tipo) {
      const info = badgeInfo.find(b => b.tipo_scadenza === tipo);
      return info ? info.overdue_count : 0;
    }
    return badgeInfo.reduce((sum, b) => sum + b.overdue_count, 0);
  };

  const getTipoLabel = (tipoScadenza) => {
    const labels = {
      COMUNICAZIONE_POLIZIA: 'Polizia',
      REPORT_ISTAT: 'ISTAT',
      ALTRO: 'Altro'
    };
    return labels[tipoScadenza] || tipoScadenza;
  };

  const getTipoIcon = (tipoScadenza) => {
    const icons = {
      COMUNICAZIONE_POLIZIA: '👮',
      REPORT_ISTAT: '📊',
      ALTRO: '📋'
    };
    return icons[tipoScadenza] || '📋';
  };

  if (loading) return null; // Don't show anything while loading
  if (error) return null; // Silent fail for badge

  const totalCount = getTotalCount();
  const overdueCount = getOverdueCount();

  // Don't show badge if no deadlines
  if (totalCount === 0) return null;

  // Simple badge (single number)
  if (!detailed) {
    return (
      <span className={`scadenza-badge ${overdueCount > 0 ? 'badge-urgent' : 'badge-warning'}`}>
        {overdueCount > 0 && <span className="badge-urgent-icon">⚠️</span>}
        {totalCount}
      </span>
    );
  }

  // Detailed badge (breakdown by type)
  return (
    <div className="scadenza-badge-detailed">
      {badgeInfo.map((info) => (
        <div
          key={info.tipo_scadenza}
          className={`badge-item ${info.overdue_count > 0 ? 'badge-urgent' : 'badge-info'}`}
          title={`${getTipoLabel(info.tipo_scadenza)}: ${info.count} totali, ${info.overdue_count} scadute`}
        >
          <span className="badge-icon">{getTipoIcon(info.tipo_scadenza)}</span>
          <span className="badge-count">{info.count}</span>
          {info.overdue_count > 0 && (
            <span className="badge-overdue">⚠️{info.overdue_count}</span>
          )}
        </div>
      ))}
    </div>
  );
}

export default ScadenzaBadge;
