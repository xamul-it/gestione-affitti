import { useState, useEffect } from 'react';
import { assegnazioniConduttoreAPI } from '../../services/immobiliAPI';
import AssegnazioneConduttoreForm from './AssegnazioneConduttoreForm';
import './Conduttori.css';

function formatData(value) {
  if (!value) return '-';
  return new Date(value).toLocaleDateString('it-IT');
}

function AssegnazioneConduttoreSection({ unitaImmobiliareId }) {
  const [assegnazioni, setAssegnazioni] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    if (unitaImmobiliareId) {
      fetchAssegnazioni();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unitaImmobiliareId]);

  const fetchAssegnazioni = async () => {
    try {
      setLoading(true);
      const response = await assegnazioniConduttoreAPI.getByUnita(unitaImmobiliareId);
      setAssegnazioni(response.data);
      setError(null);
    } catch (err) {
      setError('Errore nel caricamento delle assegnazioni');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleChiudi = async (assegnazione) => {
    if (!window.confirm('Chiudere questa assegnazione impostando la data di fine a oggi?')) return;
    try {
      await assegnazioniConduttoreAPI.update(assegnazione.id, {
        data_fine: new Date().toISOString().slice(0, 10),
      });
      fetchAssegnazioni();
    } catch (err) {
      alert('Errore nella chiusura dell\'assegnazione');
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Eliminare questa assegnazione?')) {
      try {
        await assegnazioniConduttoreAPI.delete(id);
        fetchAssegnazioni();
      } catch (err) {
        alert('Errore nell\'eliminazione dell\'assegnazione');
        console.error(err);
      }
    }
  };

  if (!unitaImmobiliareId) {
    return (
      <div className="diritti-section">
        <p className="info-message">Salva prima l'unità immobiliare per poter gestire i conduttori</p>
      </div>
    );
  }

  return (
    <div className="diritti-section">
      <div className="diritti-header">
        <h3>Conduttore (occupante)</h3>
        <button onClick={() => setShowForm(true)} className="btn btn-sm btn-primary">
          + Assegna Conduttore
        </button>
      </div>

      {showForm && (
        <AssegnazioneConduttoreForm
          unitaImmobiliareId={unitaImmobiliareId}
          onClose={(saved) => { setShowForm(false); if (saved) fetchAssegnazioni(); }}
        />
      )}

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading">Caricamento...</div>
      ) : assegnazioni.length === 0 ? (
        <p className="no-data">Nessun conduttore assegnato</p>
      ) : (
        <div className="diritti-list">
          {assegnazioni.map((a) => (
            <div key={a.id} className="diritto-card">
              <div className="diritto-info">
                <div className="diritto-nome">Conduttore #{a.conduttore_id}</div>
                <div className="diritto-meta">
                  {!a.data_fine ? (
                    <span className="badge badge-success">In corso</span>
                  ) : (
                    <span className="badge badge-info">Concluso</span>
                  )}
                  <span className="diritto-date">Dal: {formatData(a.data_inizio)}</span>
                  {a.data_fine && <span className="diritto-date">Al: {formatData(a.data_fine)}</span>}
                </div>
                {a.note && <div className="diritto-note">{a.note}</div>}
              </div>
              <div className="diritto-actions">
                {!a.data_fine && (
                  <button onClick={() => handleChiudi(a)} className="btn btn-sm btn-secondary" title="Chiudi assegnazione">
                    Chiudi
                  </button>
                )}
                <button onClick={() => handleDelete(a.id)} className="btn btn-sm btn-danger" title="Elimina">
                  🗑
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default AssegnazioneConduttoreSection;
