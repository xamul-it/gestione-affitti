/**
 * Scadenze Test Page
 *
 * Pagina di test completa per il sistema Scadenzario.
 * Permette di testare tutte le funzionalità: CRUD, badge, filtri, state transitions.
 */
import React, { useState, useEffect } from 'react';
import { useScadenze } from '../components/Platform/Scadenze/hooks/useScadenze';
import ScadenzaBadge from '../components/Platform/Scadenze/ScadenzaBadge';
import { renderIcon } from '../components/Navigation/iconRegistry.jsx';
import ScadenzeModal from '../components/Platform/Scadenze/ScadenzeModal';
import './ScadenzeTestPage.css';

const ScadenzeTestPage = () => {
  const {
    scadenze,
    loading,
    error,
    badgeInfo,
    createScadenza,
    createTodo,
    updateScadenza,
    completaScadenza,
    posticipаScadenza,
    deleteScadenza,
    loadScadenze,
    loadMyScadenze,
    loadBadgeInfo,
  } = useScadenze({ autoLoad: true });

  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    titolo: '',
    descrizione: '',
    data_scadenza: '',
    priorita: 'MEDIA',
    modulo: '',
    entity_type: '',
    entity_id: '',
    isTodo: true,
  });

  const [statistics, setStatistics] = useState(null);
  const [selectedScadenza, setSelectedScadenza] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);

  // Load statistics
  useEffect(() => {
    loadBadgeInfo().then((badge) => {
      if (badge) {
        setStatistics({
          attive: badge.count_attive,
          scadute: badge.count_scadute,
          alta_priorita: badge.count_alta_priorita,
        });
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scadenze.length]); // Only re-run when scadenze count changes

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      if (formData.isTodo) {
        // Create TODO
        await createTodo({
          titolo: formData.titolo,
          descrizione: formData.descrizione,
          data_scadenza: formData.data_scadenza,
          priorita: formData.priorita,
        });
      } else {
        // Create entity-linked scadenza
        await createScadenza({
          modulo: formData.modulo,
          entity_type: formData.entity_type,
          entity_id: parseInt(formData.entity_id),
          titolo: formData.titolo,
          descrizione: formData.descrizione,
          data_scadenza: formData.data_scadenza,
          priorita: formData.priorita,
        });
      }

      // Reset form
      setFormData({
        titolo: '',
        descrizione: '',
        data_scadenza: '',
        priorita: 'MEDIA',
        modulo: '',
        entity_type: '',
        entity_id: '',
        isTodo: true,
      });
      setShowForm(false);
      alert('Scadenza creata con successo!');
    } catch (err) {
      alert(`Errore: ${err.message}`);
    }
  };

  const handleCompleta = async (id) => {
    if (window.confirm('Vuoi completare questa scadenza?')) {
      try {
        await completaScadenza(id, 'Completato da pagina test');
        alert('Scadenza completata!');
      } catch (err) {
        alert(`Errore: ${err.message}`);
      }
    }
  };

  const handlePosticipa = async (id) => {
    const nuovaData = prompt('Nuova data (YYYY-MM-DD):');
    if (nuovaData) {
      try {
        await posticipаScadenza(id, nuovaData, 'Posticipato da pagina test');
        alert('Scadenza posticipata!');
      } catch (err) {
        alert(`Errore: ${err.message}`);
      }
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Vuoi cancellare questa scadenza?')) {
      try {
        await deleteScadenza(id);
        alert('Scadenza cancellata!');
      } catch (err) {
        alert(`Errore: ${err.message}`);
      }
    }
  };

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
      case 'ALTA':
        return renderIcon('alert-triangle', { size: 18, className: 'priority-icon priority-icon--high' });
      case 'MEDIA':
        return renderIcon('calendar', { size: 18, className: 'priority-icon priority-icon--medium' });
      case 'BASSA':
        return renderIcon('leaf', { size: 18, className: 'priority-icon priority-icon--low' });
      default:
        return renderIcon('info', { size: 18, className: 'priority-icon priority-icon--default' });
    }
  };

  const handleScadenzaClick = (scadenza) => {
    setSelectedScadenza(scadenza);
    setModalOpen(true);
  };

  const handleModalClose = () => {
    setModalOpen(false);
    setSelectedScadenza(null);
  };

  return (
    <div className="scadenze-test-page">
      <div className="test-page-header">
        <h1 className="page-title">
          {renderIcon('badge-check', { size: 24, className: 'icon-inline' })}
          Test Scadenzario
        </h1>
        <ScadenzaBadge autoLoad={true} />
      </div>

      {/* Statistics */}
      {statistics && (
        <div className="statistics-panel">
          <h2 className="section-title">
            {renderIcon('chart-line', { size: 20, className: 'icon-inline' })}
            Statistiche
          </h2>
          <div className="stats-grid">
            <div className="stat-card stat-card--green">
              <div className="stat-value">{statistics.attive}</div>
              <div className="stat-label">Attive</div>
            </div>
            <div className="stat-card stat-card--red">
              <div className="stat-value">{statistics.scadute}</div>
              <div className="stat-label">Scadute</div>
            </div>
            <div className="stat-card stat-card--orange">
              <div className="stat-value">{statistics.alta_priorita}</div>
              <div className="stat-label">Alta Priorità</div>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="actions-panel">
        <button
          className="btn btn-primary"
          onClick={() => setShowForm(!showForm)}
        >
          {renderIcon(showForm ? 'info' : 'plus', { size: 16, className: 'icon-inline' })}
          {showForm ? 'Chiudi Form' : 'Nuova Scadenza'}
        </button>
        <button
          className="btn btn-secondary"
          onClick={() => loadScadenze()}
        >
          {renderIcon('list', { size: 16, className: 'icon-inline' })}
          Ricarica
        </button>
        <button
          className="btn btn-secondary"
          onClick={() => loadMyScadenze(false, true)}
        >
          {renderIcon('alert-triangle', { size: 16, className: 'icon-inline' })}
          Solo Scadute
        </button>
        <button
          className="btn btn-secondary"
          onClick={() => loadMyScadenze(true, false)}
        >
          {renderIcon('list', { size: 16, className: 'icon-inline' })}
          Tutte (+ Completate)
        </button>
      </div>

      {/* Create Form */}
      {showForm && (
        <div className="create-form-panel">
          <h2>Crea Nuova Scadenza</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <label>
                <input
                  type="checkbox"
                  name="isTodo"
                  checked={formData.isTodo}
                  onChange={handleInputChange}
                />
                {' '}Standalone TODO (non collegata a entità)
              </label>
            </div>

            {!formData.isTodo && (
              <>
                <div className="form-row">
                  <label>
                    Modulo:
                    <input
                      type="text"
                      name="modulo"
                      value={formData.modulo}
                      onChange={handleInputChange}
                      placeholder="es: affitti_lungo"
                      required={!formData.isTodo}
                    />
                  </label>
                </div>
                <div className="form-row">
                  <label>
                    Entity Type:
                    <input
                      type="text"
                      name="entity_type"
                      value={formData.entity_type}
                      onChange={handleInputChange}
                      placeholder="es: contratto"
                      required={!formData.isTodo}
                    />
                  </label>
                </div>
                <div className="form-row">
                  <label>
                    Entity ID:
                    <input
                      type="number"
                      name="entity_id"
                      value={formData.entity_id}
                      onChange={handleInputChange}
                      placeholder="es: 1"
                      required={!formData.isTodo}
                    />
                  </label>
                </div>
              </>
            )}

            <div className="form-row">
              <label>
                Titolo: *
                <input
                  type="text"
                  name="titolo"
                  value={formData.titolo}
                  onChange={handleInputChange}
                  placeholder="Breve descrizione"
                  required
                />
              </label>
            </div>

            <div className="form-row">
              <label>
                Descrizione:
                <textarea
                  name="descrizione"
                  value={formData.descrizione}
                  onChange={handleInputChange}
                  placeholder="Note dettagliate"
                  rows="3"
                />
              </label>
            </div>

            <div className="form-row">
              <label>
                Data Scadenza: *
                <input
                  type="date"
                  name="data_scadenza"
                  value={formData.data_scadenza}
                  onChange={handleInputChange}
                  required
                />
              </label>
            </div>

            <div className="form-row">
              <label>
                Priorità:
                <select
                  name="priorita"
                  value={formData.priorita}
                  onChange={handleInputChange}
                >
                  <option value="BASSA">Bassa</option>
                  <option value="MEDIA">Media</option>
                  <option value="ALTA">Alta</option>
                </select>
              </label>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn-primary">
                {renderIcon('check-circle', { size: 16, className: 'icon-inline' })}
                Crea Scadenza
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowForm(false)}
              >
                Annulla
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-panel">
          {renderIcon('alert-triangle', { size: 16, className: 'icon-inline' })}
          Errore: {error}
        </div>
      )}

      {/* Scadenze List */}
      <div className="scadenze-list-panel">
        <h2 className="section-title">
          {renderIcon('list', { size: 18, className: 'icon-inline' })}
          Scadenze ({scadenze.length})
        </h2>

        {loading && <div className="loading">Caricamento...</div>}

        {!loading && scadenze.length === 0 && (
          <div className="empty-state">
            Nessuna scadenza trovata. Creane una per iniziare.
          </div>
        )}

        <div className="scadenze-grid">
          {scadenze.map((scadenza) => (
            <div
              key={scadenza.id}
              className={`scadenza-card ${scadenza.is_scaduta ? 'scadenza-card--overdue' : ''}`}
              onClick={() => handleScadenzaClick(scadenza)}
            >
              <div className="scadenza-card__header">
                <span className="scadenza-card__priority">
                  {getPrioritaIcon(scadenza.priorita)}
                </span>
                <span
                  className="scadenza-card__stato"
                  style={{ color: getStatoColor(scadenza.stato) }}
                >
                  {scadenza.stato}
                </span>
                {scadenza.is_todo && (
                  <span className="scadenza-card__badge">TODO</span>
                )}
              </div>

              <h3 className="scadenza-card__title">{scadenza.titolo}</h3>

              {scadenza.descrizione && (
                <p className="scadenza-card__description">
                  {scadenza.descrizione}
                </p>
              )}

              <div className="scadenza-card__meta">
                <div className="meta-row">
                  {renderIcon('calendar', { size: 14, className: 'icon-inline' })}
                  {scadenza.data_scadenza}
                </div>
                {!scadenza.is_todo && (
                  <div className="scadenza-card__entity">
                    {scadenza.modulo}/{scadenza.entity_type}#{scadenza.entity_id}
                  </div>
                )}
              </div>

              {scadenza.stato !== 'COMPLETATA' && scadenza.stato !== 'CANCELLATA' && (
                <div className="scadenza-card__actions">
                  <button
                    className="btn-small btn-success"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCompleta(scadenza.id);
                    }}
                  >
                    {renderIcon('check-circle', { size: 16, className: 'icon-inline' })}
                  </button>
                  <button
                    className="btn-small btn-warning"
                    onClick={(e) => {
                      e.stopPropagation();
                      handlePosticipa(scadenza.id);
                    }}
                  >
                    {renderIcon('calendar', { size: 16, className: 'icon-inline' })}
                  </button>
                  <button
                    className="btn-small btn-danger"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(scadenza.id);
                    }}
                  >
                    {renderIcon('trash', { size: 16, className: 'icon-inline' })}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Selected Scadenza Detail */}
      {modalOpen && (
        <ScadenzeModal
          isOpen={modalOpen}
          onClose={handleModalClose}
          mode="view"
          scadenza={selectedScadenza}
          onSaved={loadScadenze}
        />
      )}
    </div>
  );
};

export default ScadenzeTestPage;
