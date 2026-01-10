import { useState, useEffect } from 'react';
import { prenotazioniAPI } from '../../services/affittiBreviAPI';
import PrenotazioneForm from './PrenotazioneForm';
import './Prenotazioni.css';

function PrenotazioniList() {
  const [prenotazioni, setPrenotazioni] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingPrenotazione, setEditingPrenotazione] = useState(null);

  useEffect(() => {
    fetchPrenotazioni();
  }, []);

  const fetchPrenotazioni = async () => {
    try {
      setLoading(true);
      const response = await prenotazioniAPI.getAll();
      setPrenotazioni(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento delle prenotazioni');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questa prenotazione?')) {
      try {
        await prenotazioniAPI.delete(id);
        fetchPrenotazioni();
      } catch (err) {
        setError('Errore nell\'eliminazione della prenotazione');
        console.error(err);
      }
    }
  };

  const handleEdit = (prenotazione) => {
    setEditingPrenotazione(prenotazione);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingPrenotazione(null);
    fetchPrenotazioni();
  };

  const getStatoLabel = (stato) => {
    const labels = {
      CONFERMATA: 'Confermata',
      IN_ATTESA: 'In Attesa',
      CANCELLATA: 'Cancellata',
      CHECK_IN_EFFETTUATO: 'Check-in',
      CHECK_OUT_EFFETTUATO: 'Check-out',
      NO_SHOW: 'No Show'
    };
    return labels[stato] || stato;
  };

  const getStatoBadgeClass = (stato) => {
    const classes = {
      CONFERMATA: 'badge-success',
      IN_ATTESA: 'badge-warning',
      CANCELLATA: 'badge-danger',
      CHECK_IN_EFFETTUATO: 'badge-info',
      CHECK_OUT_EFFETTUATO: 'badge-secondary',
      NO_SHOW: 'badge-danger'
    };
    return classes[stato] || 'badge-secondary';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('it-IT');
  };

  if (loading) return <div className="loading">Caricamento...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="prenotazioni-container">
      <div className="header">
        <h1>Prenotazioni</h1>
        <div className="header-actions">
          <button onClick={() => setShowForm(true)} className="btn btn-primary">
            + Nuova Prenotazione
          </button>
        </div>
      </div>

      {showForm && (
        <PrenotazioneForm
          prenotazione={editingPrenotazione}
          onClose={handleFormClose}
        />
      )}

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Codice</th>
              <th>Check-in</th>
              <th>Check-out</th>
              <th>Notti</th>
              <th>Ospiti</th>
              <th>Portale</th>
              <th>Prezzo</th>
              <th>Stato</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {prenotazioni.length === 0 ? (
              <tr>
                <td colSpan="9" className="text-center">Nessuna prenotazione trovata</td>
              </tr>
            ) : (
              prenotazioni.map((prenotazione) => (
                <tr key={prenotazione.id}>
                  <td>{prenotazione.codice_prenotazione}</td>
                  <td>{formatDate(prenotazione.data_checkin)}</td>
                  <td>{formatDate(prenotazione.data_checkout)}</td>
                  <td>{prenotazione.notti || '-'}</td>
                  <td>{prenotazione.numero_ospiti}</td>
                  <td>{prenotazione.portale_origine}</td>
                  <td>
                    {prenotazione.prezzo_totale
                      ? `€ ${parseFloat(prenotazione.prezzo_totale).toFixed(2)}`
                      : '-'}
                  </td>
                  <td>
                    <span className={`badge ${getStatoBadgeClass(prenotazione.stato)}`}>
                      {getStatoLabel(prenotazione.stato)}
                    </span>
                  </td>
                  <td>
                    <button onClick={() => handleEdit(prenotazione)} className="btn btn-sm btn-secondary">
                      Modifica
                    </button>
                    <button onClick={() => handleDelete(prenotazione.id)} className="btn btn-sm btn-danger">
                      Elimina
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default PrenotazioniList;
