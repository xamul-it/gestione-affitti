import { useState, useEffect } from 'react';
import {
  createRuoloAziendaTipo,
  updateRuoloAziendaTipo
} from '../../services/anagraficaAPI';
import './RuoliAziendaTipi.css';

function RuoloAziendaTipoForm({ ruolo, onClose }) {
  const [formData, setFormData] = useState({
    nome: '',
    descrizione: '',
    attivo: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (ruolo) {
      setFormData({
        nome: ruolo.nome || '',
        descrizione: ruolo.descrizione || '',
        attivo: ruolo.attivo !== undefined ? ruolo.attivo : true
      });
    }
  }, [ruolo]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.nome.trim()) {
      setError('Il nome è obbligatorio');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      if (ruolo) {
        await updateRuoloAziendaTipo(ruolo.id, formData);
      } else {
        await createRuoloAziendaTipo(formData);
      }

      onClose();
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError(ruolo ? 'Errore nell\'aggiornamento del ruolo' : 'Errore nella creazione del ruolo');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{ruolo ? 'Modifica Ruolo' : 'Nuovo Ruolo'}</h2>
          <button onClick={onClose} className="close-btn">×</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && <div className="error">{error}</div>}

            <div className="form-group">
              <label htmlFor="nome">Nome Ruolo *</label>
              <input
                type="text"
                id="nome"
                name="nome"
                value={formData.nome}
                onChange={handleChange}
                className="form-control"
                placeholder="es: Amministratore Delegato, Segretaria, Tecnico"
                required
                maxLength={100}
              />
              <small>Il nome deve essere univoco</small>
            </div>

            <div className="form-group">
              <label htmlFor="descrizione">Descrizione</label>
              <textarea
                id="descrizione"
                name="descrizione"
                value={formData.descrizione}
                onChange={handleChange}
                className="form-control"
                rows="3"
                placeholder="Descrizione opzionale del ruolo..."
                maxLength={500}
              />
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="attivo"
                  checked={formData.attivo}
                  onChange={handleChange}
                />
                Attivo (se disattivato, il ruolo non apparirà nell'autocomplete)
              </label>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn btn-secondary">
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

export default RuoloAziendaTipoForm;
