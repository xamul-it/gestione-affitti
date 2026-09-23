import { useState, useEffect } from 'react';
import { conduttoriAPI } from '../../services/immobiliAPI';
import { getSoggettiAnagrafici } from '../../../anagrafica_italiana/services/anagraficaAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import './Conduttori.css';

function displaySoggetto(soggetto) {
  if (!soggetto) return '';
  const nomeCompleto = soggetto.ragione_sociale || [soggetto.nome, soggetto.cognome].filter(Boolean).join(' ');
  const identificativo = soggetto.codice_fiscale || soggetto.partita_iva || '';
  return identificativo ? `${nomeCompleto} (${identificativo})` : nomeCompleto;
}

function ConduttoreForm({ conduttore, onClose }) {
  const [soggettoId, setSoggettoId] = useState(conduttore?.soggetto_id || null);
  const [soggettoSelezionato, setSoggettoSelezionato] = useState(null);
  const [note, setNote] = useState(conduttore?.note || '');

  const [searchTerm, setSearchTerm] = useState('');
  const [soggettiCandidati, setSoggettiCandidati] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [loadingSoggetti, setLoadingSoggetti] = useState(false);

  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    // In edit mode, we don't have the soggetto's anagrafica details from the
    // conduttore record alone (it only stores soggetto_id) — show the ID as
    // a fallback label. The backend doesn't currently expose an endpoint to
    // fetch a single soggetto's summary from here without a broader fetch.
    if (conduttore?.soggetto_id && !soggettoSelezionato) {
      setSoggettoSelezionato({ id: conduttore.soggetto_id, nome: `Soggetto #${conduttore.soggetto_id}` });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conduttore]);

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
      if (conduttore) {
        await conduttoriAPI.update(conduttore.id, { note });
      } else {
        await conduttoriAPI.create({ soggetto_id: soggettoId, note });
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
          <h2>{conduttore ? 'Modifica Conduttore' : 'Nuovo Conduttore'}</h2>
          <button className="close-btn" onClick={() => onClose()}>×</button>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Soggetto Anagrafico *</label>
            {conduttore ? (
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
            <textarea value={note} onChange={(e) => setNote(e.target.value)} rows="3" />
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

export default ConduttoreForm;
