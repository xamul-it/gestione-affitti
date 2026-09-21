import { useState, useEffect } from 'react';
import { affittuariAPI } from '../../services/affittiAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import DocumentiSection from '../../../../components/Documenti/DocumentiSection';

function AffittuarioForm({ affittuario, onClose }) {
  const [formData, setFormData] = useState({
    nome: '',
    cognome: '',
    codice_fiscale: '',
    data_nascita: '',
    luogo_nascita: '',
    email: '',
    telefono: '',
    cellulare: '',
    indirizzo_residenza: '',
    citta_residenza: '',
    cap_residenza: '',
    provincia_residenza: '',
    note: '',
  });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (affittuario) {
      setFormData(affittuario);
    }
  }, [affittuario]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (affittuario) {
        await affittuariAPI.update(affittuario.id, formData);
      } else {
        await affittuariAPI.create(formData);
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

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>{affittuario ? 'Modifica Affittuario' : 'Nuovo Affittuario'}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {error && <div className="error">{error}</div>}
        {success && <div className="success">Operazione completata con successo!</div>}

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
            <label>Indirizzo Residenza</label>
            <input
              type="text"
              name="indirizzo_residenza"
              value={formData.indirizzo_residenza}
              onChange={handleChange}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Città Residenza</label>
              <input
                type="text"
                name="citta_residenza"
                value={formData.citta_residenza}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>CAP Residenza</label>
              <input
                type="text"
                name="cap_residenza"
                value={formData.cap_residenza}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Provincia Residenza</label>
              <input
                type="text"
                name="provincia_residenza"
                value={formData.provincia_residenza}
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

          <div className="btn-group">
            <button type="submit">Salva</button>
            <button type="button" className="secondary" onClick={onClose}>
              Annulla
            </button>
          </div>
        </form>

        <DocumentiSection entityType="AFFITTUARIO" entityId={affittuario?.id} />
      </div>
    </div>
  );
}

export default AffittuarioForm;
