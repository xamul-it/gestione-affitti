import { useState, useEffect } from 'react';
import { terreniAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';

const TIPOLOGIE_TERRENO = [
  { value: 'AGR', label: 'Agricolo', description: 'Terreno agricolo o coltivabile' },
  { value: 'EDI', label: 'Edificabile', description: 'Terreno edificabile per costruzioni' },
  { value: 'BOS', label: 'Bosco/Forestale', description: 'Terreno boschivo, forestale' },
  { value: 'IND', label: 'Industriale', description: 'Terreno destinato ad uso industriale/artigianale' },
  { value: 'ALT', label: 'Altro', description: 'Qualsiasi altra tipologia di terreno' },
];

function TerrenoForm({ terreno, onClose }) {
  const [formData, setFormData] = useState({
    codice: '',
    nome: '',
    descrizione: '',
    tipologia: 'AGR',
    indirizzo: '',
    comune: '',
    cap: '',
    provincia: '',
    nazione: 'Italia',
    superficie: '',
    unita_misura_superficie: 'mq',
    sezione_catastale: '',
    foglio: '',
    particella: '',
    subalterno: '',
    qualita_coltura: '',
    classe_catastale: '',
    reddito_dominicale: '',
    reddito_agrario: '',
    note: '',
    attivo: true,
  });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (terreno) {
      setFormData({
        ...terreno,
        superficie: terreno.superficie || '',
        reddito_dominicale: terreno.reddito_dominicale || '',
        reddito_agrario: terreno.reddito_agrario || '',
      });
    }
  }, [terreno]);

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
      // Clean data: convert empty strings to null for optional/numeric fields
      const cleanedData = {
        ...formData,
        superficie: formData.superficie === '' ? null : parseFloat(formData.superficie),
        reddito_dominicale: formData.reddito_dominicale === '' ? null : formData.reddito_dominicale,
        reddito_agrario: formData.reddito_agrario === '' ? null : formData.reddito_agrario,
        descrizione: formData.descrizione || null,
        indirizzo: formData.indirizzo || null,
        cap: formData.cap || null,
        sezione_catastale: formData.sezione_catastale || null,
        foglio: formData.foglio || null,
        particella: formData.particella || null,
        subalterno: formData.subalterno || null,
        qualita_coltura: formData.qualita_coltura || null,
        classe_catastale: formData.classe_catastale || null,
        note: formData.note || null,
      };

      if (terreno) {
        await terreniAPI.update(terreno.id, cleanedData);
      } else {
        await terreniAPI.create(cleanedData);
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
          <h2>{terreno ? 'Modifica Terreno' : 'Nuovo Terreno'}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {error && <div className="error">{error}</div>}
        {success && <div className="success">Operazione completata con successo!</div>}

        <form onSubmit={handleSubmit}>
          {/* Sezione Identificazione */}
          <h3 className="section-title">Identificazione</h3>
          <div className="form-row">
            <div className="form-group">
              <label>Codice *</label>
              <input
                type="text"
                name="codice"
                value={formData.codice}
                onChange={handleChange}
                placeholder="es. TER-001"
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
                placeholder="Nome descrittivo del terreno"
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Tipologia *</label>
              <select
                name="tipologia"
                value={formData.tipologia}
                onChange={handleChange}
                required
              >
                {TIPOLOGIE_TERRENO.map((tipo) => (
                  <option key={tipo.value} value={tipo.value}>
                    {tipo.label} - {tipo.description}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Stato</label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="attivo"
                  checked={formData.attivo}
                  onChange={handleChange}
                />
                Attivo
              </label>
            </div>
          </div>

          <div className="form-group">
            <label>Descrizione</label>
            <textarea
              name="descrizione"
              value={formData.descrizione}
              onChange={handleChange}
              rows="2"
              placeholder="Descrizione estesa del terreno"
            />
          </div>

          {/* Sezione Ubicazione */}
          <h3 className="section-title">Ubicazione</h3>
          <div className="form-group">
            <label>Indirizzo / Località</label>
            <input
              type="text"
              name="indirizzo"
              value={formData.indirizzo}
              onChange={handleChange}
              placeholder="es. Località Le Vigne, snc"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Comune *</label>
              <input
                type="text"
                name="comune"
                value={formData.comune}
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
                maxLength="5"
              />
            </div>

            <div className="form-group">
              <label>Provincia *</label>
              <input
                type="text"
                name="provincia"
                value={formData.provincia}
                onChange={handleChange}
                maxLength="2"
                placeholder="es. TO"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Nazione</label>
            <input
              type="text"
              name="nazione"
              value={formData.nazione}
              onChange={handleChange}
            />
          </div>

          {/* Sezione Caratteristiche Fisiche */}
          <h3 className="section-title">Caratteristiche Fisiche</h3>
          <div className="form-row">
            <div className="form-group">
              <label>Superficie *</label>
              <input
                type="number"
                name="superficie"
                value={formData.superficie}
                onChange={handleChange}
                step="0.01"
                min="0"
                required
              />
            </div>

            <div className="form-group">
              <label>Unità di misura</label>
              <select
                name="unita_misura_superficie"
                value={formData.unita_misura_superficie}
                onChange={handleChange}
              >
                <option value="mq">mq (metri quadri)</option>
                <option value="ha">ha (ettari)</option>
              </select>
            </div>
          </div>

          {/* Sezione Dati Catastali */}
          <h3 className="section-title">Dati Catastali</h3>
          <div className="form-row">
            <div className="form-group">
              <label>Sezione Catastale</label>
              <input
                type="text"
                name="sezione_catastale"
                value={formData.sezione_catastale}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Foglio</label>
              <input
                type="text"
                name="foglio"
                value={formData.foglio}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Particella</label>
              <input
                type="text"
                name="particella"
                value={formData.particella}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Subalterno</label>
              <input
                type="text"
                name="subalterno"
                value={formData.subalterno}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Qualità Coltura</label>
              <input
                type="text"
                name="qualita_coltura"
                value={formData.qualita_coltura}
                onChange={handleChange}
                placeholder="es. Seminativo, Vigneto, Uliveto"
              />
            </div>

            <div className="form-group">
              <label>Classe Catastale</label>
              <input
                type="text"
                name="classe_catastale"
                value={formData.classe_catastale}
                onChange={handleChange}
              />
            </div>
          </div>

          {/* Sezione Valori Fiscali */}
          <h3 className="section-title">Valori Fiscali</h3>
          <div className="form-row">
            <div className="form-group">
              <label>Reddito Dominicale (€)</label>
              <input
                type="number"
                name="reddito_dominicale"
                value={formData.reddito_dominicale}
                onChange={handleChange}
                step="0.01"
                min="0"
              />
            </div>

            <div className="form-group">
              <label>Reddito Agrario (€)</label>
              <input
                type="number"
                name="reddito_agrario"
                value={formData.reddito_agrario}
                onChange={handleChange}
                step="0.01"
                min="0"
              />
            </div>
          </div>

          {/* Note */}
          <div className="form-group">
            <label>Note</label>
            <textarea
              name="note"
              value={formData.note}
              onChange={handleChange}
              rows="3"
              placeholder="Annotazioni aggiuntive sul terreno"
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

export default TerrenoForm;
