/**
 * ScadenzeWidget Component - Dashboard Widget for Scadenze
 *
 * Displays upcoming and overdue scadenze in a compact format
 * for use in the platform dashboard.
 *
 * Features:
 * - Shows next N scadenze ordered by date
 * - Highlights overdue scadenze
 * - Quick actions (complete, postpone)
 * - Click to open modal
 * - Auto-refresh
 * - Link to full scadenze page
 *
 * Usage:
 *   <ScadenzeWidget maxItems={5} autoRefresh={true} />
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useScadenze } from './hooks/useScadenze';
import ScadenzeModal from './ScadenzeModal';
import './ScadenzeWidget.css';

const ScadenzeWidget = ({
  maxItems = 5,
  autoRefresh = true,
  refreshInterval = 5 * 60 * 1000, // 5 minutes
  showOnlyMyScadenze = true,
  title = 'Scadenze Prossime',
}) => {
  const navigate = useNavigate();

  const {
    scadenze,
    loading,
    error,
    loadMyScadenze,
    loadScadenze,
    completaScadenza,
    posticipаScadenza,
  } = useScadenze({ autoLoad: false });

  const [modalOpen, setModalOpen] = useState(false);
  const [selectedScadenza, setSelectedScadenza] = useState(null);

  // Load scadenze
  useEffect(() => {
    const load = showOnlyMyScadenze ? loadMyScadenze : loadScadenze;
    load(false, false); // includeCompleted=false, onlyOverdue=false

    if (autoRefresh) {
      const interval = setInterval(() => {
        load(false, false);
      }, refreshInterval);

      return () => clearInterval(interval);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showOnlyMyScadenze, autoRefresh, refreshInterval]);

  // Filter and sort scadenze
  const displayScadenze = scadenze
    .filter(s => s.stato !== 'COMPLETATA' && s.stato !== 'CANCELLATA')
    .sort((a, b) => {
      // Overdue first, then by date
      if (a.is_scaduta && !b.is_scaduta) return -1;
      if (!a.is_scaduta && b.is_scaduta) return 1;
      return new Date(a.data_scadenza) - new Date(b.data_scadenza);
    })
    .slice(0, maxItems);

  const overdueCount = displayScadenze.filter(s => s.is_scaduta).length;

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
    const load = showOnlyMyScadenze ? loadMyScadenze : loadScadenze;
    load(false, false);
  };

  const handleCompleta = async (e, scadenza) => {
    e.stopPropagation();
    if (window.confirm('Vuoi completare questa scadenza?')) {
      try {
        await completaScadenza(scadenza.id, 'Completato da widget dashboard');
        handleScadenzaSaved();
      } catch (err) {
        console.error('Error completing scadenza:', err);
      }
    }
  };

  const handlePosticipa = async (e, scadenza) => {
    e.stopPropagation();
    const nuovaData = prompt('Nuova data (YYYY-MM-DD):', scadenza.data_scadenza);
    if (nuovaData) {
      try {
        await posticipаScadenza(scadenza.id, nuovaData, 'Posticipato da widget dashboard');
        handleScadenzaSaved();
      } catch (err) {
        console.error('Error postponing scadenza:', err);
      }
    }
  };

  const handleViewAll = () => {
    navigate('/test/scadenze');
  };

  const handleCreateNew = () => {
    setSelectedScadenza(null);
    setModalOpen(true);
  };

  // Rendering helpers
  const getPrioritaIcon = (priorita) => {
    switch (priorita) {
      case 'ALTA': return '🔴';
      case 'MEDIA': return '🟡';
      case 'BASSA': return '🟢';
      default: return '⚪';
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const dateOnly = date.toISOString().split('T')[0];
    const todayOnly = today.toISOString().split('T')[0];
    const tomorrowOnly = tomorrow.toISOString().split('T')[0];

    if (dateOnly === todayOnly) return 'Oggi';
    if (dateOnly === tomorrowOnly) return 'Domani';

    return date.toLocaleDateString('it-IT', { day: 'numeric', month: 'short' });
  };

  return (
    <div className="scadenze-widget">
      {/* Header */}
      <div className="scadenze-widget__header">
        <h3 className="scadenze-widget__title">
          {title}
          {overdueCount > 0 && (
            <span className="overdue-badge">{overdueCount}</span>
          )}
        </h3>
        <button
          className="btn-widget-action"
          onClick={handleCreateNew}
          title="Nuova Scadenza"
        >
          ➕
        </button>
      </div>

      {/* Body */}
      <div className="scadenze-widget__body">
        {loading && (
          <div className="widget-loading">⏳ Caricamento...</div>
        )}

        {error && (
          <div className="widget-error">❌ {error}</div>
        )}

        {!loading && displayScadenze.length === 0 && (
          <div className="widget-empty">
            ✅ Nessuna scadenza in arrivo!
          </div>
        )}

        {!loading && displayScadenze.length > 0 && (
          <div className="widget-scadenze-list">
            {displayScadenze.map((scadenza) => (
              <div
                key={scadenza.id}
                className={`widget-scadenza-item ${
                  scadenza.is_scaduta ? 'widget-scadenza-item--overdue' : ''
                }`}
                onClick={() => handleScadenzaClick(scadenza)}
              >
                <div className="widget-scadenza-item__left">
                  <span className="widget-scadenza-item__icon">
                    {getPrioritaIcon(scadenza.priorita)}
                  </span>
                  <div className="widget-scadenza-item__content">
                    <div className="widget-scadenza-item__title">
                      {scadenza.titolo}
                    </div>
                    <div className="widget-scadenza-item__date">
                      📅 {formatDate(scadenza.data_scadenza)}
                      {!scadenza.is_todo && (
                        <span className="widget-scadenza-item__entity">
                          {' '}· {scadenza.modulo}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="widget-scadenza-item__actions">
                  <button
                    className="btn-widget-quick"
                    onClick={(e) => handleCompleta(e, scadenza)}
                    title="Completa"
                  >
                    ✅
                  </button>
                  <button
                    className="btn-widget-quick"
                    onClick={(e) => handlePosticipa(e, scadenza)}
                    title="Posticipa"
                  >
                    ⏭️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {!loading && displayScadenze.length > 0 && (
        <div className="scadenze-widget__footer">
          <button
            className="btn-view-all"
            onClick={handleViewAll}
          >
            Vedi tutte le scadenze →
          </button>
        </div>
      )}

      {/* Modal */}
      {modalOpen && (
        <ScadenzeModal
          isOpen={modalOpen}
          onClose={handleModalClose}
          mode={selectedScadenza ? 'view' : 'create'}
          scadenza={selectedScadenza}
          onSaved={handleScadenzaSaved}
        />
      )}
    </div>
  );
};

export default ScadenzeWidget;
