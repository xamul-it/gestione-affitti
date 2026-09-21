import { useState, useEffect } from 'react';
import { unitaImmobiliariAPI, categorieCatastaliAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import DocumentiSection from '../../../../components/Documenti/DocumentiSection';
import DirittiImmobileSection from '../DirittiImmobile/DirittiImmobileSection';

// Mapping categorie catastali a tipi default
const CATEGORIA_TIPO_MAP = {
  'A/1': 'Abitazione signorile',
  'A/2': 'Abitazione civile',
  'A/3': 'Abitazione economica',
  'A/4': 'Abitazione popolare',
  'A/5': 'Abitazione ultrapopolare',
  'A/6': 'Abitazione rurale',
  'A/7': 'Villino',
  'A/8': 'Villa',
  'A/9': 'Castello',
  'A/10': 'Ufficio',
  'A/11': 'Abitazione tipica',
  'B/1': 'Collegio',
  'B/2': 'Casa di cura',
  'B/3': 'Prigione',
  'B/4': 'Ufficio pubblico',
  'B/5': 'Scuola',
  'B/6': 'Biblioteca',
  'B/7': 'Cappella',
  'B/8': 'Magazzino sotterraneo',
  'C/1': 'Negozio',
  'C/2': 'Magazzino',
  'C/3': 'Laboratorio',
  'C/4': 'Fabbricato sportivo',
  'C/5': 'Stabilimento balneare',
  'C/6': 'Garage',
  'C/7': 'Tettoia',
  'D/1': 'Opificio',
  'D/2': 'Albergo',
  'D/3': 'Teatro',
  'D/4': 'Casa di cura privata',
  'D/5': 'Banca',
  'D/6': 'Fabbricato sportivo',
  'D/7': 'Fabbricato industriale',
  'D/8': 'Fabbricato commerciale',
  'D/9': 'Edificio galleggiante',
  'D/10': 'Fabbricato agricolo',
  'E/1': 'Stazione',
  'E/2': 'Ponte privato',
  'E/3': 'Costruzione cimiteriale',
  'E/4': 'Fabbricato per esercizi sportivi',
  'E/5': 'Fabbricato costituente fortificazione',
  'E/6': 'Faro',
  'E/7': 'Fabbricato per culto',
  'E/8': 'Fabbricato cimiteriale',
  'E/9': 'Edificio a destinazione particolare',
  'F/1': 'Area urbana',
  'F/2': 'Unità collabente',
  'F/3': 'Unità in corso di costruzione',
  'F/4': 'Unità in corso di definizione',
  'F/5': 'Lastrici solari',
};

function UnitaImmobiliareForm({ unitaImmobiliare, onClose }) {
  const [formData, setFormData] = useState({
    codice: '',
    tipo: '',
    categoria_catastale_id: '',
    indirizzo: '',
    citta: '',
    cap: '',
    provincia: '',
    superficie_mq: '',
    locali: '',
    piano: '',
    classe_energetica: '',
    rendita_catastale: '',
    foglio: '',
    particella: '',
    subalterno: '',
    descrizione: '',
    note: '',
  });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [categorieCatastali, setCategorieCatastali] = useState([]);

  useEffect(() => {
    if (unitaImmobiliare) {
      setFormData(unitaImmobiliare);
    }
  }, [unitaImmobiliare]);

  useEffect(() => {
    const fetchCategorie = async () => {
      try {
        const response = await categorieCatastaliAPI.getAll(true);
        setCategorieCatastali(response.data);
      } catch (err) {
        console.error('Error loading categorie catastali:', err);
      }
    };
    fetchCategorie();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handler speciale per la categoria catastale con inferenza automatica del tipo
  const handleCategoriaChange = (e) => {
    const categoriaId = e.target.value;

    if (categoriaId === '') {
      setFormData(prev => ({
        ...prev,
        categoria_catastale_id: ''
      }));
      return;
    }

    const categoria = categorieCatastali.find(cat => cat.id === parseInt(categoriaId));

    if (categoria) {
      const tipoDefault = CATEGORIA_TIPO_MAP[categoria.codice] || '';

      setFormData(prev => ({
        ...prev,
        categoria_catastale_id: categoriaId,
        // Solo popola il tipo se è vuoto o se vogliamo sovrascriverlo
        tipo: prev.tipo || tipoDefault
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Clean data: convert empty strings to null for numeric fields
      const cleanedData = {
        ...formData,
        superficie_mq: formData.superficie_mq === '' ? null : formData.superficie_mq,
        locali: formData.locali === '' ? null : formData.locali,
        rendita_catastale: formData.rendita_catastale === '' ? null : formData.rendita_catastale,
        condominio_id: formData.condominio_id === '' ? null : formData.condominio_id,
        categoria_catastale_id: formData.categoria_catastale_id === '' ? null : formData.categoria_catastale_id,
        // Convert string numbers to actual numbers
        ...(formData.superficie_mq !== '' && { superficie_mq: parseFloat(formData.superficie_mq) }),
        ...(formData.locali !== '' && { locali: parseInt(formData.locali) }),
        ...(formData.rendita_catastale !== '' && { rendita_catastale: parseFloat(formData.rendita_catastale) }),
        ...(formData.categoria_catastale_id !== '' && { categoria_catastale_id: parseInt(formData.categoria_catastale_id) }),
      };

      if (unitaImmobiliare) {
        await unitaImmobiliariAPI.update(unitaImmobiliare.id, cleanedData);
      } else {
        await unitaImmobiliariAPI.create(cleanedData);
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
          <h2>{unitaImmobiliare ? 'Modifica Unità Immobiliare' : 'Nuova Unità Immobiliare'}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {error && <div className="error">{error}</div>}
        {success && <div className="success">Operazione completata con successo!</div>}

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
              />
            </div>

            <div className="form-group">
              <label>Categoria Catastale *</label>
              <select
                name="categoria_catastale_id"
                value={formData.categoria_catastale_id}
                onChange={handleCategoriaChange}
                required
              >
                <option value="">Seleziona categoria catastale...</option>
                {categorieCatastali.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.codice} - {cat.nome}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Tipo</label>
            <input
              type="text"
              name="tipo"
              value={formData.tipo}
              onChange={handleChange}
              placeholder="Compilato automaticamente dalla categoria, puoi personalizzarlo"
            />
            <small style={{ display: 'block', marginTop: '4px', color: '#666', fontSize: '0.85em' }}>
              Compilato automaticamente dalla categoria catastale. Puoi modificarlo se necessario.
            </small>
          </div>

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
              <label>Superficie (mq)</label>
              <input
                type="number"
                name="superficie_mq"
                value={formData.superficie_mq}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Locali</label>
              <input
                type="number"
                name="locali"
                value={formData.locali}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label>Piano</label>
              <input
                type="text"
                name="piano"
                value={formData.piano}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Classe Energetica</label>
              <select name="classe_energetica" value={formData.classe_energetica} onChange={handleChange}>
                <option value="">Seleziona...</option>
                <option value="A+">A+</option>
                <option value="A">A</option>
                <option value="B">B</option>
                <option value="C">C</option>
                <option value="D">D</option>
                <option value="E">E</option>
                <option value="F">F</option>
                <option value="G">G</option>
              </select>
            </div>

            <div className="form-group">
              <label>Rendita Catastale</label>
              <input
                type="number"
                step="0.01"
                name="rendita_catastale"
                value={formData.rendita_catastale}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-row">
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

          <div className="form-group">
            <label>Descrizione</label>
            <textarea
              name="descrizione"
              value={formData.descrizione}
              onChange={handleChange}
              rows="3"
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

        <DirittiImmobileSection immobileId={unitaImmobiliare?.id} />
        <DocumentiSection entityType="IMMOBILE" entityId={unitaImmobiliare?.id} />
      </div>
    </div>
  );
}

export default UnitaImmobiliareForm;
