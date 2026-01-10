import { useState, useEffect } from 'react';
import { millesimiImmobileAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';

function MillesimiForm({ millesimo, tabellaId, immobili, tabella, onClose }) {
  const [formData, setFormData] = useState({
    immobile_id: '',
    tabella_millesimale_id: tabellaId,
    millesimi: '',
    piano: '',
    numero_occupanti: 0,
    consumo: 0,
    unita_misura_consumo: '',
    quota_fissa: '',
  });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (millesimo) {
      setFormData(millesimo);
    } else {
      setFormData(prev => ({
        ...prev,
        tabella_millesimale_id: tabellaId
      }));
    }
  }, [millesimo, tabellaId]);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    let newValue = value;

    if (type === 'number') {
      newValue = value === '' ? '' : parseFloat(value);
    }

    setFormData(prev => ({
      ...prev,
      [name]: newValue
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Prepara dati per invio
    const dataToSend = {
      ...formData,
      millesimi: parseFloat(formData.millesimi),
      piano: formData.piano === '' ? null : parseInt(formData.piano),
      numero_occupanti: parseInt(formData.numero_occupanti) || 0,
      consumo: parseFloat(formData.consumo) || 0,
      quota_fissa: formData.quota_fissa === '' ? null : parseFloat(formData.quota_fissa),
    };

    try {
      if (millesimo) {
        await millesimiImmobileAPI.update(millesimo.id, dataToSend);
      } else {
        await millesimiImmobileAPI.create(dataToSend);
      }
      setSuccess(true);
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (err) {
      setError(formatApiError(err));
      console.error(err);
    }
  };

  const needsPiano = tabella?.tipo_ripartizione === 'millesimi_piano';
  const needsOccupanti = tabella?.tipo_ripartizione === 'occupanti' ||
                         (tabella?.percentuale_occupanti || 0) > 0;
  const needsConsumo = tabella?.tipo_ripartizione === 'millesimi_consumo' ||
                       (tabella?.percentuale_consumo || 0) > 0;
  const needsQuotaFissa = tabella?.tipo_ripartizione === 'personalizzata';

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>{millesimo ? 'Modifica Millesimi' : 'Aggiungi Millesimi Immobile'}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {error && <div className="error">{error}</div>}
        {success && <div className="success">Operazione completata con successo!</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label>Immobile *</label>
              <select
                name="immobile_id"
                value={formData.immobile_id}
                onChange={handleChange}
                disabled={!!millesimo}
                required
              >
                <option value="">Seleziona immobile</option>
                {immobili.map((imm) => (
                  <option key={imm.id} value={imm.id}>
                    {imm.codice} - {imm.indirizzo}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Millesimi *</label>
              <input
                type="number"
                name="millesimi"
                value={formData.millesimi}
                onChange={handleChange}
                step="0.001"
                min="0"
                required
              />
              <small>Valore millesimale (es. 45.5 su 1000)</small>
            </div>
          </div>

          {needsPiano && (
            <div className="form-row">
              <div className="form-group">
                <label>Piano {needsPiano && '*'}</label>
                <input
                  type="number"
                  name="piano"
                  value={formData.piano}
                  onChange={handleChange}
                  min="0"
                  required={needsPiano}
                />
                <small>Numero del piano per calcolo ascensore</small>
              </div>
            </div>
          )}

          {needsOccupanti && (
            <div className="form-row">
              <div className="form-group">
                <label>Numero Occupanti {needsOccupanti && '*'}</label>
                <input
                  type="number"
                  name="numero_occupanti"
                  value={formData.numero_occupanti}
                  onChange={handleChange}
                  min="0"
                  required={needsOccupanti}
                />
                <small>Numero persone per ripartizione acqua, ecc.</small>
              </div>
            </div>
          )}

          {needsConsumo && (
            <div className="form-row">
              <div className="form-group">
                <label>Consumo</label>
                <input
                  type="number"
                  name="consumo"
                  value={formData.consumo}
                  onChange={handleChange}
                  step="0.01"
                  min="0"
                />
              </div>
              <div className="form-group">
                <label>Unità Misura</label>
                <input
                  type="text"
                  name="unita_misura_consumo"
                  value={formData.unita_misura_consumo}
                  onChange={handleChange}
                  placeholder="es. kWh, mc"
                />
              </div>
            </div>
          )}

          {needsQuotaFissa && (
            <div className="form-row">
              <div className="form-group">
                <label>Quota Fissa *</label>
                <input
                  type="number"
                  name="quota_fissa"
                  value={formData.quota_fissa}
                  onChange={handleChange}
                  step="0.01"
                  min="0"
                  required={needsQuotaFissa}
                />
                <small>Percentuale o importo fisso per ripartizione personalizzata</small>
              </div>
            </div>
          )}

          <div className="info-box">
            <strong>Tipo Ripartizione: </strong>
            {tabella?.tipo_ripartizione === 'millesimi' && 'Millesimi Puri'}
            {tabella?.tipo_ripartizione === 'millesimi_consumo' && 'Millesimi + Consumo'}
            {tabella?.tipo_ripartizione === 'occupanti' && 'Per Occupanti'}
            {tabella?.tipo_ripartizione === 'millesimi_piano' && 'Millesimi + Piano'}
            {tabella?.tipo_ripartizione === 'personalizzata' && 'Personalizzata'}
          </div>

          <div className="form-actions">
            <button type="button" onClick={onClose}>Annulla</button>
            <button type="submit" className="primary">Salva</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default MillesimiForm;
