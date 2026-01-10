import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { getSoggettiAnagrafici, getRuoliAziendaTipi } from '../../services/anagraficaAPI';
import './RuoloAziendaForm.css';

/**
 * Form modale per creare/modificare un ruolo azienda
 */
export default function RuoloAziendaForm({
  soggettoCorrente,
  ruoloToEdit = null,
  onClose,
  onSave
}) {
  const [formData, setFormData] = useState({
    persona_fisica_id: '',
    persona_giuridica_id: '',
    ruolo_tipo_id: '',
    ruolo: '',
    data_inizio: '',
    data_fine: ''
  });

  const [soggetti, setSoggetti] = useState([]);
  const [ruoliTipi, setRuoliTipi] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [showCustomRuolo, setShowCustomRuolo] = useState(false);

  const token = localStorage.getItem('access_token');
  const isPersonaFisica = soggettoCorrente.tipo_soggetto === 'PERSONA_FISICA';

  useEffect(() => {
    loadSoggetti();
    loadRuoliTipi();
    if (ruoloToEdit) {
      setFormData({
        persona_fisica_id: ruoloToEdit.persona_fisica_id,
        persona_giuridica_id: ruoloToEdit.persona_giuridica_id,
        ruolo_tipo_id: ruoloToEdit.ruolo_tipo_id || '',
        ruolo: ruoloToEdit.ruolo || '',
        data_inizio: ruoloToEdit.data_inizio || '',
        data_fine: ruoloToEdit.data_fine || ''
      });
      // Se ha solo ruolo testuale (legacy), mostra campo custom
      if (!ruoloToEdit.ruolo_tipo_id && ruoloToEdit.ruolo) {
        setShowCustomRuolo(true);
      }
    } else {
      // Pre-compila con il soggetto corrente
      if (isPersonaFisica) {
        setFormData(prev => ({ ...prev, persona_fisica_id: soggettoCorrente.id }));
      } else {
        setFormData(prev => ({ ...prev, persona_giuridica_id: soggettoCorrente.id }));
      }
    }
  }, [ruoloToEdit, soggettoCorrente]);

  const loadSoggetti = async () => {
    try {
      setLoading(true);
      // Carica soggetti del tipo opposto
      const tipoRicerca = isPersonaFisica ? 'PERSONA_GIURIDICA' : 'PERSONA_FISICA';
      const soggetti = await getSoggettiAnagrafici();
      const soggettiFiltered = soggetti.filter(s => s.tipo_soggetto === tipoRicerca);
      setSoggetti(soggettiFiltered);
    } catch (err) {
      console.error('Error loading soggetti:', err);
      setError('Errore nel caricamento dei soggetti');
    } finally {
      setLoading(false);
    }
  };

  const loadRuoliTipi = async () => {
    try {
      // Carica ruoli attivi per l'autocomplete
      const ruoli = await getRuoliAziendaTipi({ attivi_solo: true });
      setRuoliTipi(ruoli);
    } catch (err) {
      console.error('Error loading ruoli tipi:', err);
      // Non bloccare il form se fallisce il caricamento dei ruoli
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSaving(true);

    try {
      const dataToSave = {
        persona_fisica_id: parseInt(formData.persona_fisica_id),
        persona_giuridica_id: parseInt(formData.persona_giuridica_id),
        ruolo_tipo_id: formData.ruolo_tipo_id ? parseInt(formData.ruolo_tipo_id) : null,
        ruolo: formData.ruolo || null,
        data_inizio: formData.data_inizio || null,
        data_fine: formData.data_fine || null
      };

      await onSave(dataToSave, ruoloToEdit?.id);
      onClose();
    } catch (err) {
      console.error('Error saving ruolo:', err);
      setError(err.response?.data?.detail || 'Errore nel salvataggio del ruolo');
    } finally {
      setSaving(false);
    }
  };

  const getSoggettoNome = (soggetto) => {
    if (soggetto.tipo_soggetto === 'PERSONA_FISICA') {
      return `${soggetto.nome || ''} ${soggetto.cognome || ''}`.trim();
    }
    return soggetto.ragione_sociale || '';
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{ruoloToEdit ? 'Modifica Ruolo' : 'Nuovo Ruolo Azienda'}</h2>
          <button className="modal-close" onClick={onClose} aria-label="Chiudi">
            ✖
          </button>
        </div>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="ruolo-form">
          {/* Mostra il soggetto corrente come fisso */}
          <div className="form-group">
            <label>
              {isPersonaFisica ? 'Persona' : 'Azienda'}
            </label>
            <input
              type="text"
              value={getSoggettoNome(soggettoCorrente)}
              disabled
              className="input-disabled"
            />
          </div>

          {/* Seleziona la controparte */}
          <div className="form-group">
            <label htmlFor="controparte">
              {isPersonaFisica ? 'Azienda *' : 'Persona *'}
            </label>
            {loading ? (
              <p>Caricamento...</p>
            ) : (
              <select
                id="controparte"
                value={isPersonaFisica ? formData.persona_giuridica_id : formData.persona_fisica_id}
                onChange={(e) => {
                  const value = e.target.value;
                  if (isPersonaFisica) {
                    setFormData({ ...formData, persona_giuridica_id: value });
                  } else {
                    setFormData({ ...formData, persona_fisica_id: value });
                  }
                }}
                required
                disabled={!!ruoloToEdit}
              >
                <option value="">-- Seleziona --</option>
                {soggetti.map(s => (
                  <option key={s.id} value={s.id}>
                    {getSoggettoNome(s)}
                    {s.codice_fiscale && ` (${s.codice_fiscale})`}
                  </option>
                ))}
              </select>
            )}
            <small>Seleziona {isPersonaFisica ? "l'azienda" : 'la persona'} da associare</small>
          </div>

          {/* Selezione ruolo */}
          <div className="form-group">
            <label htmlFor="ruolo_tipo">Ruolo *</label>
            {!showCustomRuolo ? (
              <>
                <select
                  id="ruolo_tipo"
                  value={formData.ruolo_tipo_id}
                  onChange={(e) => {
                    const value = e.target.value;
                    if (value === 'custom') {
                      setShowCustomRuolo(true);
                      setFormData({ ...formData, ruolo_tipo_id: '', ruolo: '' });
                    } else {
                      const ruoloSelezionato = ruoliTipi.find(r => r.id === parseInt(value));
                      setFormData({
                        ...formData,
                        ruolo_tipo_id: value,
                        ruolo: ruoloSelezionato ? ruoloSelezionato.nome : ''
                      });
                    }
                  }}
                  required={!showCustomRuolo}
                >
                  <option value="">-- Seleziona un ruolo --</option>
                  {ruoliTipi.map(ruolo => (
                    <option key={ruolo.id} value={ruolo.id}>
                      {ruolo.nome}
                    </option>
                  ))}
                  <option value="custom">➕ Altro (nuovo ruolo)...</option>
                </select>
                <small>Seleziona un ruolo dalla lista standard. Per aggiungere nuovi ruoli, vai in Domini → Tipi Ruolo.</small>
              </>
            ) : (
              <>
                <input
                  id="ruolo_custom"
                  type="text"
                  value={formData.ruolo}
                  onChange={(e) => setFormData({ ...formData, ruolo: e.target.value })}
                  placeholder="es: Amministratore Delegato, Consulente..."
                  required
                  maxLength={100}
                />
                <button
                  type="button"
                  className="btn-link"
                  onClick={() => {
                    setShowCustomRuolo(false);
                    setFormData({ ...formData, ruolo: '', ruolo_tipo_id: '' });
                  }}
                >
                  ← Torna alla selezione standard
                </button>
                <small>
                  <strong>Attenzione:</strong> Stai inserendo un ruolo personalizzato.
                  Per mantenere la coerenza, è consigliato aggiungere prima il ruolo nei Domini → Tipi Ruolo.
                </small>
              </>
            )}
          </div>

          {/* Date */}
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="data_inizio">Data Inizio</label>
              <input
                id="data_inizio"
                type="date"
                value={formData.data_inizio}
                onChange={(e) => setFormData({ ...formData, data_inizio: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label htmlFor="data_fine">Data Fine</label>
              <input
                id="data_fine"
                type="date"
                value={formData.data_fine}
                onChange={(e) => setFormData({ ...formData, data_fine: e.target.value })}
              />
              <small>Lascia vuoto se attualmente attivo</small>
            </div>
          </div>

          {/* Actions */}
          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? 'Salvataggio...' : (ruoloToEdit ? 'Aggiorna' : 'Crea')}
            </button>
            <button type="button" className="btn-secondary" onClick={onClose}>
              Annulla
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

RuoloAziendaForm.propTypes = {
  soggettoCorrente: PropTypes.object.isRequired,
  ruoloToEdit: PropTypes.object,
  onClose: PropTypes.func.isRequired,
  onSave: PropTypes.func.isRequired
};
