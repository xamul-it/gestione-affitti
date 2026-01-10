import { useState, useEffect } from 'react';
import { speseAPI } from '../../services/affittiAPI';
import { formatApiError } from '../../../../utils/errorHandling';

function SpesaForm({ spesa, immobili, onClose }) {
  const [formData, setFormData] = useState({
    immobile_id: '',
    data: '',
    importo: '',
    categoria: 'manutenzione',
    descrizione: '',
    fornitore: '',
    numero_fattura: '',
    pagata: 0,
    data_pagamento: '',
    metodo_pagamento: '',
    note: '',
  });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (spesa) {
      setFormData(spesa);
    }
  }, [spesa]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (checked ? 1 : 0) : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const dataToSend = {
        ...formData,
        immobile_id: parseInt(formData.immobile_id),
        importo: parseFloat(formData.importo),
      };

      if (spesa) {
        await speseAPI.update(spesa.id, dataToSend);
      } else {
        await speseAPI.create(dataToSend);
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
          <h2>{spesa ? 'Modifica Spesa' : 'Nuova Spesa'}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {error && <div className="error">{error}</div>}
        {success && <div className="success">Operazione completata con successo!</div>}

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
                <option value="">Seleziona immobile...</option>
                {immobili.map(immobile => (
                  <option key={immobile.id} value={immobile.id}>
                    {immobile.codice} - {immobile.indirizzo}, {immobile.citta}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Data *</label>
              <input
                type="date"
                name="data"
                value={formData.data}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Categoria *</label>
              <select name="categoria" value={formData.categoria} onChange={handleChange} required>
                <option value="manutenzione">Manutenzione</option>
                <option value="utenze">Utenze</option>
                <option value="tasse">Tasse</option>
                <option value="assicurazione">Assicurazione</option>
                <option value="amministrazione">Amministrazione</option>
                <option value="ristrutturazione">Ristrutturazione</option>
                <option value="altro">Altro</option>
              </select>
            </div>

            <div className="form-group">
              <label>Importo *</label>
              <input
                type="number"
                step="0.01"
                name="importo"
                value={formData.importo}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Descrizione *</label>
            <input
              type="text"
              name="descrizione"
              value={formData.descrizione}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Fornitore</label>
              <input
                type="text"
                name="fornitore"
                value={formData.fornitore}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Numero Fattura</label>
              <input
                type="text"
                name="numero_fattura"
                value={formData.numero_fattura}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label>
              <input
                type="checkbox"
                name="pagata"
                checked={formData.pagata === 1}
                onChange={handleChange}
                style={{ width: 'auto', marginRight: '10px' }}
              />
              Pagata
            </label>
          </div>

          {formData.pagata === 1 && (
            <div className="form-row">
              <div className="form-group">
                <label>Data Pagamento</label>
                <input
                  type="date"
                  name="data_pagamento"
                  value={formData.data_pagamento}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group">
                <label>Metodo Pagamento</label>
                <select name="metodo_pagamento" value={formData.metodo_pagamento} onChange={handleChange}>
                  <option value="">Seleziona...</option>
                  <option value="Bonifico">Bonifico</option>
                  <option value="Contanti">Contanti</option>
                  <option value="Carta">Carta</option>
                  <option value="Assegno">Assegno</option>
                </select>
              </div>
            </div>
          )}

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
      </div>
    </div>
  );
}

export default SpesaForm;
