/**
 * ScadenzeSection Component - Reusable Section for Entity Detail Pages
 *
 * Displays scadenze related to a specific entity (contratto, immobile, etc.)
 * Can be easily integrated into any module's detail page.
 *
 * Features:
 * - Auto-load scadenze for specific entity
 * - Collapsible section
 * - Create new scadenza linked to entity
 * - View/edit existing scadenze via modal
 * - Visual indicator for overdue scadenze
 * - Compact list view
 *
 * Usage:
 *   <ScadenzeSection
 *     modulo="affitti_lungo"
 *     entityType="contratto"
 *     entityId={contractId}
 *     title="Scadenze Contratto"
 *   />
 */
import React, { useState, useEffect } from 'react';
import { useScadenze } from './hooks/useScadenze';
import ScadenzeModal from './ScadenzeModal';
import './ScadenzeSection.css';

const ScadenzeSection = ({
  modulo,
  entityType,
  entityId,
  title = 'Scadenze',
  initialCollapsed = false,
  showCreateButton = true,
  showCompletedByDefault = false,
}) => {
  const entity = { modulo, entityType, entityId };

  const {
    scadenze,
    loading,
    error,
    loadScadenzeByEntity,
  } = useScadenze({ autoLoad: false });

  const [isCollapsed, setIsCollapsed] = useState(initialCollapsed);
  const [showCompleted, setShowCompleted] = useState(showCompletedByDefault);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('create');
  const [selectedScadenza, setSelectedScadenza] = useState(null);

  // Load scadenze for this entity
  useEffect(() => {
    if (modulo && entityType && entityId) {
      loadScadenzeByEntity(modulo, entityType, entityId, showCompleted);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modulo, entityType, entityId, showCompleted]);

  // Handlers
  const handleCreateClick = () => {
    setModalMode('create');
    setSelectedScadenza(null);
    setModalOpen(true);
  };

  const handleScadenzaClick = (scadenza) => {
    setModalMode('view');
    setSelectedScadenza(scadenza);
    setModalOpen(true);
  };

  const handleModalClose = () => {
    setModalOpen(false);
    setSelectedScadenza(null);
  };

  const handleScadenzaSaved = () => {
    // Reload scadenze after save
    loadScadenzeByEntity(modulo, entityType, entityId, showCompleted);
  };

  // Filter active scadenze
  const activeScadenze = scadenze.filter(s =>
    s.stato !== 'COMPLETATA' && s.stato !== 'CANCELLATA'
  );

  const overdueCount = activeScadenze.filter(s => s.is_scaduta).length;
  const highPriorityCount = activeScadenze.filter(s => s.priorita === 'ALTA').length;

  // Rendering helpers
  const getStatoColor = (stato) => {
    switch (stato) {
      case 'ATTIVA': return 'green';
      case 'SCADUTA': return 'red';
      case 'COMPLETATA': return 'gray';
      case 'POSTICIPATA': return 'orange';
      case 'CANCELLATA': return 'darkgray';
      default: return 'black';
    }
  };

  const getPrioritaIcon = (priorita) => {
    switch (priorita) {
      case 'ALTA': return '🔴';
      case 'MEDIA': return '🟡';
      case 'BASSA': return '🟢';
      default: return '⚪';
    }
  };

  const displayScadenze = showCompleted ? scadenze : activeScadenze;

  return (
    <div className="scadenze-section">
      {/* Header */}
      <div className="scadenze-section__header" onClick={() => setIsCollapsed(!isCollapsed)}>
        <div className="scadenze-section__title">
          <button className="collapse-btn" type="button">
            {isCollapsed ? '▶' : '▼'}
          </button>
          <h3>{title}</h3>
          <span className="scadenze-count">({displayScadenze.length})</span>

          {/* Warning badges */}
          {overdueCount > 0 && (
            <span className="warning-badge warning-badge--danger" title="Scadenze scadute">
              ⚠️ {overdueCount}
            </span>
          )}
          {highPriorityCount > 0 && (
            <span className="warning-badge warning-badge--warning" title="Alta priorità">
              🔴 {highPriorityCount}
            </span>
          )}
        </div>

        <div className="scadenze-section__actions" onClick={(e) => e.stopPropagation()}>
          {showCreateButton && (
            <button
              className="btn-create"
              onClick={handleCreateClick}
              type="button"
            >
              ➕ Nuova Scadenza
            </button>
          )}
        </div>
      </div>

      {/* Body */}
      {!isCollapsed && (
        <div className="scadenze-section__body">
          {/* Toggle for completed */}
          <div className="scadenze-section__filters">
            <label className="filter-checkbox">
              <input
                type="checkbox"
                checked={showCompleted}
                onChange={(e) => setShowCompleted(e.target.checked)}
              />
              {' '}Mostra completate
            </label>
          </div>

          {/* Loading / Error */}
          {loading && (
            <div className="scadenze-section__loading">⏳ Caricamento...</div>
          )}

          {error && (
            <div className="scadenze-section__error">❌ {error}</div>
          )}

          {/* Empty state */}
          {!loading && displayScadenze.length === 0 && (
            <div className="scadenze-section__empty">
              Nessuna scadenza per questa entità.
            </div>
          )}

          {/* Scadenze list */}
          {!loading && displayScadenze.length > 0 && (
            <div className="scadenze-section__list">
              {displayScadenze.map((scadenza) => (
                <div
                  key={scadenza.id}
                  className={`scadenza-item-compact ${
                    scadenza.is_scaduta ? 'scadenza-item-compact--overdue' : ''
                  }`}
                  onClick={() => handleScadenzaClick(scadenza)}
                >
                  <div className="scadenza-item-compact__icon">
                    {getPrioritaIcon(scadenza.priorita)}
                  </div>

                  <div className="scadenza-item-compact__content">
                    <div className="scadenza-item-compact__header">
                      <span className="scadenza-item-compact__title">
                        {scadenza.titolo}
                      </span>
                      <span
                        className="scadenza-item-compact__stato"
                        style={{ color: getStatoColor(scadenza.stato) }}
                      >
                        {scadenza.stato}
                      </span>
                    </div>
                    <div className="scadenza-item-compact__meta">
                      <span className="scadenza-item-compact__date">
                        📅 {scadenza.data_scadenza}
                      </span>
                      {scadenza.descrizione && (
                        <span className="scadenza-item-compact__desc">
                          {scadenza.descrizione.substring(0, 50)}
                          {scadenza.descrizione.length > 50 ? '...' : ''}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="scadenza-item-compact__arrow">›</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Modal */}
      {modalOpen && (
        <ScadenzeModal
          isOpen={modalOpen}
          onClose={handleModalClose}
          mode={modalMode}
          scadenza={selectedScadenza}
          entity={modalMode === 'create' ? entity : null}
          onSaved={handleScadenzaSaved}
        />
      )}
    </div>
  );
};

export default ScadenzeSection;
