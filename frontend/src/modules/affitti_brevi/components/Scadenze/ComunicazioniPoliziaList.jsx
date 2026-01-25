import { useState, useEffect } from 'react';
import { scadenzeAPI } from '../../services/affittiBreviAPI';
import './Scadenze.css';

function ComunicazioniPoliziaList() {
  const [comunicazioni, setComunicazioni] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterView, setFilterView] = useState('all'); // all, pending, overdue

  // Modal state
  const [showSendModal, setShowSendModal] = useState(false);
  const [selectedComunicazione, setSelectedComunicazione] = useState(null);
  const [dataInvio, setDataInvio] = useState('');
  const [numeroProtocollo, setNumeroProtocollo] = useState('');

  useEffect(() => {
    fetchComunicazioni();
  }, [filterView]);

  const fetchComunicazioni = async () => {
    try {
      setLoading(true);
      let response;

      if (filterView === 'pending') {
        response = await scadenzeAPI.getPendingComunicazioni();
      } else if (filterView === 'overdue') {
        response = await scadenzeAPI.getOverdueComunicazioni();
      } else {
        response = await scadenzeAPI.getComunicazioni();
      }

      setComunicazioni(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento delle comunicazioni');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkSent = (comunicazione) => {
    setSelectedComunicazione(comunicazione);
    // Pre-fill with current date/time
    const now = new Date();
    setDataInvio(now.toISOString().slice(0, 16)); // Format: YYYY-MM-DDTHH:mm
    setNumeroProtocollo('');
    setShowSendModal(true);
  };

  const handleSendModalSubmit = async () => {
    try {
      await scadenzeAPI.markComunicazioneSent(selectedComunicazione.id, {
        data_invio: dataInvio,
        numero_protocollo: numeroProtocollo || null
      });
      setShowSendModal(false);
      setSelectedComunicazione(null);
      fetchComunicazioni();
    } catch (err) {
      alert('Errore nell\'invio: ' + (err.response?.data?.detail || err.message));
      console.error(err);
    }
  };

  const handleMarkConfirmed = async (id) => {
    if (window.confirm('Confermare che la comunicazione è stata ricevuta dalla Questura?')) {
      try {
        await scadenzeAPI.markComunicazioneConfirmed(id);
        fetchComunicazioni();
      } catch (err) {
        alert('Errore: ' + (err.response?.data?.detail || err.message));
        console.error(err);
      }
    }
  };

  const handleMarkError = async (id) => {
    const erroreMessaggio = prompt('Inserisci il messaggio di errore ricevuto:');
    if (erroreMessaggio) {
      try {
        await scadenzeAPI.markComunicazioneError(id, erroreMessaggio);
        fetchComunicazioni();
      } catch (err) {
        alert('Errore: ' + (err.response?.data?.detail || err.message));
        console.error(err);
      }
    }
  };

  const handleRetry = async (id) => {
    if (window.confirm('Riprova invio comunicazione?')) {
      try {
        await scadenzeAPI.retryComunicazione(id);
        fetchComunicazioni();
      } catch (err) {
        alert('Errore: ' + (err.response?.data?.detail || err.message));
        console.error(err);
      }
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questa comunicazione?')) {
      try {
        await scadenzeAPI.deleteComunicazione(id);
        fetchComunicazioni();
      } catch (err) {
        alert('Errore nell\'eliminazione: ' + (err.response?.data?.detail || err.message));
        console.error(err);
      }
    }
  };

  const getStatoLabel = (stato) => {
    const labels = {
      DA_INVIARE: 'Da Inviare',
      INVIATA: 'Inviata',
      CONFERMATA: 'Confermata',
      ERRORE: 'Errore'
    };
    return labels[stato] || stato;
  };

  const getStatoBadgeClass = (stato) => {
    const classes = {
      DA_INVIARE: 'badge-warning',
      INVIATA: 'badge-info',
      CONFERMATA: 'badge-success',
      ERRORE: 'badge-danger'
    };
    return classes[stato] || 'badge-secondary';
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isOverdue = (comunicazione) => {
    if (!comunicazione.prenotazione?.data_checkin) return false;
    const checkin = new Date(comunicazione.prenotazione.data_checkin);
    const deadline = new Date(checkin.getTime() + 24 * 60 * 60 * 1000); // +24 hours
    return new Date() > deadline && comunicazione.stato === 'DA_INVIARE';
  };

  if (loading) return <div className="loading">Caricamento...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="comunicazioni-container">
      <div className="header">
        <h1>Comunicazioni Polizia (Alloggiati Web)</h1>
        <div className="header-actions">
          <button onClick={fetchComunicazioni} className="btn btn-secondary">
            🔄 Aggiorna
          </button>
        </div>
      </div>

      {/* Info Alert */}
      <div className="info-alert">
        <p>
          <strong>⚠️ Obbligo di legge:</strong> Le comunicazioni alla Questura devono essere inviate entro 24 ore dal check-in.
          Le comunicazioni scadute sono evidenziate in rosso.
        </p>
      </div>

      {/* Filters */}
      <div className="filters-bar">
        <div className="filter-group">
          <label>Vista:</label>
          <select value={filterView} onChange={(e) => setFilterView(e.target.value)}>
            <option value="all">Tutte</option>
            <option value="pending">Da Inviare</option>
            <option value="overdue">Scadute (&gt;24h)</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card card-danger">
          <div className="card-number">{comunicazioni.filter(c => isOverdue(c)).length}</div>
          <div className="card-label">Scadute (&gt;24h)</div>
        </div>
        <div className="summary-card card-warning">
          <div className="card-number">{comunicazioni.filter(c => c.stato === 'DA_INVIARE').length}</div>
          <div className="card-label">Da Inviare</div>
        </div>
        <div className="summary-card card-info">
          <div className="card-number">{comunicazioni.filter(c => c.stato === 'INVIATA').length}</div>
          <div className="card-label">Inviate</div>
        </div>
        <div className="summary-card card-success">
          <div className="card-number">{comunicazioni.filter(c => c.stato === 'CONFERMATA').length}</div>
          <div className="card-label">Confermate</div>
        </div>
      </div>

      {/* Send Modal */}
      {showSendModal && selectedComunicazione && (
        <div className="modal-overlay" onClick={() => setShowSendModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Marca come Inviata</h2>
              <button onClick={() => setShowSendModal(false)} className="close-button">&times;</button>
            </div>
            <div className="modal-body">
              <p>Prenotazione: <strong>{selectedComunicazione.prenotazione?.codice_prenotazione}</strong></p>

              <div className="form-group">
                <label>Data/Ora Invio: *</label>
                <input
                  type="datetime-local"
                  value={dataInvio}
                  onChange={(e) => setDataInvio(e.target.value)}
                  className="form-control"
                  required
                />
              </div>

              <div className="form-group">
                <label>Numero Protocollo (opzionale):</label>
                <input
                  type="text"
                  value={numeroProtocollo}
                  onChange={(e) => setNumeroProtocollo(e.target.value)}
                  placeholder="Es: PROT-2025-001234"
                  className="form-control"
                />
                <small className="form-text">Inserisci il numero protocollo se fornito dalla Questura</small>
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={handleSendModalSubmit} className="btn btn-success">
                ✓ Conferma Invio
              </button>
              <button onClick={() => setShowSendModal(false)} className="btn btn-secondary">
                Annulla
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Prenotazione</th>
              <th>Check-in</th>
              <th>Immobile</th>
              <th>N. Ospiti</th>
              <th>Stato</th>
              <th>Data Invio</th>
              <th>Protocollo</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {comunicazioni.length === 0 ? (
              <tr>
                <td colSpan="8" className="text-center">Nessuna comunicazione trovata</td>
              </tr>
            ) : (
              comunicazioni.map((comunicazione) => (
                <tr
                  key={comunicazione.id}
                  className={isOverdue(comunicazione) ? 'row-overdue' : ''}
                >
                  <td>
                    <a href={`#/prenotazioni/${comunicazione.prenotazione_id}`}>
                      {comunicazione.prenotazione?.codice_prenotazione || `#${comunicazione.prenotazione_id}`}
                    </a>
                    {isOverdue(comunicazione) && <span className="overdue-badge">⚠️ SCADUTA</span>}
                  </td>
                  <td>{formatDateTime(comunicazione.prenotazione?.data_checkin)}</td>
                  <td>
                    {comunicazione.prenotazione?.unita_immobiliare_id
                      ? `Immobile #${comunicazione.prenotazione.unita_immobiliare_id}`
                      : '-'}
                  </td>
                  <td>
                    {comunicazione.dati_ospiti
                      ? (Array.isArray(comunicazione.dati_ospiti) ? comunicazione.dati_ospiti.length : Object.keys(comunicazione.dati_ospiti).length)
                      : comunicazione.prenotazione?.numero_ospiti || '-'}
                  </td>
                  <td>
                    <span className={`badge ${getStatoBadgeClass(comunicazione.stato)}`}>
                      {getStatoLabel(comunicazione.stato)}
                    </span>
                  </td>
                  <td>{formatDateTime(comunicazione.data_invio)}</td>
                  <td>{comunicazione.numero_protocollo || '-'}</td>
                  <td className="actions-cell">
                    {comunicazione.stato === 'DA_INVIARE' && (
                      <>
                        <button
                          onClick={() => handleMarkSent(comunicazione)}
                          className="btn btn-sm btn-success"
                          title="Marca come Inviata"
                        >
                          📤 Inviata
                        </button>
                        <button
                          onClick={() => handleMarkError(comunicazione.id)}
                          className="btn btn-sm btn-danger"
                          title="Segna Errore"
                        >
                          ❌
                        </button>
                      </>
                    )}
                    {comunicazione.stato === 'INVIATA' && (
                      <>
                        <button
                          onClick={() => handleMarkConfirmed(comunicazione.id)}
                          className="btn btn-sm btn-success"
                          title="Conferma Ricezione"
                        >
                          ✓ Conferma
                        </button>
                        <button
                          onClick={() => handleMarkError(comunicazione.id)}
                          className="btn btn-sm btn-danger"
                          title="Segna Errore"
                        >
                          ❌
                        </button>
                      </>
                    )}
                    {comunicazione.stato === 'ERRORE' && (
                      <button
                        onClick={() => handleRetry(comunicazione.id)}
                        className="btn btn-sm btn-warning"
                        title="Riprova"
                      >
                        🔄 Riprova
                      </button>
                    )}
                    {comunicazione.stato !== 'CONFERMATA' && (
                      <button
                        onClick={() => handleDelete(comunicazione.id)}
                        className="btn btn-sm btn-danger"
                        title="Elimina"
                      >
                        🗑️
                      </button>
                    )}
                    {comunicazione.errore_messaggio && (
                      <button
                        onClick={() => alert(`Errore:\n${comunicazione.errore_messaggio}`)}
                        className="btn btn-sm btn-info"
                        title="Vedi Errore"
                      >
                        ℹ️
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="table-footer">
        <p>Totale: {comunicazioni.length} comunicazioni</p>
      </div>
    </div>
  );
}

export default ComunicazioniPoliziaList;
