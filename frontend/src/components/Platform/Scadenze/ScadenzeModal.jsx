/**
 * ScadenzeModal Component - Universal Modal for Scadenza Management
 *
 * Modes:
 * - create: Create new scadenza (TODO or entity-linked)
 * - edit: Edit existing scadenza
 * - view: View scadenza details with audit log
 *
 * Features:
 * - Form validation
 * - TODO vs Entity-linked toggle
 * - Multi-recipient support
 * - Audit log display
 * - Quick actions (save, delete, complete, postpone)
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { renderIcon } from '../../Navigation/iconRegistry.jsx';
import { useScadenze } from './hooks/useScadenze';
import './ScadenzeModal.css';

const ScadenzeModal = ({
  isOpen,
  onClose,
  mode = 'create', // 'create', 'edit', 'view'
  scadenza = null,
  entity = null, // { modulo, entityType, entityId }
  onSaved = null,
}) => {
  const navigate = useNavigate();
  const {
    createScadenza,
    createTodo,
    updateScadenza,
    deleteScadenza,
    completaScadenza,
    posticipaScadenza,
    loadLogs,
  } = useScadenze({ autoLoad: false });

  const [formData, setFormData] = useState({
    titolo: '',
    descrizione: '',
    data_scadenza: '',
    priorita: 'MEDIA',
    modulo: '',
    entity_type: '',
    entity_id: '',
    is_todo: true,
    destinatari_ids: [],
  });

  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [validationErrors, setValidationErrors] = useState({});

  // Initialize form data
  useEffect(() => {
    if (mode === 'edit' || mode === 'view') {
      if (scadenza) {
        setFormData({
          titolo: scadenza.titolo || '',
          descrizione: scadenza.descrizione || '',
          data_scadenza: scadenza.data_scadenza || '',
          priorita: scadenza.priorita || 'MEDIA',
          modulo: scadenza.modulo || '',
          entity_type: scadenza.entity_type || '',
          entity_id: scadenza.entity_id || '',
          is_todo: scadenza.is_todo || false,
          destinatari_ids: scadenza.destinatari?.map(d => d.user_id) || [],
        });

        // Load audit logs for view/edit mode
        if (scadenza.id) {
          loadLogs(scadenza.id).then(setLogs).catch(console.error);
        }
      }
    } else if (mode === 'create' && entity) {
      // Pre-fill entity info if provided
      setFormData(prev => ({
        ...prev,
        modulo: entity.modulo,
        entity_type: entity.entityType,
        entity_id: entity.entityId,
        is_todo: false,
      }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, scadenza, entity?.modulo, entity?.entityType, entity?.entityId]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // Clear validation error for this field
    if (validationErrors[name]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const validateForm = () => {
    const errors = {};

    if (!formData.titolo.trim()) {
      errors.titolo = 'Il titolo è obbligatorio';
    }

    if (!formData.data_scadenza) {
      errors.data_scadenza = 'La data di scadenza è obbligatoria';
    }

    if (!formData.is_todo) {
      if (!formData.modulo) errors.modulo = 'Il modulo è obbligatorio';
      if (!formData.entity_type) errors.entity_type = 'Il tipo entità è obbligatorio';
      if (!formData.entity_id) errors.entity_id = 'L\'ID entità è obbligatorio';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (mode === 'create') {
        if (formData.is_todo) {
          await createTodo({
            titolo: formData.titolo,
            descrizione: formData.descrizione,
            data_scadenza: formData.data_scadenza,
            priorita: formData.priorita,
            destinatari_ids: formData.destinatari_ids,
          });
        } else {
          await createScadenza({
            modulo: formData.modulo,
            entity_type: formData.entity_type,
            entity_id: parseInt(formData.entity_id),
            titolo: formData.titolo,
            descrizione: formData.descrizione,
            data_scadenza: formData.data_scadenza,
            priorita: formData.priorita,
            destinatari_ids: formData.destinatari_ids,
          });
        }
      } else if (mode === 'edit') {
        await updateScadenza(scadenza.id, {
          titolo: formData.titolo,
          descrizione: formData.descrizione,
          data_scadenza: formData.data_scadenza,
          priorita: formData.priorita,
        });
      }

      if (onSaved) onSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore nel salvataggio');
      console.error('Error saving scadenza:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!scadenza?.id) return;
    if (!window.confirm('Vuoi cancellare questa scadenza?')) return;

    setLoading(true);
    try {
      await deleteScadenza(scadenza.id);
      if (onSaved) onSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore nella cancellazione');
    } finally {
      setLoading(false);
    }
  };

  const handleCompleta = async () => {
    if (!scadenza?.id) return;
    if (!window.confirm('Vuoi completare questa scadenza?')) return;

    setLoading(true);
    try {
      await completaScadenza(scadenza.id, 'Completato da modal');
      if (onSaved) onSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore nel completamento');
    } finally {
      setLoading(false);
    }
  };

  const handlePosticipa = async () => {
    if (!scadenza?.id) return;
    const nuovaData = prompt('Nuova data (YYYY-MM-DD):', formData.data_scadenza);
    if (!nuovaData) return;

    setLoading(true);
    try {
      await posticipaScadenza(scadenza.id, nuovaData, 'Posticipato da modal');
      if (onSaved) onSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore nel posticipo');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const isReadOnly = mode === 'view';
  const canEdit = mode === 'edit' && scadenza?.stato !== 'COMPLETATA' && scadenza?.stato !== 'CANCELLATA';
  const canTransition = (mode === 'view' || mode === 'edit') &&
                        scadenza?.stato !== 'COMPLETATA' &&
                        scadenza?.stato !== 'CANCELLATA';

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
        return renderIcon('alert-triangle', { size: 14, className: 'scadenza-icon scadenza-icon--high' });
      case 'MEDIA':
        return renderIcon('calendar-check', { size: 14, className: 'scadenza-icon scadenza-icon--medium' });
      case 'BASSA':
        return renderIcon('leaf', { size: 14, className: 'scadenza-icon scadenza-icon--low' });
      default:
        return renderIcon('info', { size: 14, className: 'scadenza-icon scadenza-icon--default' });
    }
  };

  const getEntityLink = (scadenzaItem) => {
    if (!scadenzaItem?.modulo || !scadenzaItem?.entity_type || !scadenzaItem?.entity_id) return null;
    const params = new URLSearchParams({
      modulo: scadenzaItem.modulo,
      entity_type: scadenzaItem.entity_type,
      entity_id: String(scadenzaItem.entity_id),
      scadenza_id: String(scadenzaItem.id),
    });
    return `/scadenze/resolve?${params.toString()}`;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container modal-container--large" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <h2 className="modal-title">
            {mode === 'create' && (
              <>
                {renderIcon('plus', { size: 18, className: 'scadenza-icon' })}
                Nuova Scadenza
              </>
            )}
            {mode === 'edit' && (
              <>
                {renderIcon('pencil', { size: 18, className: 'scadenza-icon' })}
                Modifica Scadenza
              </>
            )}
            {mode === 'view' && (
              <>
                {renderIcon('info', { size: 18, className: 'scadenza-icon' })}
                Dettagli Scadenza
              </>
            )}
          </h2>
          <button className="modal-close" onClick={onClose}>✖</button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {error && (
            <div className="modal-error">❌ {error}</div>
          )}

          {/* Status badge for view/edit mode */}
          {scadenza && (
            <div className="scadenza-status-bar">
              <div className="status-item">
                <span className="status-label">Stato:</span>
                <span
                  className="status-value"
                  style={{ color: getStatoColor(scadenza.stato) }}
                >
                  {scadenza.stato}
                </span>
              </div>
              <div className="status-item">
                <span className="status-label">Priorità:</span>
                <span className="status-value">
                  {getPrioritaIcon(scadenza.priorita)} {scadenza.priorita}
                </span>
              </div>
              {mode === 'view' && getEntityLink(scadenza) && (
                <button
                  className="btn btn-secondary"
                  type="button"
                  onClick={() => {
                    navigate(getEntityLink(scadenza));
                    onClose();
                  }}
                >
                  Apri scheda
                </button>
              )}
              {scadenza.is_todo && (
                <span className="status-badge">TODO</span>
              )}
              {scadenza.is_scaduta && (
                <span className="status-badge status-badge--danger">SCADUTA</span>
              )}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="scadenza-form">
            {/* TODO toggle (only in create mode) */}
            {mode === 'create' && !entity && (
              <div className="form-group form-group--checkbox">
                <label>
                  <input
                    type="checkbox"
                    name="is_todo"
                    checked={formData.is_todo}
                    onChange={handleInputChange}
                    disabled={isReadOnly}
                  />
                  {' '}Standalone TODO (non collegata a entità)
                </label>
              </div>
            )}

            {/* Entity fields (only for entity-linked scadenze) */}
            {!formData.is_todo && (
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="modulo">
                    Modulo: *
                    {validationErrors.modulo && <span className="error-text">{validationErrors.modulo}</span>}
                  </label>
                  <input
                    type="text"
                    id="modulo"
                    name="modulo"
                    value={formData.modulo}
                    onChange={handleInputChange}
                    disabled={isReadOnly || mode === 'edit'}
                    placeholder="es: affitti_lungo"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="entity_type">
                    Entity Type: *
                    {validationErrors.entity_type && <span className="error-text">{validationErrors.entity_type}</span>}
                  </label>
                  <input
                    type="text"
                    id="entity_type"
                    name="entity_type"
                    value={formData.entity_type}
                    onChange={handleInputChange}
                    disabled={isReadOnly || mode === 'edit'}
                    placeholder="es: contratto"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="entity_id">
                    Entity ID: *
                    {validationErrors.entity_id && <span className="error-text">{validationErrors.entity_id}</span>}
                  </label>
                  <input
                    type="number"
                    id="entity_id"
                    name="entity_id"
                    value={formData.entity_id}
                    onChange={handleInputChange}
                    disabled={isReadOnly || mode === 'edit'}
                    placeholder="es: 1"
                  />
                </div>
              </div>
            )}

            {/* Main fields */}
            <div className="form-group">
              <label htmlFor="titolo">
                Titolo: *
                {validationErrors.titolo && <span className="error-text">{validationErrors.titolo}</span>}
              </label>
              <input
                type="text"
                id="titolo"
                name="titolo"
                value={formData.titolo}
                onChange={handleInputChange}
                disabled={isReadOnly}
                placeholder="Breve descrizione della scadenza"
                maxLength={200}
              />
            </div>

            <div className="form-group">
              <label htmlFor="descrizione">Descrizione:</label>
              <textarea
                id="descrizione"
                name="descrizione"
                value={formData.descrizione}
                onChange={handleInputChange}
                disabled={isReadOnly}
                placeholder="Note dettagliate (opzionale)"
                rows="4"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="data_scadenza">
                  Data Scadenza: *
                  {validationErrors.data_scadenza && <span className="error-text">{validationErrors.data_scadenza}</span>}
                </label>
                <input
                  type="date"
                  id="data_scadenza"
                  name="data_scadenza"
                  value={formData.data_scadenza}
                  onChange={handleInputChange}
                  disabled={isReadOnly}
                />
              </div>

              <div className="form-group">
                <label htmlFor="priorita">Priorità:</label>
                <select
                  id="priorita"
                  name="priorita"
                  value={formData.priorita}
                  onChange={handleInputChange}
                  disabled={isReadOnly}
                >
                  <option value="BASSA">🟢 Bassa</option>
                  <option value="MEDIA">🟡 Media</option>
                  <option value="ALTA">🔴 Alta</option>
                </select>
              </div>
            </div>

            {/* Metadata (view mode only) */}
            {mode === 'view' && scadenza && (
              <div className="scadenza-metadata">
                {getEntityLink(scadenza) && (
                  <div className="metadata-row">
                    <span className="metadata-label">Collegamento:</span>
                    <button
                      type="button"
                      className="btn btn-secondary scadenza-btn"
                      onClick={() => {
                        navigate(getEntityLink(scadenza));
                        onClose();
                      }}
                    >
                      {renderIcon('link', { size: 16, className: 'scadenza-btn__icon' })}
                      Apri scheda
                    </button>
                  </div>
                )}
                <div className="metadata-row">
                  <span className="metadata-label">Creato da:</span>
                  <span className="metadata-value">{scadenza.created_by_username || 'N/A'}</span>
                </div>
                <div className="metadata-row">
                  <span className="metadata-label">Creato il:</span>
                  <span className="metadata-value">{new Date(scadenza.created_at).toLocaleString('it-IT')}</span>
                </div>
                {scadenza.updated_at && (
                  <div className="metadata-row">
                    <span className="metadata-label">Ultimo aggiornamento:</span>
                    <span className="metadata-value">{new Date(scadenza.updated_at).toLocaleString('it-IT')}</span>
                  </div>
                )}
                {scadenza.completed_at && (
                  <div className="metadata-row">
                    <span className="metadata-label">Completato il:</span>
                    <span className="metadata-value">{new Date(scadenza.completed_at).toLocaleString('it-IT')}</span>
                  </div>
                )}
              </div>
            )}

            {/* Audit logs (view mode only) */}
            {mode === 'view' && logs.length > 0 && (
              <div className="scadenza-logs">
                <h3 className="scadenza-logs__title">
                  {renderIcon('list', { size: 16, className: 'scadenza-icon' })}
                  Storico Modifiche
                </h3>
                <div className="logs-list">
                  {logs.map((log, index) => (
                    <div key={index} className="log-entry">
                      <div className="log-header">
                        <span className="log-azione">{log.azione}</span>
                        <span className="log-date">{new Date(log.created_at).toLocaleString('it-IT')}</span>
                      </div>
                      <div className="log-user">
                        {renderIcon('user', { size: 14, className: 'scadenza-icon' })}
                        {log.username || 'Sistema'}
                      </div>
                      {log.note && (
                        <div className="log-note">
                          {renderIcon('info', { size: 14, className: 'scadenza-icon' })}
                          {log.note}
                        </div>
                      )}
                      {log.data_vecchia && (
                        <div className="log-data">
                          {renderIcon('calendar', { size: 14, className: 'scadenza-icon' })}
                          {log.data_vecchia} → {log.data_nuova}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="modal-actions">
              {/* Left actions (destructive) */}
              <div className="modal-actions-left">
                {(mode === 'edit' || mode === 'view') && (
                  <button
                    type="button"
                    onClick={handleDelete}
                    className="btn btn-danger scadenza-btn"
                    disabled={loading}
                  >
                    {renderIcon('trash', { size: 16, className: 'scadenza-btn__icon' })}
                    Cancella
                  </button>
                )}
              </div>

              {/* Right actions (primary) */}
              <div className="modal-actions-right">
                {canTransition && (
                  <>
                    <button
                      type="button"
                      onClick={handleCompleta}
                      className="btn btn-success scadenza-btn"
                      disabled={loading}
                    >
                      {renderIcon('check-circle', { size: 16, className: 'scadenza-btn__icon' })}
                      Completa
                    </button>
                    <button
                      type="button"
                      onClick={handlePosticipa}
                      className="btn btn-warning scadenza-btn"
                      disabled={loading}
                    >
                      {renderIcon('calendar', { size: 16, className: 'scadenza-btn__icon' })}
                      Posticipa
                    </button>
                  </>
                )}

                {mode !== 'view' && (
                  <button
                    type="submit"
                    className="btn btn-primary scadenza-btn"
                    disabled={loading || isReadOnly}
                  >
                    {loading
                      ? 'Salvataggio...'
                      : (
                        <>
                          {renderIcon('save', { size: 16, className: 'scadenza-btn__icon' })}
                          Salva
                        </>
                      )}
                  </button>
                )}

                <button
                  type="button"
                  onClick={onClose}
                  className="btn btn-secondary scadenza-btn"
                  disabled={loading}
                >
                  {mode === 'view' ? 'Chiudi' : 'Annulla'}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ScadenzeModal;
