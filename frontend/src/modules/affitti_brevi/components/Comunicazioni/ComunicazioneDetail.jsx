import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { comunicazioniAPI } from '../../services/affittiBreviAPI';
import './ComunicazioneDetail.css';

const TIPO_LABELS = {
  POLIZIA: 'Comunicazione Polizia',
  ISTAT: 'Report ISTAT',
  TASSA_DICHIARAZIONE: 'Tassa di Soggiorno',
  ALTRO: 'Altro',
};

function ComunicazioneDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [comunicazione, setComunicazione] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [note, setNote] = useState('');
  const [completing, setCompleting] = useState(false);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await comunicazioniAPI.getById(id);
      setComunicazione(response.data);
    } catch (err) {
      setError('Comunicazione non trovata o errore di caricamento');
    } finally {
      setLoading(false);
    }
  };

  const handleCompleta = async () => {
    if (!window.confirm('Segnare questa comunicazione come completata?')) return;
    try {
      setCompleting(true);
      await comunicazioniAPI.segnaCompletata(id, note || null);
      await load();
    } catch (err) {
      alert('Errore nel completamento della comunicazione');
    } finally {
      setCompleting(false);
    }
  };

  if (loading) return <div className="comunicazione-detail">Caricamento...</div>;
  if (error) return <div className="comunicazione-detail error">{error}</div>;
  if (!comunicazione) return null;

  const STATI_COMPLETATI = ['INVIATA', 'CONFERMATA', 'ANNULLATA'];
  const completata = STATI_COMPLETATI.includes(comunicazione.stato);

  return (
    <div className="comunicazione-detail">
      <button className="btn btn-secondary" onClick={() => navigate(-1)}>&larr; Indietro</button>

      <h2>{TIPO_LABELS[comunicazione.tipo] || comunicazione.tipo}</h2>

      <div className="comunicazione-detail-grid">
        <div className="comunicazione-detail-row">
          <span className="comunicazione-detail-label">Stato:</span>
          <span className={`badge badge-${completata ? 'success' : 'warning'}`}>{comunicazione.stato}</span>
        </div>
        <div className="comunicazione-detail-row">
          <span className="comunicazione-detail-label">Scadenza:</span>
          <span>{new Date(comunicazione.data_scadenza).toLocaleString('it-IT')}</span>
        </div>
        {comunicazione.data_invio && (
          <div className="comunicazione-detail-row">
            <span className="comunicazione-detail-label">Inviata il:</span>
            <span>{new Date(comunicazione.data_invio).toLocaleString('it-IT')}</span>
          </div>
        )}
      </div>

      {!completata && (
        <div className="completion-section">
          <h4>Completa manualmente</h4>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Note (opzionale)"
            rows={3}
          />
          <button className="btn btn-success" disabled={completing} onClick={handleCompleta}>
            {completing ? 'Completamento...' : '✓ Segna come completata'}
          </button>
        </div>
      )}
    </div>
  );
}

export default ComunicazioneDetail;
