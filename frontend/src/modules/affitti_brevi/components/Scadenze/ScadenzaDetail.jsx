import { useState } from 'react';
import './Scadenze.css';

function ScadenzaDetail({ scadenza, onClose, onComplete }) {
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);

  const handleComplete = async () => {
    if (window.confirm('Sei sicuro di voler marcare questa scadenza come completata?')) {
      setLoading(true);
      try {
        await onComplete(scadenza.id, note || null);
        onClose();
      } catch (err) {
        console.error(err);
        alert('Errore nel completamento della scadenza');
      } finally {
        setLoading(false);
      }
    }
  };

  const getTipoLabel = (tipo) => {
    const labels = {
      COMUNICAZIONE_POLIZIA: 'Comunicazione Polizia',
      REPORT_ISTAT: 'Report ISTAT',
      ALTRO: 'Altro'
    };
    return labels[tipo] || tipo;
  };

  const getStatoLabel = (scadenza) => {
    if (scadenza.completata) return 'Completata';

    const dataScadenza = new Date(scadenza.data_scadenza);
    const oggi = new Date();
    const setteDa = new Date();
    setteDa.setDate(oggi.getDate() + 7);

    if (dataScadenza < oggi) return 'Scaduta';
    if (dataScadenza <= setteDa) return 'In Scadenza';
    return 'Da Fare';
  };

  const getStatoBadgeClass = (scadenza) => {
    if (scadenza.completata) return 'badge-success';

    const stato = getStatoLabel(scadenza);
    const classes = {
      'Scaduta': 'badge-danger',
      'In Scadenza': 'badge-warning',
      'Da Fare': 'badge-info'
    };
    return classes[stato] || 'badge-secondary';
  };

  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT');
  };

  const calculateTimeRemaining = () => {
    if (scadenza.completata) return null;

    const dataScadenza = new Date(scadenza.data_scadenza);
    const ora = new Date();
    const diff = dataScadenza - ora;

    if (diff < 0) {
      // Scaduta
      const oreScadute = Math.floor(Math.abs(diff) / (1000 * 60 * 60));
      const giorniScaduti = Math.floor(oreScadute / 24);
      if (giorniScaduti > 0) {
        return `Scaduta da ${giorniScaduti} giorni`;
      }
      return `Scaduta da ${oreScadute} ore`;
    } else {
      // Rimanente
      const oreRimanenti = Math.floor(diff / (1000 * 60 * 60));
      const giorniRimanenti = Math.floor(oreRimanenti / 24);
      if (giorniRimanenti > 0) {
        return `${giorniRimanenti} giorni rimanenti`;
      }
      return `${oreRimanenti} ore rimanenti`;
    }
  };

  const timeRemaining = calculateTimeRemaining();

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content scadenza-detail-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Dettaglio Scadenza</h2>
          <button onClick={onClose} className="close-button">&times;</button>
        </div>

        <div className="modal-body">
          {/* Header Info */}
          <div className="scadenza-header">
            <div className="scadenza-title">
              <h3>{scadenza.titolo}</h3>
              <div className="scadenza-badges">
                <span className={`badge ${getStatoBadgeClass(scadenza)}`}>
                  {getStatoLabel(scadenza)}
                </span>
                <span className="tipo-badge">
                  {getTipoLabel(scadenza.tipo_scadenza)}
                </span>
                {scadenza.ricorrente && (
                  <span className="badge badge-info">🔁 Ricorrente</span>
                )}
              </div>
            </div>
            {timeRemaining && (
              <div className={`time-remaining ${scadenza.completata ? '' : new Date(scadenza.data_scadenza) < new Date() ? 'overdue' : 'upcoming'}`}>
                ⏱️ {timeRemaining}
              </div>
            )}
          </div>

          {/* Details Grid */}
          <div className="detail-grid">
            <div className="detail-row">
              <span className="detail-label">Data Scadenza:</span>
              <span className="detail-value">{formatDateTime(scadenza.data_scadenza)}</span>
            </div>

            {scadenza.prenotazione_id && (
              <div className="detail-row">
                <span className="detail-label">Prenotazione:</span>
                <span className="detail-value">
                  <a href={`#/prenotazioni/${scadenza.prenotazione_id}`} target="_blank" rel="noopener noreferrer">
                    Prenotazione #{scadenza.prenotazione_id}
                  </a>
                </span>
              </div>
            )}

            {scadenza.descrizione && (
              <div className="detail-row full-width">
                <span className="detail-label">Descrizione:</span>
                <span className="detail-value descrizione-text">{scadenza.descrizione}</span>
              </div>
            )}

            <div className="detail-row">
              <span className="detail-label">Creata il:</span>
              <span className="detail-value">{formatDate(scadenza.created_at)}</span>
            </div>

            {scadenza.completata && (
              <>
                <div className="detail-row">
                  <span className="detail-label">Completata il:</span>
                  <span className="detail-value">
                    {scadenza.data_completamento ? formatDateTime(scadenza.data_completamento) : 'N/D'}
                  </span>
                </div>

                {scadenza.note_completamento && (
                  <div className="detail-row full-width">
                    <span className="detail-label">Note Completamento:</span>
                    <span className="detail-value note-completamento">{scadenza.note_completamento}</span>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Completion Section (if not completed) */}
          {!scadenza.completata && (
            <div className="completion-section">
              <h4>Completa Scadenza</h4>
              <p className="help-text">
                Inserisci eventuali note sul completamento della scadenza (opzionale).
              </p>
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Es: Comunicazione inviata con protocollo 12345..."
                rows="4"
                className="form-control"
              />
            </div>
          )}

          {/* Action Buttons for Police Communications */}
          {scadenza.tipo_scadenza === 'COMUNICAZIONE_POLIZIA' && !scadenza.completata && (
            <div className="quick-actions">
              <h4>Azioni Rapide</h4>
              <div className="action-buttons">
                <button
                  className="btn btn-primary"
                  onClick={() => window.location.href = `#/affitti-brevi/comunicazioni-polizia?prenotazione=${scadenza.prenotazione_id}`}
                >
                  📝 Gestisci Comunicazione Polizia
                </button>
              </div>
            </div>
          )}

          {/* Action Buttons for ISTAT Reports */}
          {scadenza.tipo_scadenza === 'REPORT_ISTAT' && !scadenza.completata && (
            <div className="quick-actions">
              <h4>Azioni Rapide</h4>
              <div className="action-buttons">
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    // Extract year/month from scadenza date (deadline is 15th of month for previous month)
                    const deadline = new Date(scadenza.data_scadenza);
                    const reportMonth = deadline.getMonth() === 0 ? 12 : deadline.getMonth();
                    const reportYear = deadline.getMonth() === 0 ? deadline.getFullYear() - 1 : deadline.getFullYear();
                    alert(`Genera report ISTAT per ${reportMonth}/${reportYear}\n\nFunzionalità in sviluppo...`);
                  }}
                >
                  📊 Genera Report ISTAT
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          {!scadenza.completata ? (
            <>
              <button
                onClick={handleComplete}
                disabled={loading}
                className="btn btn-success"
              >
                {loading ? 'Completamento...' : '✓ Completa Scadenza'}
              </button>
              <button onClick={onClose} className="btn btn-secondary">
                Chiudi
              </button>
            </>
          ) : (
            <button onClick={onClose} className="btn btn-primary">
              Chiudi
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default ScadenzaDetail;
