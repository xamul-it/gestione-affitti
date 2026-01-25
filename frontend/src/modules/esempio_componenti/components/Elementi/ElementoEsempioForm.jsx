/**
 * ElementoEsempioForm - Create/Edit Form Component
 *
 * Modal form for creating and editing elementi.
 * Demonstrates various field types and domain data dropdowns.
 */
import { useState, useEffect } from 'react';
import esempioAPI from '../../services/esempioAPI';
import './ElementoEsempioForm.css';

const STATI_OPTIONS = [
  { value: 'bozza', label: 'Bozza' },
  { value: 'attivo', label: 'Attivo' },
  { value: 'completato', label: 'Completato' },
  { value: 'annullato', label: 'Annullato' },
];

function ElementoEsempioForm({ elemento, onClose, onSave }) {
  const isEditing = !!elemento?.id;

  // Form state
  const [formData, setFormData] = useState({
    codice: '',
    titolo: '',
    descrizione: '',
    categoria_id: '',
    priorita_id: '',
    quantita: 1,
    importo: '',
    percentuale: '',
    data_inizio: '',
    data_fine: '',
    stato: 'bozza',
    attivo: true,
    note: '',
  });

  // Domain data for dropdowns
  const [categorie, setCategorie] = useState([]);
  const [priorita, setPriorita] = useState([]);

  // UI state
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Load domain data on mount
  useEffect(() => {
    loadDomainData();
  }, []);

  // Populate form when editing
  useEffect(() => {
    if (elemento) {
      setFormData({
        codice: elemento.codice || '',
        titolo: elemento.titolo || '',
        descrizione: elemento.descrizione || '',
        categoria_id: elemento.categoria_id || '',
        priorita_id: elemento.priorita_id || '',
        quantita: elemento.quantita || 1,
        importo: elemento.importo || '',
        percentuale: elemento.percentuale || '',
        data_inizio: elemento.data_inizio || '',
        data_fine: elemento.data_fine || '',
        stato: elemento.stato || 'bozza',
        attivo: elemento.attivo ?? true,
        note: elemento.note || '',
      });
    }
  }, [elemento]);

  const loadDomainData = async () => {
    setLoading(true);
    try {
      const [categorieData, prioritaData] = await Promise.all([
        esempioAPI.getCategorie(),
        esempioAPI.getPriorita(),
      ]);
      setCategorie(categorieData);
      setPriorita(prioritaData);
    } catch (err) {
      console.error('Error loading domain data:', err);
      setError('Errore nel caricamento dei dati di dominio');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSaving(true);

    try {
      // Prepare data for API
      const data = {
        ...formData,
        categoria_id: formData.categoria_id ? parseInt(formData.categoria_id) : null,
        priorita_id: formData.priorita_id ? parseInt(formData.priorita_id) : null,
        quantita: formData.quantita ? parseInt(formData.quantita) : null,
        importo: formData.importo ? parseFloat(formData.importo) : null,
        percentuale: formData.percentuale ? parseFloat(formData.percentuale) : null,
        data_inizio: formData.data_inizio || null,
        data_fine: formData.data_fine || null,
      };

      if (isEditing) {
        await esempioAPI.updateElemento(elemento.id, data);
      } else {
        await esempioAPI.createElemento(data);
      }

      onSave();
    } catch (err) {
      console.error('Error saving elemento:', err);
      setError(err.response?.data?.detail || 'Errore nel salvataggio');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="modal-overlay">
        <div className="modal-content">
          <div className="loading">Caricamento...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content elemento-form" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{isEditing ? 'Modifica Elemento' : 'Nuovo Elemento'}</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="error-message">{error}</div>
          )}

          <div className="form-grid">
            {/* Row 1: Codice + Titolo */}
            <div className="form-group">
              <label htmlFor="codice">Codice *</label>
              <input
                type="text"
                id="codice"
                name="codice"
                value={formData.codice}
                onChange={handleChange}
                required
                maxLength={20}
                placeholder="Es: EL001"
              />
            </div>

            <div className="form-group">
              <label htmlFor="titolo">Titolo *</label>
              <input
                type="text"
                id="titolo"
                name="titolo"
                value={formData.titolo}
                onChange={handleChange}
                required
                maxLength={200}
                placeholder="Titolo dell'elemento"
              />
            </div>

            {/* Row 2: Categoria + Priorità */}
            <div className="form-group">
              <label htmlFor="categoria_id">Categoria</label>
              <select
                id="categoria_id"
                name="categoria_id"
                value={formData.categoria_id}
                onChange={handleChange}
              >
                <option value="">-- Seleziona --</option>
                {categorie.map(cat => (
                  <option key={cat.id} value={cat.id}>
                    {cat.nome}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="priorita_id">Priorità</label>
              <select
                id="priorita_id"
                name="priorita_id"
                value={formData.priorita_id}
                onChange={handleChange}
              >
                <option value="">-- Seleziona --</option>
                {priorita.map(pri => (
                  <option key={pri.id} value={pri.id}>
                    {pri.nome}
                  </option>
                ))}
              </select>
            </div>

            {/* Row 3: Stato + Attivo */}
            <div className="form-group">
              <label htmlFor="stato">Stato</label>
              <select
                id="stato"
                name="stato"
                value={formData.stato}
                onChange={handleChange}
              >
                {STATI_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  name="attivo"
                  checked={formData.attivo}
                  onChange={handleChange}
                />
                Attivo
              </label>
            </div>

            {/* Row 4: Quantità + Importo + Percentuale */}
            <div className="form-group">
              <label htmlFor="quantita">Quantità</label>
              <input
                type="number"
                id="quantita"
                name="quantita"
                value={formData.quantita}
                onChange={handleChange}
                min={0}
              />
            </div>

            <div className="form-group">
              <label htmlFor="importo">Importo (€)</label>
              <input
                type="number"
                id="importo"
                name="importo"
                value={formData.importo}
                onChange={handleChange}
                min={0}
                step="0.01"
                placeholder="0.00"
              />
            </div>

            <div className="form-group">
              <label htmlFor="percentuale">Percentuale (%)</label>
              <input
                type="number"
                id="percentuale"
                name="percentuale"
                value={formData.percentuale}
                onChange={handleChange}
                min={0}
                max={100}
                step="0.01"
                placeholder="0.00"
              />
            </div>

            {/* Row 5: Date */}
            <div className="form-group">
              <label htmlFor="data_inizio">Data Inizio</label>
              <input
                type="date"
                id="data_inizio"
                name="data_inizio"
                value={formData.data_inizio}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label htmlFor="data_fine">Data Fine</label>
              <input
                type="date"
                id="data_fine"
                name="data_fine"
                value={formData.data_fine}
                onChange={handleChange}
              />
            </div>
          </div>

          {/* Descrizione (full width) */}
          <div className="form-group full-width">
            <label htmlFor="descrizione">Descrizione</label>
            <textarea
              id="descrizione"
              name="descrizione"
              value={formData.descrizione}
              onChange={handleChange}
              rows={3}
              placeholder="Descrizione dettagliata dell'elemento"
            />
          </div>

          {/* Note (full width) */}
          <div className="form-group full-width">
            <label htmlFor="note">Note</label>
            <textarea
              id="note"
              name="note"
              value={formData.note}
              onChange={handleChange}
              rows={2}
              placeholder="Note aggiuntive"
            />
          </div>

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Annulla
            </button>
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? 'Salvataggio...' : (isEditing ? 'Salva Modifiche' : 'Crea Elemento')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ElementoEsempioForm;
