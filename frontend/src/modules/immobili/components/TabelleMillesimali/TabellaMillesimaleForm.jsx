import { useState, useEffect } from 'react';
import { tabelleMillesimaliAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';

function TabellaMillesimaleForm({ tabella, condomini, onClose }) {
  const [formData, setFormData] = useState({
    condominio_id: '',
    nome: '',
    codice: '',
    tipo_ripartizione: 'millesimi',
    percentuale_millesimi: 100,
    percentuale_consumo: 0,
    percentuale_occupanti: 0,
    descrizione: '',
    note: '',
    attiva: true,
  });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (tabella) {
      setFormData(tabella);
    }
  }, [tabella]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    let newValue = type === 'checkbox' ? checked : value;

    if (type === 'number') {
      newValue = parseFloat(value) || 0;
    }

    setFormData(prev => ({
      ...prev,
      [name]: newValue
    }));
  };

  const handleTipoChange = (e) => {
    const tipo = e.target.value;
    let newData = {
      tipo_ripartizione: tipo,
      percentuale_millesimi: 100,
      percentuale_consumo: 0,
      percentuale_occupanti: 0,
    };

    // Preset percentuali per riscaldamento (millesimi_consumo)
    if (tipo === 'millesimi_consumo') {
      newData.percentuale_millesimi = 30;
      newData.percentuale_consumo = 70;
    }

    setFormData(prev => ({
      ...prev,
      ...newData
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validazione percentuali
    const totale = formData.percentuale_millesimi + formData.percentuale_consumo + formData.percentuale_occupanti;
    if (Math.abs(totale - 100) > 0.01) {
      setError('La somma delle percentuali deve essere 100%');
      return;
    }

    try {
      if (tabella) {
        await tabelleMillesimaliAPI.update(tabella.id, formData);
      } else {
        await tabelleMillesimaliAPI.create(formData);
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
          <h2>{tabella ? 'Modifica Tabella Millesimale' : 'Nuova Tabella Millesimale'}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {error && <div className="error">{error}</div>}
        {success && <div className="success">Operazione completata con successo!</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label>Condominio *</label>
              <select
                name="condominio_id"
                value={formData.condominio_id}
                onChange={handleChange}
                required
              >
                <option value="">Seleziona condominio</option>
                {condomini.map((cond) => (
                  <option key={cond.id} value={cond.id}>
                    {cond.nome}
                  </option>
                ))}
              </select>
            </div>
          </div>

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
                placeholder="es. Spese Generali, Ascensore, Riscaldamento"
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Tipo Ripartizione *</label>
              <select
                name="tipo_ripartizione"
                value={formData.tipo_ripartizione}
                onChange={handleTipoChange}
                required
              >
                <option value="millesimi">Millesimi (puri)</option>
                <option value="millesimi_consumo">Millesimi + Consumo (es. riscaldamento)</option>
                <option value="occupanti">Occupanti (es. acqua)</option>
                <option value="millesimi_piano">Millesimi + Piano (ascensore)</option>
                <option value="personalizzata">Personalizzata (quote fisse)</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Percentuale Millesimi</label>
              <input
                type="number"
                name="percentuale_millesimi"
                value={formData.percentuale_millesimi}
                onChange={handleChange}
                min="0"
                max="100"
                step="0.1"
              />
            </div>
            <div className="form-group">
              <label>Percentuale Consumo</label>
              <input
                type="number"
                name="percentuale_consumo"
                value={formData.percentuale_consumo}
                onChange={handleChange}
                min="0"
                max="100"
                step="0.1"
              />
            </div>
            <div className="form-group">
              <label>Percentuale Occupanti</label>
              <input
                type="number"
                name="percentuale_occupanti"
                value={formData.percentuale_occupanti}
                onChange={handleChange}
                min="0"
                max="100"
                step="0.1"
              />
            </div>
          </div>

          <div className="info-box">
            <strong>Totale: {(formData.percentuale_millesimi + formData.percentuale_consumo + formData.percentuale_occupanti).toFixed(1)}%</strong>
            {Math.abs((formData.percentuale_millesimi + formData.percentuale_consumo + formData.percentuale_occupanti) - 100) > 0.01 && (
              <span className="warning"> (deve essere 100%)</span>
            )}
          </div>

          <div className="form-row">
            <div className="form-group full-width">
              <label>Descrizione</label>
              <textarea
                name="descrizione"
                value={formData.descrizione}
                onChange={handleChange}
                rows="2"
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
                rows="2"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="attiva"
                  checked={formData.attiva}
                  onChange={handleChange}
                />
                Tabella Attiva
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

export default TabellaMillesimaleForm;
