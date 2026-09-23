import { useState } from 'react';
import { speseRicorrentiAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';

const TIPI_NOTI = ['IMU', 'TARI', 'UTENZA_LUCE', 'UTENZA_GAS', 'UTENZA_ACQUA', 'ALTRO'];

function SpesaRicorrenteForm({ unitaImmobiliareId, condominioId, onClose }) {
  const [tipoSpesa, setTipoSpesa] = useState('IMU');
  const [tipoSpesaLibero, setTipoSpesaLibero] = useState('');
  const [responsabile, setResponsabile] = useState('PROPRIETARIO');
  const [periodo, setPeriodo] = useState(String(new Date().getFullYear()));
  const [rata, setRata] = useState('');
  const [importo, setImporto] = useState('');
  const [dataScadenza, setDataScadenza] = useState('');
  const [note, setNote] = useState('');

  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await speseRicorrentiAPI.create({
        unita_immobiliare_id: unitaImmobiliareId || undefined,
        condominio_id: condominioId || undefined,
        tipo_spesa: tipoSpesa === 'ALTRO' && tipoSpesaLibero ? tipoSpesaLibero : tipoSpesa,
        responsabile,
        periodo,
        rata: rata || undefined,
        importo: parseFloat(importo),
        data_scadenza: dataScadenza,
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
          <h2>Nuova Spesa Ricorrente</h2>
          <button className="close-btn" onClick={() => onClose(false)}>×</button>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label>Tipo Spesa *</label>
              <select value={tipoSpesa} onChange={(e) => setTipoSpesa(e.target.value)} required>
                {TIPI_NOTI.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            {tipoSpesa === 'ALTRO' && (
              <div className="form-group">
                <label>Specifica tipo</label>
                <input type="text" value={tipoSpesaLibero} onChange={(e) => setTipoSpesaLibero(e.target.value)} />
              </div>
            )}
            <div className="form-group">
              <label>Responsabile *</label>
              <select value={responsabile} onChange={(e) => setResponsabile(e.target.value)} required>
                <option value="PROPRIETARIO">Proprietario</option>
                <option value="CONDUTTORE">Conduttore</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Periodo *</label>
              <input type="text" value={periodo} onChange={(e) => setPeriodo(e.target.value)} placeholder="es. 2026" required />
            </div>
            <div className="form-group">
              <label>Rata</label>
              <input type="text" value={rata} onChange={(e) => setRata(e.target.value)} placeholder="es. ACCONTO, SALDO" />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Importo (€) *</label>
              <input type="number" step="0.01" min="0.01" value={importo} onChange={(e) => setImporto(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Data Scadenza *</label>
              <input type="date" value={dataScadenza} onChange={(e) => setDataScadenza(e.target.value)} required />
            </div>
          </div>

          <div className="form-group">
            <label>Note</label>
            <textarea value={note} onChange={(e) => setNote(e.target.value)} rows="2" />
          </div>

          <div className="form-actions">
            <button type="button" onClick={() => onClose(false)} disabled={saving}>Annulla</button>
            <button type="submit" className="primary" disabled={saving}>
              {saving ? 'Salvataggio...' : 'Salva'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default SpesaRicorrenteForm;
