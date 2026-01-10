import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { createSoggetto, updateSoggetto, getSoggettoById } from '../../services/anagraficaAPI';
import { renderIcon } from '../../../../components/Navigation/iconRegistry.jsx';
import './PersonaFisicaForm.css';

/**
 * PersonaFisicaForm - Form ottimizzato per persone fisiche
 *
 * Campi specifici: Nome, Cognome, CF (16 char), Data Nascita, Luogo Nascita
 * Supporta sia creazione che modifica (rileva ID dai params)
 */
function PersonaFisicaForm() {
  const navigate = useNavigate();
  const { id } = useParams(); // Se presente, siamo in edit mode
  const isEditMode = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(isEditMode);
  const [error, setError] = useState(null);

  const [formData, setFormData] = useState({
    tipo_soggetto: 'PERSONA_FISICA',
    // Dati anagrafici
    nome: '',
    cognome: '',
    codice_fiscale: '',
    data_nascita: '',
    luogo_nascita: '',
    // Contatti
    email: '',
    telefono: '',
    cellulare: '',
    pec: '',
    // Residenza
    indirizzo: '',
    citta: '',
    cap: '',
    provincia: '',
    // Attività professionale (opzionale)
    partita_iva: '',
    // Altro
    note: '',
    attivo: true,
  });

  const formatErrorMessage = (err, fallback) => {
    const detail = err?.response?.data?.detail;
    if (!detail) return fallback;
    if (typeof detail === 'string') return detail;
    try {
      return JSON.stringify(detail);
    } catch (stringifyError) {
      return fallback;
    }
  };

  // Carica dati in edit mode
  useEffect(() => {
    if (isEditMode) {
      loadPersonaData();
    }
  }, [id]);

  const loadPersonaData = async () => {
    try {
      setLoadingData(true);
      setError(null);
      const data = await getSoggettoById(id);

      // Verifica che sia effettivamente una persona fisica
      if (data.tipo_soggetto !== 'PERSONA_FISICA') {
        setError('Questo soggetto non è una persona fisica');
        return;
      }

      // Popola il form con i dati esistenti
      setFormData({
        tipo_soggetto: data.tipo_soggetto,
        nome: data.nome || '',
        cognome: data.cognome || '',
        codice_fiscale: data.codice_fiscale || '',
        data_nascita: data.data_nascita || '',
        luogo_nascita: data.luogo_nascita || '',
        email: data.email || '',
        telefono: data.telefono || '',
        cellulare: data.cellulare || '',
        pec: data.pec || '',
        indirizzo: data.indirizzo || '',
        citta: data.citta || '',
        cap: data.cap || '',
        provincia: data.provincia || '',
        partita_iva: data.partita_iva || '',
        note: data.note || '',
        attivo: data.attivo !== undefined ? data.attivo : true,
      });
    } catch (err) {
      console.error('Error loading persona:', err);
      setError('Errore nel caricamento dei dati della persona');
    } finally {
      setLoadingData(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const validateCodiceFiscale = (cf) => {
    if (!cf) return true;
    // Validazione base: 16 caratteri alfanumerici maiuscoli
    const cfRegex = /^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$/;
    return cfRegex.test(cf.toUpperCase());
  };

  const validateForm = () => {
    // Campi obbligatori
    if (!formData.nome.trim()) {
      setError('Nome è obbligatorio');
      return false;
    }
    if (!formData.cognome.trim()) {
      setError('Cognome è obbligatorio');
      return false;
    }

    // Validazione CF
    if (!validateCodiceFiscale(formData.codice_fiscale)) {
      setError('Codice Fiscale non valido (deve essere 16 caratteri)');
      return false;
    }

    // Validazione email (se presente)
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      setError('Email non valida');
      return false;
    }

    // Validazione P.IVA (se presente)
    if (formData.partita_iva && !/^\d{11}$/.test(formData.partita_iva)) {
      setError('Partita IVA deve essere di 11 cifre');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);

      // Normalizza CF in maiuscolo
      const dataToSend = {
        ...formData,
        codice_fiscale: formData.codice_fiscale ? formData.codice_fiscale.toUpperCase() : null,
        partita_iva: formData.partita_iva || null,
        data_nascita: formData.data_nascita || null,
      };

      let result;
      if (isEditMode) {
        // Modifica persona esistente
        result = await updateSoggetto(id, dataToSend);
      } else {
        // Crea nuova persona
        result = await createSoggetto(dataToSend);
      }

      // Redirect al dettaglio della persona (specifico per persone fisiche)
      navigate(`/anagrafiche/persone-fisiche/${result.id}`);
    } catch (err) {
      console.error(`Error ${isEditMode ? 'updating' : 'creating'} persona fisica:`, err);
      setError(formatErrorMessage(
        err,
        `Errore ${isEditMode ? 'nella modifica' : 'nella creazione'} della persona fisica`
      ));
    } finally {
      setLoading(false);
    }
  };

  // Loading state per caricamento dati in edit mode
  if (loadingData) {
    return (
      <div className="form-container">
        <div className="loading">Caricamento dati persona fisica...</div>
      </div>
    );
  }

  return (
    <div className="form-container">
      <div className="form-header">
        <h1 className="form-title">
          <span className="form-title-icon" aria-hidden="true">
            {renderIcon('user', { size: 20, className: 'form-title-icon-svg', fallbackClassName: 'nav-emoji-icon' })}
          </span>
          {isEditMode ? 'Modifica Persona Fisica' : 'Nuova Persona Fisica'}
        </h1>
        <button
          type="button"
          onClick={() => navigate('/anagrafiche/persone-fisiche')}
          className="btn btn-secondary"
        >
          ← Indietro
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          <strong>Errore:</strong> {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="persona-fisica-form">

        {/* Dati Anagrafici */}
        <details className="form-section collapsible" open>
          <summary className="form-section-summary">
            <span className="form-section-title">
              <span className="form-section-icon" aria-hidden="true">
                {renderIcon('list', { size: 18, className: 'form-section-icon-svg', fallbackClassName: 'nav-emoji-icon' })}
              </span>
              Dati Anagrafici
            </span>
          </summary>
          <div className="form-section-body">
            <div className="form-row">
            <div className="form-group">
              <label htmlFor="nome">Nome <span className="required">*</span></label>
              <input
                type="text"
                id="nome"
                name="nome"
                value={formData.nome}
                onChange={handleChange}
                required
                placeholder="es. Mario"
              />
            </div>

            <div className="form-group">
              <label htmlFor="cognome">Cognome <span className="required">*</span></label>
              <input
                type="text"
                id="cognome"
                name="cognome"
                value={formData.cognome}
                onChange={handleChange}
                required
                placeholder="es. Rossi"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="codice_fiscale">Codice Fiscale <span className="required">*</span></label>
              <input
                type="text"
                id="codice_fiscale"
                name="codice_fiscale"
                value={formData.codice_fiscale}
                onChange={handleChange}
                required
                maxLength="16"
                placeholder="RSSMRA85M01H501Z"
                style={{ textTransform: 'uppercase', fontFamily: 'monospace' }}
              />
              <small>16 caratteri alfanumerici</small>
            </div>

            <div className="form-group">
              <label htmlFor="data_nascita">Data di Nascita</label>
              <input
                type="date"
                id="data_nascita"
                name="data_nascita"
                value={formData.data_nascita}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="luogo_nascita">Luogo di Nascita</label>
            <input
              type="text"
              id="luogo_nascita"
              name="luogo_nascita"
              value={formData.luogo_nascita}
              onChange={handleChange}
              placeholder="es. Roma"
            />
          </div>
          </div>
        </details>

        {/* Contatti */}
        <details className="form-section collapsible" open>
          <summary className="form-section-summary">
            <span className="form-section-title">
              <span className="form-section-icon" aria-hidden="true">
                {renderIcon('users', { size: 18, className: 'form-section-icon-svg', fallbackClassName: 'nav-emoji-icon' })}
              </span>
              Contatti
            </span>
          </summary>
          <div className="form-section-body">
            <div className="form-row">
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="mario.rossi@example.com"
              />
            </div>

            <div className="form-group">
              <label htmlFor="telefono">Telefono</label>
              <input
                type="tel"
                id="telefono"
                name="telefono"
                value={formData.telefono}
                onChange={handleChange}
                placeholder="02-1234567"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="cellulare">Cellulare</label>
              <input
                type="tel"
                id="cellulare"
                name="cellulare"
                value={formData.cellulare}
                onChange={handleChange}
                placeholder="333-1234567"
              />
            </div>

            <div className="form-group">
              <label htmlFor="pec">PEC</label>
              <input
                type="email"
                id="pec"
                name="pec"
                value={formData.pec}
                onChange={handleChange}
                placeholder="mario.rossi@pec.it"
              />
            </div>
          </div>
          </div>
        </details>

        {/* Residenza */}
        <details className="form-section collapsible" open>
          <summary className="form-section-summary">
            <span className="form-section-title">
              <span className="form-section-icon" aria-hidden="true">
                {renderIcon('building', { size: 18, className: 'form-section-icon-svg', fallbackClassName: 'nav-emoji-icon' })}
              </span>
              Residenza
            </span>
          </summary>
          <div className="form-section-body">
            <div className="form-group">
            <label htmlFor="indirizzo">Indirizzo</label>
            <input
              type="text"
              id="indirizzo"
              name="indirizzo"
              value={formData.indirizzo}
              onChange={handleChange}
              placeholder="Via Roma 123"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="citta">Città</label>
              <input
                type="text"
                id="citta"
                name="citta"
                value={formData.citta}
                onChange={handleChange}
                placeholder="Milano"
              />
            </div>

            <div className="form-group">
              <label htmlFor="cap">CAP</label>
              <input
                type="text"
                id="cap"
                name="cap"
                value={formData.cap}
                onChange={handleChange}
                maxLength="5"
                placeholder="20100"
              />
            </div>

            <div className="form-group">
              <label htmlFor="provincia">Provincia</label>
              <input
                type="text"
                id="provincia"
                name="provincia"
                value={formData.provincia}
                onChange={handleChange}
                maxLength="2"
                placeholder="MI"
                style={{ textTransform: 'uppercase' }}
              />
            </div>
          </div>
          </div>
        </details>

        {/* Attività Professionale */}
        <details className="form-section collapsible">
          <summary className="form-section-summary">
            <span className="form-section-title">
              <span className="form-section-icon" aria-hidden="true">
                {renderIcon('briefcase', { size: 18, className: 'form-section-icon-svg', fallbackClassName: 'nav-emoji-icon' })}
              </span>
              Attività Professionale (Opzionale)
            </span>
          </summary>
          <div className="form-section-body">
            <div className="form-group">
            <label htmlFor="partita_iva">Partita IVA</label>
            <input
              type="text"
              id="partita_iva"
              name="partita_iva"
              value={formData.partita_iva}
              onChange={handleChange}
              maxLength="11"
              placeholder="12345678901"
              style={{ fontFamily: 'monospace' }}
            />
            <small>Solo per liberi professionisti - 11 cifre</small>
          </div>
          </div>
        </details>

        {/* Note */}
        <details className="form-section collapsible">
          <summary className="form-section-summary">
            <span className="form-section-title">
              <span className="form-section-icon" aria-hidden="true">
                {renderIcon('list', { size: 18, className: 'form-section-icon-svg', fallbackClassName: 'nav-emoji-icon' })}
              </span>
              Note
            </span>
          </summary>
          <div className="form-section-body">
            <div className="form-group">
            <label htmlFor="note">Note aggiuntive</label>
            <textarea
              id="note"
              name="note"
              value={formData.note}
              onChange={handleChange}
              rows="4"
              placeholder="Eventuali note o informazioni aggiuntive..."
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
              <span>Attivo</span>
            </label>
          </div>
          </div>
        </details>

        {/* Actions */}
        <div className="form-actions">
          <button
            type="button"
            onClick={() => navigate('/anagrafiche/persone-fisiche')}
            className="btn btn-secondary"
            disabled={loading}
          >
            Annulla
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading
              ? (isEditMode ? 'Salvataggio in corso...' : 'Creazione in corso...')
              : (isEditMode ? '✅ Salva Modifiche' : '✅ Crea Persona Fisica')
            }
          </button>
        </div>
      </form>
    </div>
  );
}

export default PersonaFisicaForm;
