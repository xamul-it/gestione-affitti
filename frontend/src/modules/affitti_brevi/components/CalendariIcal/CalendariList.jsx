import { useState, useEffect } from 'react';
import { calendariAPI } from '../../services/affittiBreviAPI';
import CalendarioForm from './CalendarioForm';
import './Calendari.css';

function CalendariList() {
  const [calendari, setCalendari] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingCalendario, setEditingCalendario] = useState(null);

  useEffect(() => {
    fetchCalendari();
  }, []);

  const fetchCalendari = async () => {
    try {
      setLoading(true);
      const response = await calendariAPI.getAll();
      setCalendari(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento dei calendari iCal');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Sei sicuro di voler eliminare questa configurazione calendario?')) {
      try {
        await calendariAPI.delete(id);
        fetchCalendari();
      } catch (err) {
        setError('Errore nell\'eliminazione del calendario');
        console.error(err);
      }
    }
  };

  const handleEdit = (calendario) => {
    setEditingCalendario(calendario);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingCalendario(null);
    fetchCalendari();
  };

  const getPortaleLabel = (portale) => {
    const labels = {
      BOOKING_COM: 'Booking.com',
      AIRBNB: 'Airbnb',
      VRBO: 'Vrbo',
      ALTRO: 'Altro'
    };
    return labels[portale] || portale;
  };

  const getStatoSyncLabel = (stato) => {
    const labels = {
      MAI_SINCRONIZZATO: 'Mai sincronizzato',
      IN_CORSO: 'In corso',
      SUCCESSO: 'Successo',
      ERRORE: 'Errore'
    };
    return labels[stato] || stato;
  };

  const getStatoSyncBadgeClass = (stato) => {
    const classes = {
      MAI_SINCRONIZZATO: 'badge-secondary',
      IN_CORSO: 'badge-warning',
      SUCCESSO: 'badge-success',
      ERRORE: 'badge-danger'
    };
    return classes[stato] || 'badge-secondary';
  };

  const formatDateTime = (dateTimeString) => {
    if (!dateTimeString) return '-';
    return new Date(dateTimeString).toLocaleString('it-IT');
  };

  if (loading) return <div className="loading">Caricamento...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="calendari-container">
      <div className="header">
        <h1>Calendari iCal</h1>
        <div className="header-actions">
          <button onClick={() => setShowForm(true)} className="btn btn-primary">
            + Nuovo Calendario
          </button>
        </div>
      </div>

      {showForm && (
        <CalendarioForm
          calendario={editingCalendario}
          onClose={handleFormClose}
        />
      )}

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID Immobile</th>
              <th>Portale</th>
              <th>URL Dashboard</th>
              <th>Stato Sync</th>
              <th>Ultima Sync</th>
              <th>Attivo</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {calendari.length === 0 ? (
              <tr>
                <td colSpan="7" className="text-center">Nessun calendario configurato</td>
              </tr>
            ) : (
              calendari.map((calendario) => (
                <tr key={calendario.id}>
                  <td>{calendario.unita_immobiliare_id}</td>
                  <td>{getPortaleLabel(calendario.portale)}</td>
                  <td>
                    {calendario.url_dashboard_portale ? (
                      <a
                        href={calendario.url_dashboard_portale}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="external-link"
                      >
                        Apri Dashboard
                      </a>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td>
                    <span className={`badge ${getStatoSyncBadgeClass(calendario.stato_sincronizzazione)}`}>
                      {getStatoSyncLabel(calendario.stato_sincronizzazione)}
                    </span>
                  </td>
                  <td>{formatDateTime(calendario.ultima_sincronizzazione)}</td>
                  <td>
                    <span className={`badge ${calendario.attivo ? 'badge-success' : 'badge-danger'}`}>
                      {calendario.attivo ? 'Sì' : 'No'}
                    </span>
                  </td>
                  <td>
                    <button onClick={() => handleEdit(calendario)} className="btn btn-sm btn-secondary">
                      Modifica
                    </button>
                    <button onClick={() => handleDelete(calendario.id)} className="btn btn-sm btn-danger">
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

export default CalendariList;
