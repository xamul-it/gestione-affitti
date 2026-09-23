import { useState, useEffect } from 'react';
import { assegnazioniConduttoreAPI, conduttoriAPI } from '../../services/immobiliAPI';
import { getSoggettoById } from '../../../anagrafica_italiana/services/anagraficaAPI';
import { formatApiError } from '../../../../utils/errorHandling';

function AssegnazioneConduttoreForm({ unitaImmobiliareId, onClose }) {
  const [conduttori, setConduttori] = useState([]);
  const [conduttoreId, setConduttoreId] = useState('');
  const [dataInizio, setDataInizio] = useState('');
  const [dataFine, setDataFine] = useState('');
  const [note, setNote] = useState('');
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchConduttori();
  }, []);

  const fetchConduttori = async () => {
    try {
      const response = await conduttoriAPI.getAll();
      const arricchiti = await Promise.all(
        response.data.map(async (c) => {
          try {
            const soggetto = await getSoggettoById(c.soggetto_id);
            const nome = soggetto.ragione_sociale || [soggetto.nome, soggetto.cognome].filter(Boolean).join(' ');
            return { ...c, nomeVisualizzato: nome || `Soggetto #${c.soggetto_id}` };
          } catch (err) {
            return { ...c, nomeVisualizzato: `Soggetto #${c.soggetto_id}` };
          }
        })
      );
      setConduttori(arricchiti);
    } catch (err) {
      console.error('Errore nel caricamento dei conduttori:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!conduttoreId) {
      setError('Seleziona un conduttore');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await assegnazioniConduttoreAPI.create({
        unita_immobiliare_id: unitaImmobiliareId,
        conduttore_id: parseInt(conduttoreId, 10),
        data_inizio: dataInizio || undefined,
        data_fine: dataFine || undefined,
        note: note || undefined,
      });
      onClose(true);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Assegna Conduttore</h2>
          <button className="close-btn" onClick={() => onClose(false)}>×</button>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Conduttore *</label>
            <select value={conduttoreId} onChange={(e) => setConduttoreId(e.target.value)} required>
              <option value="">Seleziona conduttore...</option>
              {conduttori.map((c) => (
                <option key={c.id} value={c.id}>{c.nomeVisualizzato}</option>
              ))}
            </select>
            {conduttori.length === 0 && (
              <small className="field-hint">Nessun conduttore disponibile. Registrane uno nella sezione Conduttori.</small>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Dal</label>
              <input type="date" value={dataInizio} onChange={(e) => setDataInizio(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Al (vuoto = tuttora in corso)</label>
              <input type="date" value={dataFine} onChange={(e) => setDataFine(e.target.value)} />
            </div>
          </div>

          <div className="form-group">
            <label>Note</label>
            <textarea value={note} onChange={(e) => setNote(e.target.value)} rows="2" />
          </div>

          <div className="form-actions">
            <button type="button" onClick={() => onClose(false)} disabled={saving}>Annulla</button>
            <button type="submit" className="primary" disabled={saving}>
              {saving ? 'Salvataggio...' : 'Assegna'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default AssegnazioneConduttoreForm;
