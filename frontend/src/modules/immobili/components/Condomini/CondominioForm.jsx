import { useState, useEffect } from 'react';
import { condominAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';

function CondominioForm({ condominio, onClose }) {
  const [formData, setFormData] = useState({
    nome: '',
    codice: '',
    indirizzo: '',
    citta: '',
    cap: '',
    provincia: '',
    codice_fiscale: '',
    partita_iva: '',
    amministratore_nome: '',
    amministratore_telefono: '',
    amministratore_email: '',
    amministratore_indirizzo: '',
    iban: '',
    note: '',
    attivo: true,
  });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (condominio) {
      setFormData(condominio);
    }
  }, [condominio]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (condominio) {
        await condominAPI.update(condominio.id, formData);
      } else {
        await condominAPI.create(formData);
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
      <div className="modal-content large">
        <div className="modal-header">
          <h2>{condominio ? 'Modifica Condominio' : 'Nuovo Condominio'}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {error && <div className="error">{error}</div>}
        {success && <div className="success">Operazione completata con successo!</div>}

        <form onSubmit={handleSubmit}>
          <h3>Dati Condominio</h3>
          <div className="form-row">
            <div className="form-group">
              <label>Codice *</label>
              <input
                type="text"
                name="codice"
                value={formData.codice}
                onChange={handleChange}
                required
              />
            </div>
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
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Indirizzo *</label>
              <input
                type="text"
                name="indirizzo"
                value={formData.indirizzo}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Città *</label>
              <input
                type="text"
                name="citta"
                value={formData.citta}
                onChange={handleChange}
                required
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

          <div className="form-row">
            <div className="form-group">
              <label>Codice Fiscale</label>
              <input
                type="text"
                name="codice_fiscale"
                value={formData.codice_fiscale}
                onChange={handleChange}
                maxLength="16"
              />
            </div>
            <div className="form-group">
              <label>Partita IVA</label>
              <input
                type="text"
                name="partita_iva"
                value={formData.partita_iva}
                onChange={handleChange}
                maxLength="11"
              />
            </div>
          </div>

          <h3>Dati Amministratore</h3>
          <div className="form-row">
            <div className="form-group">
              <label>Nome Amministratore</label>
              <input
                type="text"
                name="amministratore_nome"
                value={formData.amministratore_nome}
                onChange={handleChange}
              />
            </div>
            <div className="form-group">
              <label>Telefono</label>
              <input
                type="text"
                name="amministratore_telefono"
                value={formData.amministratore_telefono}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                name="amministratore_email"
                value={formData.amministratore_email}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Indirizzo Amministratore</label>
              <input
                type="text"
                name="amministratore_indirizzo"
                value={formData.amministratore_indirizzo}
                onChange={handleChange}
              />
            </div>
          </div>

          <h3>Dati Bancari</h3>
          <div className="form-row">
            <div className="form-group">
              <label>IBAN</label>
              <input
                type="text"
                name="iban"
                value={formData.iban}
                onChange={handleChange}
                maxLength="34"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group full-width">
              <label>Note</label>
              <textarea
                name="note"
                value={formData.note}
                onChange={handleChange}
                rows="3"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="attivo"
                  checked={formData.attivo}
                  onChange={handleChange}
                />
                Condominio Attivo
              </label>
            </div>
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

export default CondominioForm;
