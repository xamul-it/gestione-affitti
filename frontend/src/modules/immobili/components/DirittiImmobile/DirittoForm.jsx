import { useState, useEffect } from 'react';
import { dirittiImmobileAPI, proprietariAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';

const TIPI_DIRITTO = [
  { value: 'PROPRIETARIO', label: 'Proprietario' },
  { value: 'COMPROPRIETARIO', label: 'Comproprietario' },
  { value: 'USUFRUTTUARIO', label: 'Usufruttuario' },
  { value: 'NUDA_PROPRIETA', label: 'Nuda Proprietà' },
  { value: 'ALTRO', label: 'Altro' }
];

function DirittoForm({ immobileId, onClose, onComplete }) {
  const [proprietari, setProprietari] = useState([]);
  const [formData, setFormData] = useState({
    proprietario_id: '',
    tipo_diritto: 'PROPRIETARIO',
    quota_percentuale: '',
    data_inizio: '',
    data_fine: '',
    note: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchProprietari();
  }, []);

  const fetchProprietari = async () => {
    try {
      const response = await proprietariAPI.getAll(true); // solo attivi
      setProprietari(response.data);
    } catch (err) {
      console.error('Errore nel caricamento dei proprietari:', err);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.proprietario_id) {
      setError('Seleziona un proprietario');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const dataToSend = {
        immobile_id: immobileId,
        proprietario_id: parseInt(formData.proprietario_id),
        tipo_diritto: formData.tipo_diritto,
        quota_percentuale: formData.quota_percentuale ? parseFloat(formData.quota_percentuale) : null,
        data_inizio: formData.data_inizio || null,
        data_fine: formData.data_fine || null,
        note: formData.note || null
      };

      await dirittiImmobileAPI.create(dataToSend);
      onComplete();
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content diritto-form-modal">
        <h3>Aggiungi Diritto</h3>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Proprietario *</label>
            <select
              name="proprietario_id"
              value={formData.proprietario_id}
              onChange={handleChange}
              required
            >
              <option value="">Seleziona proprietario...</option>
              {proprietari.map(prop => (
                <option key={prop.id} value={prop.id}>
                  {prop.nome} {prop.cognome} - {prop.codice_fiscale}
                </option>
              ))}
            </select>
            {proprietari.length === 0 && (
              <small className="form-hint">Nessun proprietario disponibile. Creane uno nella sezione Proprietari.</small>
            )}
          </div>

          <div className="form-group">
            <label>Tipo Diritto *</label>
            <select
              name="tipo_diritto"
              value={formData.tipo_diritto}
              onChange={handleChange}
              required
            >
              {TIPI_DIRITTO.map(tipo => (
                <option key={tipo.value} value={tipo.value}>
                  {tipo.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Quota Percentuale (%)</label>
            <input
              type="number"
              name="quota_percentuale"
              value={formData.quota_percentuale}
              onChange={handleChange}
              min="0"
              max="100"
              step="0.01"
              placeholder="es. 50.00 per 50%"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Data Inizio</label>
              <input
                type="date"
                name="data_inizio"
                value={formData.data_inizio}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Data Fine</label>
              <input
                type="date"
                name="data_fine"
                value={formData.data_fine}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Note</label>
            <textarea
              name="note"
              value={formData.note}
              onChange={handleChange}
              rows="3"
              placeholder="Note aggiuntive"
            />
          </div>

          <div className="form-actions">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
              disabled={loading}
            >
              Annulla
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Salvataggio...' : 'Aggiungi'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default DirittoForm;
