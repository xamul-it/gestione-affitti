import { useState, useEffect } from 'react';
import { tecniciAPI } from '../../services/affittiAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import DocumentiSection from '../Documenti/DocumentiSection';

const SPECIALIZZAZIONI = [
  { value: 'ELETTRICISTA', label: 'Elettricista' },
  { value: 'IDRAULICO', label: 'Idraulico' },
  { value: 'TERMOTECNICO', label: 'Termotecnico' },
  { value: 'GEOMETRA', label: 'Geometra' },
  { value: 'ARCHITETTO', label: 'Architetto' },
  { value: 'INGEGNERE', label: 'Ingegnere' },
  { value: 'CERTIFICATORE_ENERGETICO', label: 'Certificatore Energetico' },
  { value: 'MANUTENTORE_CALDAIE', label: 'Manutentore Caldaie' },
  { value: 'ALTRO', label: 'Altro' }
];

function TecnicoForm({ tecnico, onClose }) {
  const [formData, setFormData] = useState({
    nome: '',
    cognome: '',
    ragione_sociale: '',
    specializzazione: 'CERTIFICATORE_ENERGETICO',
    partita_iva: '',
    codice_fiscale: '',
    telefono: '',
    email: '',
    indirizzo: '',
    note: '',
    attivo: true
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (tecnico) {
      setFormData(tecnico);
    }
  }, [tecnico]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (tecnico) {
        await tecniciAPI.update(tecnico.id, formData);
      } else {
        await tecniciAPI.create(formData);
      }
      onClose();
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>{tecnico ? 'Modifica Tecnico' : 'Nuovo Tecnico'}</h2>
        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label>Nome *</label>
              <input
                type="text"
                name="nome"
                value={formData.nome}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-group">
              <label>Cognome *</label>
              <input
                type="text"
                name="cognome"
                value={formData.cognome}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Ragione Sociale</label>
            <input
              type="text"
              name="ragione_sociale"
              value={formData.ragione_sociale}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label>Specializzazione *</label>
            <select
              name="specializzazione"
              value={formData.specializzazione}
              onChange={handleChange}
              required
            >
              {SPECIALIZZAZIONI.map(spec => (
                <option key={spec.value} value={spec.value}>{spec.label}</option>
              ))}
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Partita IVA</label>
              <input
                type="text"
                name="partita_iva"
                value={formData.partita_iva}
                onChange={handleChange}
              />
            </div>
            <div className="form-group">
              <label>Codice Fiscale</label>
              <input
                type="text"
                name="codice_fiscale"
                value={formData.codice_fiscale}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Telefono</label>
              <input
                type="tel"
                name="telefono"
                value={formData.telefono}
                onChange={handleChange}
              />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Indirizzo</label>
            <input
              type="text"
              name="indirizzo"
              value={formData.indirizzo}
              onChange={handleChange}
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

          <div className="form-group">
            <label>
              <input
                type="checkbox"
                name="attivo"
                checked={formData.attivo}
                onChange={handleChange}
              />
              Attivo
            </label>
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

        <DocumentiSection entityType="TECNICO" entityId={tecnico?.id} />
      </div>
    </div>
  );
}

export default TecnicoForm;
