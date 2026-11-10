import { Button } from '../../../../components/UI';
import { useState } from 'react';
import { speseRicorrentiAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';

function prossimoPeriodo(periodo) {
  const next = Number(periodo) + 1;
  return Number.isNaN(next) ? '' : String(next);
}

function DuplicaSpesaModal({ spesa, onClose }) {
  const [periodo, setPeriodo] = useState(prossimoPeriodo(spesa.periodo));
  const [dataScadenza, setDataScadenza] = useState('');
  const [importo, setImporto] = useState(spesa.importo);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await speseRicorrentiAPI.duplica(spesa.id, {
        periodo,
        data_scadenza: dataScadenza,
        importo: importo !== '' ? parseFloat(importo) : undefined,
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
          <h2>Duplica per Periodo Successivo</h2>
          <Button type="button" variant="ghost" size="sm" aria-label="Chiudi" onClick={() => onClose(false)}>×</Button>
        </div>

        <p className="field-hint">
          {spesa.tipo_spesa} {spesa.rata ? `(${spesa.rata})` : ''} — importo e rata sono precompilati con i valori
          dell'originale, ma vanno confermati: gli importi di IMU/TARI/utenze cambiano ogni periodo.
        </p>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Nuovo Periodo *</label>
            <input type="text" value={periodo} onChange={(e) => setPeriodo(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Nuova Data Scadenza *</label>
            <input type="date" value={dataScadenza} onChange={(e) => setDataScadenza(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Importo (€)</label>
            <input type="number" step="0.01" min="0.01" value={importo} onChange={(e) => setImporto(e.target.value)} />
          </div>

          <div className="form-actions">
            <Button variant="secondary" type="button" onClick={() => onClose(false)} disabled={saving}>Annulla</Button>
            <Button type="submit" disabled={saving}>
              {saving ? 'Creazione...' : 'Crea'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default DuplicaSpesaModal;
