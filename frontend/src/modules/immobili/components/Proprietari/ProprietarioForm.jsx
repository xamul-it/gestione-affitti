import { useState, useEffect } from 'react';
import { proprietariAPI } from '../../services/immobiliAPI';
import { getSoggettiAnagrafici } from '../../../anagrafica_italiana/services/anagraficaAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import './Proprietari.css';

function displaySoggetto(soggetto) {
  if (!soggetto) return '';
  const nomeCompleto = soggetto.ragione_sociale || [soggetto.nome, soggetto.cognome].filter(Boolean).join(' ');
  const identificativo = soggetto.codice_fiscale || soggetto.partita_iva || '';
  return identificativo ? `${nomeCompleto} (${identificativo})` : nomeCompleto;
}

function ProprietarioForm({ proprietario, onClose }) {
  const [soggettoId, setSoggettoId] = useState(proprietario?.soggetto_id || null);
  const [soggettoSelezionato, setSoggettoSelezionato] = useState(null);
  const [noteProprietario, setNoteProprietario] = useState(proprietario?.note_proprietario || '');

  const [searchTerm, setSearchTerm] = useState('');
  const [soggettiCandidati, setSoggettiCandidati] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [loadingSoggetti, setLoadingSoggetti] = useState(false);

  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    // In edit mode, we don't have the soggetto's anagrafica details from the
    // proprietario record alone (it only stores soggetto_id) — show the ID as
    // a fallback label. The backend doesn't currently expose an endpoint to
    // fetch a single soggetto's summary from here without a broader fetch.
    if (proprietario?.soggetto_id && !soggettoSelezionato) {
      setSoggettoSelezionato({ id: proprietario.soggetto_id, nome: `Soggetto #${proprietario.soggetto_id}` });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [proprietario]);

  const handleSearch = async (term) => {
    setSearchTerm(term);
    if (!term || term.trim().length < 2) {
      setSoggettiCandidati([]);
      setShowResults(false);
      return;
    }
    setLoadingSoggetti(true);
    try {
      // No server-side search on this endpoint today — fetch a page and
      // filter client-side. Fine for the realistic size of an anagrafica
      // registry; revisit if this ever needs to scale to thousands.
      const tutti = await getSoggettiAnagrafici({ limit: 200 });
      const termLower = term.toLowerCase();
      const filtrati = tutti.filter((s) => {
        const nomeCompleto = (s.ragione_sociale || `${s.nome || ''} ${s.cognome || ''}`).toLowerCase();
        const cf = (s.codice_fiscale || '').toLowerCase();
        return nomeCompleto.includes(termLower) || cf.includes(termLower);
      });
      setSoggettiCandidati(filtrati.slice(0, 15));
      setShowResults(true);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingSoggetti(false);
    }
  };

  const handleSelectSoggetto = (soggetto) => {
    setSoggettoId(soggetto.id);
    setSoggettoSelezionato(soggetto);
    setSearchTerm('');
    setShowResults(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!soggettoId) {
      setError('Seleziona un soggetto anagrafico');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      if (proprietario) {
        await proprietariAPI.update(proprietario.id, { note_proprietario: noteProprietario });
      } else {
        await proprietariAPI.create({ soggetto_id: soggettoId, note_proprietario: noteProprietario });
      }
      onClose();
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>{proprietario ? 'Modifica Proprietario' : 'Nuovo Proprietario'}</h2>
          <button className="close-btn" onClick={() => onClose()}>×</button>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Soggetto Anagrafico *</label>
            {proprietario ? (
              <input type="text" value={displaySoggetto(soggettoSelezionato) || soggettoSelezionato?.nome || ''} disabled />
            ) : soggettoSelezionato ? (
              <div className="soggetto-selezionato">
                <span>{displaySoggetto(soggettoSelezionato)}</span>
                <button type="button" onClick={() => { setSoggettoId(null); setSoggettoSelezionato(null); }}>
                  Cambia
                </button>
              </div>
            ) : (
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => handleSearch(e.target.value)}
                  placeholder="Cerca per nome, cognome o codice fiscale..."
                  autoComplete="off"
                />
                {showResults && (
                  <div className="soggetto-search-results">
                    {loadingSoggetti && <div className="soggetto-search-item">Ricerca...</div>}
                    {!loadingSoggetti && soggettiCandidati.length === 0 && (
                      <div className="soggetto-search-item">Nessun soggetto trovato</div>
                    )}
                    {soggettiCandidati.map((s) => (
                      <div key={s.id} className="soggetto-search-item" onClick={() => handleSelectSoggetto(s)}>
                        {displaySoggetto(s)}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            <p className="field-hint">
              Il soggetto deve già esistere in anagrafica. Non trovi chi cerchi? Registralo prima nella sezione Anagrafica.
            </p>
          </div>

          <div className="form-group">
            <label>Note</label>
            <textarea value={noteProprietario} onChange={(e) => setNoteProprietario(e.target.value)} rows="3" />
          </div>

          <div className="form-actions">
            <button type="button" onClick={() => onClose()} disabled={saving}>Annulla</button>
            <button type="submit" className="primary" disabled={saving || !soggettoId}>
              {saving ? 'Salvataggio...' : 'Salva'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ProprietarioForm;
