import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { createSoggetto, updateSoggetto, getSoggettoById } from '../../services/anagraficaAPI';
import './PersonaGiuridicaForm.css';

/**
 * PersonaGiuridicaForm - Form ottimizzato per persone giuridiche
 *
 * Campi specifici: Ragione Sociale, P.IVA, CF (11 cifre), Forma Giuridica
 * Supporta sia creazione che modifica (rileva ID dai params)
 */
function PersonaGiuridicaForm() {
  const navigate = useNavigate();
  const { id } = useParams(); // Se presente, siamo in edit mode
  const isEditMode = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(isEditMode);
  const [error, setError] = useState(null);

  const [formData, setFormData] = useState({
    tipo_soggetto: 'PERSONA_GIURIDICA',
    // Dati azienda
    ragione_sociale: '',
    partita_iva: '',
    codice_fiscale: '',
    forma_giuridica: '',
    // Contatti
    email: '',
    telefono: '',
    pec: '',
    // Sede legale
    indirizzo: '',
    citta: '',
    cap: '',
    provincia: '',
    // Altro
    note: '',
    attivo: true,
  });

  const formeGiuridiche = [
    'SRL - Società a Responsabilità Limitata',
    'SPA - Società per Azioni',
    'SAPA - Società in Accomandita per Azioni',
    'SNC - Società in Nome Collettivo',
    'SAS - Società in Accomandita Semplice',
    'SS - Società Semplice',
    'SRLS - Società a Responsabilità Limitata Semplificata',
    'Cooperativa',
    'Associazione',
    'Fondazione',
    'Ente Pubblico',
    'Altro'
  ];

  // Carica dati in edit mode
  useEffect(() => {
    if (isEditMode) {
      loadAziendaData();
    }
  }, [id]);

  const loadAziendaData = async () => {
    try {
      setLoadingData(true);
      setError(null);
      const data = await getSoggettoById(id);

      // Verifica che sia effettivamente una persona giuridica
      if (data.tipo_soggetto !== 'PERSONA_GIURIDICA') {
        setError('Questo soggetto non è una persona giuridica');
        return;
      }

      // Popola il form con i dati esistenti
      setFormData({
        tipo_soggetto: data.tipo_soggetto,
        ragione_sociale: data.ragione_sociale || '',
        partita_iva: data.partita_iva || '',
        codice_fiscale: data.codice_fiscale || '',
        forma_giuridica: data.forma_giuridica || '',
        email: data.email || '',
        telefono: data.telefono || '',
        pec: data.pec || '',
        indirizzo: data.indirizzo || '',
        citta: data.citta || '',
        cap: data.cap || '',
        provincia: data.provincia || '',
        note: data.note || '',
        attivo: data.attivo !== undefined ? data.attivo : true,
      });
    } catch (err) {
      console.error('Error loading azienda:', err);
      setError('Errore nel caricamento dei dati dell\'azienda/ente');
    } finally {
      setLoadingData(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;

    // Auto-sync CF con P.IVA per persone giuridiche
    if (name === 'partita_iva') {
      setFormData(prev => ({
        ...prev,
        partita_iva: value,
        codice_fiscale: value  // CF = P.IVA per aziende
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: type === 'checkbox' ? checked : value
      }));
    }
  };

  const validatePartitaIVA = (piva) => {
    // Validazione: 11 cifre numeriche
    return /^\d{11}$/.test(piva);
  };

  const validateForm = () => {
    // Campi obbligatori
    if (!formData.ragione_sociale.trim()) {
      setError('Ragione Sociale è obbligatoria');
      return false;
    }
    if (!formData.partita_iva.trim()) {
      setError('Partita IVA è obbligatoria');
      return false;
    }

    // Validazione P.IVA
    if (!validatePartitaIVA(formData.partita_iva)) {
      setError('Partita IVA deve essere di 11 cifre numeriche');
      return false;
    }

    // Validazione email (se presente)
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      setError('Email non valida');
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

      const dataToSend = {
        ...formData,
        // CF = P.IVA per persone giuridiche
        codice_fiscale: formData.partita_iva,
      };

      let result;
      if (isEditMode) {
        // Modifica azienda esistente
        result = await updateSoggetto(id, dataToSend);
      } else {
        // Crea nuova azienda
        result = await createSoggetto(dataToSend);
      }

      // Redirect al dettaglio dell'azienda (specifico per persone giuridiche)
      navigate(`/anagrafiche/persone-giuridiche/${result.id}`);
    } catch (err) {
      console.error(`Error ${isEditMode ? 'updating' : 'creating'} persona giuridica:`, err);
      setError(err.response?.data?.detail || `Errore ${isEditMode ? 'nella modifica' : 'nella creazione'} della persona giuridica`);
    } finally {
      setLoading(false);
    }
  };

  // Loading state per caricamento dati in edit mode
  if (loadingData) {
    return (
      <div className="form-container">
        <div className="loading">Caricamento dati persona giuridica...</div>
      </div>
    );
  }

  return (
    <div className="form-container">
      <div className="form-header">
        <h1>🏢 {isEditMode ? 'Modifica Persona Giuridica' : 'Nuova Persona Giuridica'}</h1>
        <button
          type="button"
          onClick={() => navigate('/anagrafiche/persone-giuridiche')}
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

      <div className="info-banner">
        <strong>ℹ️ Nota:</strong> Le persone giuridiche (aziende, società) non possono avere account utente.
        Per accedere al sistema, crea un account per una persona fisica che rappresenta l'azienda.
      </div>

      <form onSubmit={handleSubmit} className="persona-giuridica-form">

        {/* Dati Azienda */}
        <section className="form-section">
          <h2>🏢 Dati Azienda</h2>

          <div className="form-group">
            <label htmlFor="ragione_sociale">Ragione Sociale <span className="required">*</span></label>
            <input
              type="text"
              id="ragione_sociale"
              name="ragione_sociale"
              value={formData.ragione_sociale}
              onChange={handleChange}
              required
              placeholder="es. Acme S.r.l."
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="partita_iva">Partita IVA <span className="required">*</span></label>
              <input
                type="text"
                id="partita_iva"
                name="partita_iva"
                value={formData.partita_iva}
                onChange={handleChange}
                required
                maxLength="11"
                placeholder="12345678901"
                style={{ fontFamily: 'monospace' }}
              />
              <small>11 cifre numeriche</small>
            </div>

            <div className="form-group">
              <label htmlFor="codice_fiscale">Codice Fiscale</label>
              <input
                type="text"
                id="codice_fiscale"
                name="codice_fiscale"
                value={formData.codice_fiscale}
                readOnly
                style={{ fontFamily: 'monospace', backgroundColor: '#f5f5f5' }}
              />
              <small>Auto-compilato dalla P.IVA</small>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="forma_giuridica">Forma Giuridica</label>
            <select
              id="forma_giuridica"
              name="forma_giuridica"
              value={formData.forma_giuridica}
              onChange={handleChange}
            >
              <option value="">Seleziona forma giuridica...</option>
              {formeGiuridiche.map(forma => (
                <option key={forma} value={forma}>{forma}</option>
              ))}
            </select>
          </div>
        </section>

        {/* Contatti */}
        <section className="form-section">
          <h2>📧 Contatti</h2>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="info@acme.it"
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

          <div className="form-group">
            <label htmlFor="pec">PEC</label>
            <input
              type="email"
              id="pec"
              name="pec"
              value={formData.pec}
              onChange={handleChange}
              placeholder="acme@pec.it"
            />
            <small>Posta Elettronica Certificata</small>
          </div>
        </section>

        {/* Sede Legale */}
        <section className="form-section">
          <h2>🏢 Sede Legale</h2>

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
        </section>

        {/* Note */}
        <section className="form-section">
          <h2>📝 Note</h2>

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
        </section>

        {/* Actions */}
        <div className="form-actions">
          <button
            type="button"
            onClick={() => navigate('/anagrafiche/persone-giuridiche')}
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
              : (isEditMode ? '✅ Salva Modifiche' : '✅ Crea Persona Giuridica')
            }
          </button>
        </div>
      </form>
    </div>
  );
}

export default PersonaGiuridicaForm;
