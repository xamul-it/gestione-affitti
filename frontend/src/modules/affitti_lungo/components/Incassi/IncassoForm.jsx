import { useState, useEffect } from 'react';
import { incassiAPI } from '../../services/affittiAPI';
import { formatApiError } from '../../../../utils/errorHandling';

function IncassoForm({ incasso, contratti, onClose }) {
  const [formData, setFormData] = useState({
    contratto_id: '',
    data_incasso: '',
    importo: '',
    mese_riferimento: '',
    metodo_pagamento: '',
    numero_ricevuta: '',
    note: '',
  });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (incasso) {
      setFormData(incasso);
    }
  }, [incasso]);

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
      const dataToSend = {
        ...formData,
        contratto_id: parseInt(formData.contratto_id),
        importo: parseFloat(formData.importo),
      };

      if (incasso) {
        await incassiAPI.update(incasso.id, dataToSend);
      } else {
        await incassiAPI.create(dataToSend);
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
          <h2>{incasso ? 'Modifica Incasso' : 'Nuovo Incasso'}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {error && <div className="error">{error}</div>}
        {success && <div className="success">Operazione completata con successo!</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Contratto *</label>
            <select
              name="contratto_id"
              value={formData.contratto_id}
              onChange={handleChange}
              required
            >
              <option value="">Seleziona contratto...</option>
              {contratti.map(contratto => (
                <option key={contratto.id} value={contratto.id}>
                  {contratto.numero_contratto} - € {contratto.canone_mensile}
                </option>
              ))}
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Data Incasso *</label>
              <input
                type="date"
                name="data_incasso"
                value={formData.data_incasso}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Mese Riferimento * (YYYY-MM)</label>
              <input
                type="month"
                name="mese_riferimento"
                value={formData.mese_riferimento}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="form-row">
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

            <div className="form-group">
              <label>Metodo Pagamento</label>
              <select name="metodo_pagamento" value={formData.metodo_pagamento} onChange={handleChange}>
                <option value="">Seleziona...</option>
                <option value="Bonifico">Bonifico</option>
                <option value="Contanti">Contanti</option>
                <option value="Assegno">Assegno</option>
                <option value="RID">RID</option>
                <option value="Altro">Altro</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Numero Ricevuta</label>
            <input
              type="text"
              name="numero_ricevuta"
              value={formData.numero_ricevuta}
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

export default IncassoForm;
