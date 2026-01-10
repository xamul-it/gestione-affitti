import { useState, useEffect } from 'react';
import { tasseAPI } from '../../services/affittiBreviAPI';
import './Tasse.css';

function TassaConfigForm({ config, onClose }) {
  const [formData, setFormData] = useState({
    comune_id: '',
    comune_nome: '',
    tipo_calcolo: 'FISSO',
    importo_fisso: '',
    percentuale: '',
    eta_minima: '0',
    eta_massima: '',
    notti_max: '',
    data_inizio_validita: '',
    data_fine_validita: '',
    attiva: true,
    note: ''
  });

  const [scaglioni, setScaglioni] = useState([]);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (config) {
      setFormData({
        comune_id: config.comune_id || '',
        comune_nome: config.comune_nome || '',
        tipo_calcolo: config.tipo_calcolo || 'FISSO',
        importo_fisso: config.importo_fisso || '',
        percentuale: config.percentuale || '',
        eta_minima: config.eta_minima?.toString() || '0',
        eta_massima: config.eta_massima?.toString() || '',
        notti_max: config.notti_max?.toString() || '',
        data_inizio_validita: config.data_inizio_validita || '',
        data_fine_validita: config.data_fine_validita || '',
        attiva: config.attiva !== undefined ? config.attiva : true,
        note: config.note || ''
      });

      // Load scaglioni if editing SCAGLIONI config
      if (config.tipo_calcolo === 'SCAGLIONI' && config.id) {
        loadScaglioni(config.id);
      }
    }
  }, [config]);

  const loadScaglioni = async (configId) => {
    try {
      const response = await tasseAPI.getScaglioni(configId);
      setScaglioni(response.data);
    } catch (err) {
      console.error('Errore nel caricamento scaglioni:', err);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const addScaglione = () => {
    setScaglioni(prev => [
      ...prev,
      { notte_da: '', notte_a: '', importo: '' }
    ]);
  };

  const removeScaglione = (index) => {
    setScaglioni(prev => prev.filter((_, i) => i !== index));
  };

  const handleScaglioneChange = (index, field, value) => {
    setScaglioni(prev => prev.map((scaglione, i) => {
      if (i === index) {
        return { ...scaglione, [field]: value };
      }
      return scaglione;
    }));
  };

  const validateForm = () => {
    // Required fields
    if (!formData.comune_id || !formData.comune_nome || !formData.data_inizio_validita) {
      setError('Compila tutti i campi obbligatori');
      return false;
    }

    // Tipo-specific validation
    if (formData.tipo_calcolo === 'FISSO' && !formData.importo_fisso) {
      setError('Importo fisso è obbligatorio per tipo calcolo FISSO');
      return false;
    }

    if (formData.tipo_calcolo === 'PERCENTUALE' && !formData.percentuale) {
      setError('Percentuale è obbligatoria per tipo calcolo PERCENTUALE');
      return false;
    }

    if (formData.tipo_calcolo === 'SCAGLIONI' && scaglioni.length === 0) {
      setError('Almeno uno scaglione è richiesto per tipo calcolo SCAGLIONI');
      return false;
    }

    // Date validation
    if (formData.data_fine_validita && formData.data_fine_validita < formData.data_inizio_validita) {
      setError('La data di fine validità deve essere successiva alla data di inizio');
      return false;
    }

    // Scaglioni validation
    if (formData.tipo_calcolo === 'SCAGLIONI') {
      for (const scaglione of scaglioni) {
        if (!scaglione.notte_da || !scaglione.importo) {
          setError('Tutti gli scaglioni devono avere notte_da e importo compilati');
          return false;
        }
        if (scaglione.notte_a && parseInt(scaglione.notte_a) < parseInt(scaglione.notte_da)) {
          setError('notte_a deve essere >= notte_da');
          return false;
        }
      }
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      // Prepare data
      const submitData = {
        comune_id: parseInt(formData.comune_id),
        comune_nome: formData.comune_nome,
        tipo_calcolo: formData.tipo_calcolo,
        importo_fisso: formData.importo_fisso ? parseFloat(formData.importo_fisso) : null,
        percentuale: formData.percentuale ? parseFloat(formData.percentuale) : null,
        eta_minima: parseInt(formData.eta_minima) || 0,
        eta_massima: formData.eta_massima ? parseInt(formData.eta_massima) : null,
        notti_max: formData.notti_max ? parseInt(formData.notti_max) : null,
        data_inizio_validita: formData.data_inizio_validita,
        data_fine_validita: formData.data_fine_validita || null,
        attiva: formData.attiva,
        note: formData.note || null
      };

      if (config && config.id) {
        // Update existing
        await tasseAPI.updateConfig(config.id, submitData);
      } else {
        // Create new
        if (formData.tipo_calcolo === 'SCAGLIONI' && scaglioni.length > 0) {
          // Create with scaglioni in one request
          await tasseAPI.createConfigWithScaglioni({
            ...submitData,
            scaglioni: scaglioni.map(s => ({
              notte_da: parseInt(s.notte_da),
              notte_a: s.notte_a ? parseInt(s.notte_a) : null,
              importo: parseFloat(s.importo)
            }))
          });
        } else {
          // Create without scaglioni
          await tasseAPI.createConfig(submitData);
        }
      }

      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore nel salvataggio della configurazione');
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{config ? 'Modifica Configurazione' : 'Nuova Configurazione'}</h2>
          <button onClick={onClose} className="btn btn-sm btn-secondary">✕</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && <div className="error">{error}</div>}

            <div className="form-row">
              <div className="form-group">
                <label>Comune ID *</label>
                <input
                  type="number"
                  name="comune_id"
                  value={formData.comune_id}
                  onChange={handleChange}
                  required
                  disabled={config && config.id}
                />
              </div>

              <div className="form-group">
                <label>Nome Comune *</label>
                <input
                  type="text"
                  name="comune_nome"
                  value={formData.comune_nome}
                  onChange={handleChange}
                  required
                  maxLength={200}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Tipo Calcolo *</label>
              <select
                name="tipo_calcolo"
                value={formData.tipo_calcolo}
                onChange={handleChange}
                required
              >
                <option value="FISSO">Fisso (importo per notte per persona)</option>
                <option value="PERCENTUALE">Percentuale (% del prezzo notte)</option>
                <option value="SCAGLIONI">Scaglioni (tariffe progressive)</option>
              </select>
            </div>

            {formData.tipo_calcolo === 'FISSO' && (
              <div className="form-group">
                <label>Importo Fisso (€) *</label>
                <input
                  type="number"
                  name="importo_fisso"
                  value={formData.importo_fisso}
                  onChange={handleChange}
                  step="0.01"
                  min="0"
                  required
                />
                <div className="form-help">Importo per notte per persona</div>
              </div>
            )}

            {formData.tipo_calcolo === 'PERCENTUALE' && (
              <div className="form-group">
                <label>Percentuale (%) *</label>
                <input
                  type="number"
                  name="percentuale"
                  value={formData.percentuale}
                  onChange={handleChange}
                  step="0.01"
                  min="0"
                  max="100"
                  required
                />
                <div className="form-help">Percentuale del prezzo notte</div>
              </div>
            )}

            {formData.tipo_calcolo === 'SCAGLIONI' && (
              <div className="form-group">
                <label>Scaglioni *</label>
                <div className="scaglioni-editor">
                  {scaglioni.map((scaglione, index) => (
                    <div key={index} className="scaglione-row">
                      <input
                        type="number"
                        placeholder="Notte da"
                        value={scaglione.notte_da}
                        onChange={(e) => handleScaglioneChange(index, 'notte_da', e.target.value)}
                        min="1"
                        required
                      />
                      <input
                        type="number"
                        placeholder="Notte a (opzionale)"
                        value={scaglione.notte_a}
                        onChange={(e) => handleScaglioneChange(index, 'notte_a', e.target.value)}
                        min="1"
                      />
                      <input
                        type="number"
                        placeholder="Importo €"
                        value={scaglione.importo}
                        onChange={(e) => handleScaglioneChange(index, 'importo', e.target.value)}
                        step="0.01"
                        min="0"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => removeScaglione(index)}
                        className="btn btn-sm btn-danger"
                      >
                        Rimuovi
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={addScaglione}
                    className="btn btn-sm btn-secondary"
                  >
                    + Aggiungi Scaglione
                  </button>
                </div>
                <div className="form-help">
                  Lascia "Notte a" vuoto per l'ultimo scaglione (infinito)
                </div>
              </div>
            )}

            <div className="form-row">
              <div className="form-group">
                <label>Età Minima</label>
                <input
                  type="number"
                  name="eta_minima"
                  value={formData.eta_minima}
                  onChange={handleChange}
                  min="0"
                  max="120"
                />
                <div className="form-help">Sotto questa età sono esenti</div>
              </div>

              <div className="form-group">
                <label>Età Massima (opzionale)</label>
                <input
                  type="number"
                  name="eta_massima"
                  value={formData.eta_massima}
                  onChange={handleChange}
                  min="0"
                  max="120"
                />
                <div className="form-help">Sopra questa età sono esenti</div>
              </div>

              <div className="form-group">
                <label>Notti Max Tassabili (opzionale)</label>
                <input
                  type="number"
                  name="notti_max"
                  value={formData.notti_max}
                  onChange={handleChange}
                  min="1"
                  max="365"
                />
                <div className="form-help">Massimo notti soggette a tassa</div>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Data Inizio Validità *</label>
                <input
                  type="date"
                  name="data_inizio_validita"
                  value={formData.data_inizio_validita}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Data Fine Validità (opzionale)</label>
                <input
                  type="date"
                  name="data_fine_validita"
                  value={formData.data_fine_validita}
                  onChange={handleChange}
                />
                <div className="form-help">Lascia vuoto per configurazione attiva indefinitamente</div>
              </div>
            </div>

            <div className="form-group">
              <div className="checkbox-group">
                <input
                  type="checkbox"
                  name="attiva"
                  id="attiva"
                  checked={formData.attiva}
                  onChange={handleChange}
                />
                <label htmlFor="attiva">Configurazione attiva</label>
              </div>
            </div>

            <div className="form-group">
              <label>Note (opzionale)</label>
              <textarea
                name="note"
                value={formData.note}
                onChange={handleChange}
                rows={3}
                placeholder="Note su regolamento comunale, esenzioni speciali, etc."
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn btn-secondary" disabled={submitting}>
              Annulla
            </button>
            <button type="submit" className="btn btn-success" disabled={submitting}>
              {submitting ? 'Salvataggio...' : (config ? 'Aggiorna' : 'Crea')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default TassaConfigForm;
