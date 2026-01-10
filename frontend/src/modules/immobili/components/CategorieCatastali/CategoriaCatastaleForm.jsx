import { useState, useEffect } from 'react';
import { categorieCatastaliAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';

function CategoriaCatastaleForm({ categoria, onClose }) {
  const [formData, setFormData] = useState({
    codice: '',
    nome: '',
    gruppo: '',
    descrizione: '',
    ordinamento: '',
    attiva: true
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (categoria) {
      setFormData(categoria);
    }
  }, [categoria]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Clean data: convert empty strings to null for numeric fields
      const cleanedData = {
        ...formData,
        ordinamento: formData.ordinamento === '' ? null : parseInt(formData.ordinamento),
        gruppo: formData.gruppo === '' ? null : formData.gruppo,
        descrizione: formData.descrizione === '' ? null : formData.descrizione,
      };

      if (categoria) {
        await categorieCatastaliAPI.update(categoria.id, cleanedData);
      } else {
        await categorieCatastaliAPI.create(cleanedData);
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
          <h2>{categoria ? 'Modifica Categoria Catastale' : 'Nuova Categoria Catastale'}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label>Codice *</label>
              <input
                type="text"
                name="codice"
                value={formData.codice}
                onChange={handleChange}
                placeholder="es. A/2"
                maxLength="10"
                required
              />
              <small style={{ display: 'block', marginTop: '4px', color: '#666', fontSize: '0.85em' }}>
                Formato: lettera/numero (es. A/2, C/1, D/8)
              </small>
            </div>

            <div className="form-group">
              <label>Gruppo</label>
              <input
                type="text"
                name="gruppo"
                value={formData.gruppo}
                onChange={handleChange}
                placeholder="es. A"
                maxLength="2"
              />
              <small style={{ display: 'block', marginTop: '4px', color: '#666', fontSize: '0.85em' }}>
                Gruppo catastale (A, B, C, D, E, F)
              </small>
            </div>
          </div>

          <div className="form-group">
            <label>Nome *</label>
            <input
              type="text"
              name="nome"
              value={formData.nome}
              onChange={handleChange}
              placeholder="es. Abitazioni civili"
              required
            />
          </div>

          <div className="form-group">
            <label>Descrizione</label>
            <textarea
              name="descrizione"
              value={formData.descrizione}
              onChange={handleChange}
              rows="4"
              placeholder="Descrizione dettagliata della categoria catastale..."
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Ordinamento</label>
              <input
                type="number"
                name="ordinamento"
                value={formData.ordinamento}
                onChange={handleChange}
                placeholder="es. 10"
                min="0"
              />
              <small style={{ display: 'block', marginTop: '4px', color: '#666', fontSize: '0.85em' }}>
                Numero per ordinare le categorie nella lista
              </small>
            </div>

            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  name="attiva"
                  checked={formData.attiva}
                  onChange={handleChange}
                />
                Attiva
              </label>
              <small style={{ display: 'block', marginTop: '4px', color: '#666', fontSize: '0.85em' }}>
                Solo le categorie attive sono selezionabili
              </small>
            </div>
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

export default CategoriaCatastaleForm;
