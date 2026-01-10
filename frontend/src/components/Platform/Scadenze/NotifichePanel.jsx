/**
 * NotifichePanel Component - In-App Notifications Panel
 *
 * Displays scadenze as in-app notifications in a dropdown panel.
 * Shows overdue and upcoming scadenze with priority.
 *
 * Features:
 * - Dropdown panel from TopBar
 * - Grouped by: overdue, today, tomorrow, this week
 * - Quick actions (complete, postpone)
 * - Click to view full scadenza
 * - Badge count indicator
 * - Auto-refresh
 * - Mark all as read
 *
 * Usage:
 *   <NotifichePanel isOpen={isOpen} onClose={onClose} />
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useScadenze } from './hooks/useScadenze';
import ScadenzeModal from './ScadenzeModal';
import './NotifichePanel.css';

const NotifichePanel = ({
  isOpen,
  onClose,
  autoRefresh = true,
  refreshInterval = 2 * 60 * 1000, // 2 minutes
}) => {
  const navigate = useNavigate();

  const {
    scadenze,
    loading,
    loadMyScadenze,
    completaScadenza,
    posticipaScadenza,
  } = useScadenze({ autoLoad: false });

  const [modalOpen, setModalOpen] = useState(false);
  const [selectedScadenza, setSelectedScadenza] = useState(null);

  // Load scadenze
  useEffect(() => {
    if (isOpen) {
      loadMyScadenze(false, false); // includeCompleted=false, onlyOverdue=false
    }

    if (autoRefresh && isOpen) {
      const interval = setInterval(() => {
        loadMyScadenze(false, false);
      }, refreshInterval);

      return () => clearInterval(interval);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, autoRefresh, refreshInterval]);

  // Group scadenze by time
  const groupScadenze = () => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const nextWeek = new Date(today);
    nextWeek.setDate(nextWeek.getDate() + 7);

    const groups = {
      overdue: [],
      today: [],
      tomorrow: [],
      thisWeek: [],
      later: [],
    };

    scadenze
      .filter(s => s.stato !== 'COMPLETATA' && s.stato !== 'CANCELLATA')
      .forEach(scadenza => {
        const scadenzaDate = new Date(scadenza.data_scadenza);
        scadenzaDate.setHours(0, 0, 0, 0);

        if (scadenza.is_scaduta) {
          groups.overdue.push(scadenza);
        } else if (scadenzaDate.getTime() === today.getTime()) {
          groups.today.push(scadenza);
        } else if (scadenzaDate.getTime() === tomorrow.getTime()) {
          groups.tomorrow.push(scadenza);
        } else if (scadenzaDate < nextWeek) {
          groups.thisWeek.push(scadenza);
        } else {
          groups.later.push(scadenza);
        }
      });

    return groups;
  };

  const groups = groupScadenze();
  const totalCount = Object.values(groups).flat().length;

  // Handlers
  const handleScadenzaClick = (scadenza) => {
    setSelectedScadenza(scadenza);
    setModalOpen(true);
  };

  const handleModalClose = () => {
    setModalOpen(false);
    setSelectedScadenza(null);
  };

  const handleScadenzaSaved = () => {
    loadMyScadenze(false, false);
  };

  const handleCompleta = async (e, scadenza) => {
    e.stopPropagation();
    try {
      await completaScadenza(scadenza.id, 'Completato da notifiche');
      handleScadenzaSaved();
    } catch (err) {
      console.error('Error completing scadenza:', err);
    }
  };

  const handlePosticipa = async (e, scadenza) => {
    e.stopPropagation();
    const nuovaData = prompt('Nuova data (YYYY-MM-DD):', scadenza.data_scadenza);
    if (nuovaData) {
      try {
        await posticipaScadenza(scadenza.id, nuovaData, 'Posticipato da notifiche');
        handleScadenzaSaved();
      } catch (err) {
        console.error('Error postponing scadenza:', err);
      }
    }
  };

  const handleViewAll = () => {
    navigate('/test/scadenze');
    onClose();
  };

  const getPrioritaIcon = (priorita) => {
    switch (priorita) {
      case 'ALTA': return '🔴';
      case 'MEDIA': return '🟡';
      case 'BASSA': return '🟢';
      default: return '⚪';
    }
  };

  const renderGroup = (title, items, icon) => {
    if (items.length === 0) return null;

    return (
      <div className="notifiche-group">
        <div className="notifiche-group__header">
          <span className="notifiche-group__icon">{icon}</span>
          <span className="notifiche-group__title">{title}</span>
          <span className="notifiche-group__count">({items.length})</span>
        </div>
        <div className="notifiche-group__items">
          {items.map((scadenza) => (
            <div
              key={scadenza.id}
              className="notifica-item"
              onClick={() => handleScadenzaClick(scadenza)}
            >
              <div className="notifica-item__icon">
                {getPrioritaIcon(scadenza.priorita)}
              </div>
              <div className="notifica-item__content">
                <div className="notifica-item__title">{scadenza.titolo}</div>
                <div className="notifica-item__meta">
                  {scadenza.data_scadenza}
                  {!scadenza.is_todo && (
                    <span className="notifica-item__entity">
                      {' '}· {scadenza.modulo}
                    </span>
                  )}
                </div>
              </div>
              <div className="notifica-item__actions">
                <button
                  className="btn-notifica-quick"
                  onClick={(e) => handleCompleta(e, scadenza)}
                  title="Completa"
                >
                  ✅
                </button>
                <button
                  className="btn-notifica-quick"
                  onClick={(e) => handlePosticipa(e, scadenza)}
                  title="Posticipa"
                >
                  ⏭️
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div className="notifiche-overlay" onClick={onClose} />

      {/* Panel */}
      <div className="notifiche-panel">
        {/* Header */}
        <div className="notifiche-panel__header">
          <h3 className="notifiche-panel__title">🔔 Notifiche</h3>
          <button className="notifiche-panel__close" onClick={onClose}>✖</button>
        </div>

        {/* Body */}
        <div className="notifiche-panel__body">
          {loading && (
            <div className="notifiche-loading">⏳ Caricamento...</div>
          )}

          {!loading && totalCount === 0 && (
            <div className="notifiche-empty">
              ✅ Nessuna notifica!<br/>
              <span>Tutte le scadenze sono gestite.</span>
            </div>
          )}

          {!loading && totalCount > 0 && (
            <>
              {renderGroup('Scadute', groups.overdue, '🔴')}
              {renderGroup('Oggi', groups.today, '📅')}
              {renderGroup('Domani', groups.tomorrow, '➡️')}
              {renderGroup('Questa Settimana', groups.thisWeek, '📆')}
              {renderGroup('Successivi', groups.later, '⏰')}
            </>
          )}
        </div>

        {/* Footer */}
        {!loading && totalCount > 0 && (
          <div className="notifiche-panel__footer">
            <button className="btn-notifiche-view-all" onClick={handleViewAll}>
              Vedi tutte le scadenze →
            </button>
          </div>
        )}
      </div>

      {/* Modal */}
      {modalOpen && (
        <ScadenzeModal
          isOpen={modalOpen}
          onClose={handleModalClose}
          mode="view"
          scadenza={selectedScadenza}
          onSaved={handleScadenzaSaved}
        />
      )}
    </>
  );
};

export default NotifichePanel;
