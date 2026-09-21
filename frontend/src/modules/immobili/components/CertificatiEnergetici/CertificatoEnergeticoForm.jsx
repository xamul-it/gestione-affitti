import { useState, useEffect } from 'react';
import { certificatiEnergeticiAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import DocumentiSection from '../../../../components/Documenti/DocumentiSection';

const CLASSI_ENERGETICHE = ['A4', 'A3', 'A2', 'A1', 'B', 'C', 'D', 'E', 'F', 'G'];

function CertificatoEnergeticoForm({ certificato, immobili, tecnici, onClose }) {
  const [formData, setFormData] = useState({
    immobile_id: '',
    tecnico_id: '',
    classe_energetica: 'A3',
    indice_prestazione_energetica: '',
    data_emissione: '',
    data_scadenza: '',
    numero_protocollo: '',
    file_path: '',
    note: ''
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (certificato) {
      setFormData(certificato);
    } else {
      // Set default dates
      const oggi = new Date();
      const scadenza = new Date();
      scadenza.setFullYear(oggi.getFullYear() + 10);

      setFormData(prev => ({
        ...prev,
        data_emissione: oggi.toISOString().split('T')[0],
        data_scadenza: scadenza.toISOString().split('T')[0]
      }));
    }
  }, [certificato]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Validation
    if (new Date(formData.data_emissione) >= new Date(formData.data_scadenza)) {
      setError('La data di scadenza deve essere successiva alla data di emissione');
      setLoading(false);
      return;
    }

    try {
      const submitData = {
        ...formData,
        immobile_id: parseInt(formData.immobile_id),
        tecnico_id: parseInt(formData.tecnico_id),
        indice_prestazione_energetica: formData.indice_prestazione_energetica ?
          parseFloat(formData.indice_prestazione_energetica) : null
      };

      if (certificato) {
        await certificatiEnergeticiAPI.update(certificato.id, submitData);
      } else {
        await certificatiEnergeticiAPI.create(submitData);
      }
      onClose();
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>{certificato ? 'Modifica Certificato Energetico' : 'Nuovo Certificato Energetico'}</h2>
        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label>Immobile *</label>
              <select
                name="immobile_id"
                value={formData.immobile_id}
                onChange={handleChange}
                required
              >
                <option value="">Seleziona immobile</option>
                {immobili.map(imm => (
                  <option key={imm.id} value={imm.id}>
                    {imm.codice} - {imm.indirizzo}, {imm.citta}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Tecnico Certificatore *</label>
              <select
                name="tecnico_id"
                value={formData.tecnico_id}
                onChange={handleChange}
                required
              >
                <option value="">Seleziona tecnico</option>
                {tecnici.map(tec => (
                  <option key={tec.id} value={tec.id}>
                    {tec.nome} {tec.cognome} - {tec.specializzazione}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Classe Energetica *</label>
              <select
                name="classe_energetica"
                value={formData.classe_energetica}
                onChange={handleChange}
                required
              >
                {CLASSI_ENERGETICHE.map(classe => (
                  <option key={classe} value={classe}>{classe}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>IPE (kWh/m²anno)</label>
              <input
                type="number"
                step="0.1"
                name="indice_prestazione_energetica"
                value={formData.indice_prestazione_energetica}
                onChange={handleChange}
                placeholder="es. 45.5"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Data Emissione *</label>
              <input
                type="date"
                name="data_emissione"
                value={formData.data_emissione}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-group">
              <label>Data Scadenza *</label>
              <input
                type="date"
                name="data_scadenza"
                value={formData.data_scadenza}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Numero Protocollo</label>
            <input
              type="text"
              name="numero_protocollo"
              value={formData.numero_protocollo}
              onChange={handleChange}
              placeholder="es. APE-2024-001"
            />
          </div>

          <div className="form-group">
            <label>Path File PDF</label>
            <input
              type="text"
              name="file_path"
              value={formData.file_path}
              onChange={handleChange}
              placeholder="/percorso/al/certificato.pdf"
            />
          </div>

          <div className="form-group">
            <label>Note</label>
            <textarea
              name="note"
              value={formData.note}
              onChange={handleChange}
              rows="3"
            />
          </div>

          <div className="form-actions">
            <button type="button" onClick={onClose} className="btn btn-secondary" disabled={loading}>
              Annulla
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Salvataggio...' : 'Salva'}
            </button>
          </div>
        </form>

        <DocumentiSection entityType="CERTIFICATO_ENERGETICO" entityId={certificato?.id} />
      </div>
    </div>
  );
}

export default CertificatoEnergeticoForm;
