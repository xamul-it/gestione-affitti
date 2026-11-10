import { Button } from '../../../../components/UI';
import { useState, useEffect } from 'react';
import { tipologieTerrenoAPI } from '../../services/immobiliAPI';
import '../CategorieCatastali/CategorieCatastali.css';

function TipologiaTerrenoForm({ tipologia, onClose }) {
  const [formData, setFormData] = useState({
    codice: '',
    nome: '',
    descrizione: '',
    ordinamento: 0,
    attiva: true,
  });
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (tipologia) {
      setFormData({
        codice: tipologia.codice || '',
        nome: tipologia.nome || '',
        descrizione: tipologia.descrizione || '',
        ordinamento: tipologia.ordinamento ?? 0,
        attiva: tipologia.attiva ?? true,
      });
    }
  }, [tipologia]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const payload = {
        ...formData,
        codice: formData.codice.trim().toUpperCase(),
        ordinamento: formData.ordinamento === '' ? 0 : Number(formData.ordinamento),
      };
      if (tipologia) {
        await tipologieTerrenoAPI.update(tipologia.id, payload);
      } else {
        await tipologieTerrenoAPI.create(payload);
      }
      onClose();
    } catch (err) {
      setError('Errore nel salvataggio della tipologia terreno');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>{tipologia ? 'Modifica Tipologia Terreno' : 'Nuova Tipologia Terreno'}</h2>
          <Button type="button" variant="ghost" size="sm" aria-label="Chiudi" onClick={onClose}>×</Button>
        </div>

        {error && <div className="error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label>Codice *</label>
              <input
                type="text"
                name="codice"
                value={formData.codice}
                onChange={handleChange}
                required
                maxLength="10"
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
                maxLength="100"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Descrizione</label>
            <textarea
              name="descrizione"
              value={formData.descrizione}
              onChange={handleChange}
              rows="3"
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
                min="0"
              />
            </div>
            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="attiva"
                  checked={formData.attiva}
                  onChange={handleChange}
                />
                Attiva
              </label>
            </div>
          </div>

          <div className="modal-actions">
            <Button type="button" variant="secondary" onClick={onClose}>
              Annulla
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? 'Salvataggio...' : 'Salva'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default TipologiaTerrenoForm;
