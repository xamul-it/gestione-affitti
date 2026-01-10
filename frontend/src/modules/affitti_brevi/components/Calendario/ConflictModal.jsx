import { useState } from 'react';
import axios from 'axios';
import './calendario.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

function ConflictModal({ conflicts, onClose, onResolved }) {
  const [resolving, setResolving] = useState(null);
  const [error, setError] = useState(null);

  const handleResolve = async (prenotazioneId, action) => {
    setResolving(prenotazioneId);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');

      await axios.post(
        `${API_BASE_URL}/affitti-brevi/calendario/resolve-conflict/${prenotazioneId}`,
        null,
        {
          params: { action },
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      // Notify parent that conflict was resolved
      onResolved();
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore nella risoluzione del conflitto');
      console.error(err);
    } finally {
      setResolving(null);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content conflict-modal">
        <div className="modal-header">
          <h2>⚠️ Conflitti di Prenotazione</h2>
          <button onClick={onClose} className="btn-close">&times;</button>
        </div>

        <div className="modal-body">
          {error && (
            <div className="alert alert-danger">{error}</div>
          )}

          <p className="conflict-intro">
            Sono stati rilevati <strong>{conflicts.length}</strong> conflitti di prenotazione.
            Lo stesso immobile è prenotato su più piattaforme per le stesse date.
          </p>

          <div className="conflicts-list">
            {conflicts.map((conflict, index) => (
              <div key={index} className="conflict-item">
                <div className="conflict-header">
                  <h3>Conflitto #{index + 1}</h3>
                  <div className="conflict-meta">
                    <span className="conflict-property">Immobile ID: {conflict.immobile_id}</span>
                    <span className="conflict-dates">
                      {formatDate(conflict.overlap_start)} - {formatDate(conflict.overlap_end)}
                    </span>
                    <span className="conflict-duration">
                      ({conflict.overlap_days} {conflict.overlap_days === 1 ? 'giorno' : 'giorni'})
                    </span>
                  </div>
                </div>

                <div className="conflict-bookings">
                  {conflict.prenotazioni.map((pren, idx) => (
                    <div key={pren.id} className={`booking-card booking-${idx + 1}`}>
                      <div className="booking-header">
                        <span className="booking-platform">{pren.portale}</span>
                        <span className={`booking-status status-${pren.stato.toLowerCase()}`}>
                          {pren.stato}
                        </span>
                      </div>

                      <div className="booking-details">
                        <div><strong>Codice:</strong> {pren.codice}</div>
                        <div><strong>Check-in:</strong> {formatDate(pren.checkin)}</div>
                        <div><strong>Check-out:</strong> {formatDate(pren.checkout)}</div>
                      </div>

                      <div className="booking-actions">
                        <button
                          onClick={() => handleResolve(pren.id, 'keep')}
                          className="btn btn-sm btn-success"
                          disabled={resolving !== null || pren.stato === 'CANCELLATA'}
                        >
                          {resolving === pren.id ? 'Elaborazione...' : '✓ Mantieni Questa'}
                        </button>
                        <button
                          onClick={() => handleResolve(pren.id, 'cancel')}
                          className="btn btn-sm btn-danger"
                          disabled={resolving !== null || pren.stato === 'CANCELLATA'}
                        >
                          {resolving === pren.id ? 'Elaborazione...' : '✗ Cancella'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="conflict-note">
                  <p><strong>Come risolvere:</strong> Scegli quale prenotazione mantenere e cancella l'altra.
                    Assicurati di contattare l'ospite della prenotazione cancellata.</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="modal-footer">
          <button onClick={onClose} className="btn btn-secondary">
            Chiudi
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConflictModal;
