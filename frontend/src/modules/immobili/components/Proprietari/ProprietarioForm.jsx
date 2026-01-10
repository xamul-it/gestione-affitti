import { useState, useEffect } from 'react';
import { proprietariAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';

function ProprietarioForm({ proprietario, onClose }) {
  const [formData, setFormData] = useState({
    nome: '',
    cognome: '',
    codice_fiscale: '',
    data_nascita: '',
    luogo_nascita: '',
    email: '',
    telefono: '',
    cellulare: '',
    indirizzo: '',
    citta: '',
    cap: '',
    provincia: '',
    note: '',
    attivo: true
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (proprietario) {
      setFormData(proprietario);
    }
  }, [proprietario]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (proprietario) {
        await proprietariAPI.update(proprietario.id, formData);
      } else {
        await proprietariAPI.create(formData);
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
        <div className="modal-header">
          <h2>{proprietario ? 'Modifica Proprietario' : 'Nuovo Proprietario'}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

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
            <label>Codice Fiscale *</label>
            <input
              type="text"
              name="codice_fiscale"
              value={formData.codice_fiscale}
              onChange={handleChange}
              maxLength="16"
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Data di Nascita</label>
              <input
                type="date"
                name="data_nascita"
                value={formData.data_nascita}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Luogo di Nascita</label>
              <input
                type="text"
                name="luogo_nascita"
                value={formData.luogo_nascita}
                onChange={handleChange}
              />
            </div>
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
              <label>Cellulare</label>
              <input
                type="tel"
                name="cellulare"
                value={formData.cellulare}
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

          <div className="form-row">
            <div className="form-group">
              <label>Città</label>
              <input
                type="text"
                name="citta"
                value={formData.citta}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>CAP</label>
              <input
                type="text"
                name="cap"
                value={formData.cap}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Provincia</label>
              <input
                type="text"
                name="provincia"
                value={formData.provincia}
                onChange={handleChange}
                maxLength="2"
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
      </div>
    </div>
  );
}

export default ProprietarioForm;
