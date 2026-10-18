import { useState } from 'react';
import { messaggiAPI } from '../../services/pecAPI';
import RispostaConfirm from './RispostaConfirm';
import './Risposta.css';

function formatData(dateString) {
  if (!dateString) return '';
  try {
    return new Date(dateString).toLocaleString('it-IT');
  } catch {
    return dateString;
  }
}

/**
 * RispostaModal
 *
 * Overlay modale per comporre e inviare una risposta PEC.
 *
 * Props:
 *   messaggio          {object}   Messaggio originale a cui si risponde
 *   casella            {object}   Casella PEC mittente (per mostrare indirizzo)
 *   onClose            {function} Chiude la modale senza inviare
 *   onRispostaInviata  {function} Callback chiamato dopo invio riuscito (o FAILED)
 */
export default function RispostaModal({ messaggio, casella, onClose, onRispostaInviata }) {
  // Pre-compila destinatario con il mittente del messaggio originale
  const [destinatari, setDestinatari] = useState(messaggio?.da || '');
  // Pre-compila oggetto con "Re: " se non già presente
  const oggettoOriginale = messaggio?.oggetto || '';
  const oggettoDefault = oggettoOriginale.toLowerCase().startsWith('re:')
    ? oggettoOriginale
    : `Re: ${oggettoOriginale}`;
  const [oggetto, setOggetto] = useState(oggettoDefault);
  const [corpo, setCorpo] = useState('');
  const [step, setStep] = useState('compose'); // 'compose' | 'confirm'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!messaggio) return null;

  // ── Validazione form ──
  const handleAnteprima = (e) => {
    e.preventDefault();
    setError(null);

    const destinatariTrimmed = destinatari.trim();
    const oggettoTrimmed = oggetto.trim();
    const corpoTrimmed = corpo.trim();

    if (!destinatariTrimmed) {
      setError('Inserisci almeno un destinatario.');
      return;
    }
    if (!oggettoTrimmed) {
      setError("Inserisci l'oggetto della risposta.");
      return;
    }
    if (corpoTrimmed.length < 10) {
      setError('Il corpo della risposta deve contenere almeno 10 caratteri.');
      return;
    }

    setStep('confirm');
  };

  // ── Invio effettivo ──
  const handleConferma = async () => {
    setLoading(true);
    setError(null);

    // Normalizza lista destinatari: separa per virgola/punto-virgola
    const listaDestinatari = destinatari
      .split(/[,;]/)
      .map((s) => s.trim())
      .filter(Boolean);

    try {
      const res = await messaggiAPI.rispondi(messaggio.id, {
        destinatari: listaDestinatari,
        oggetto,
        corpo_testo: corpo,
      });

      const smtpStatus = res.data?.smtp_status;
      onRispostaInviata && onRispostaInviata(smtpStatus);
    } catch (err) {
      const detail = err.response?.data?.detail || 'Errore durante l\'invio della risposta.';
      setError(detail);
      setStep('compose');
    } finally {
      setLoading(false);
    }
  };

  const dataMessaggio = formatData(messaggio.data_invio || messaggio.data_ricezione);

  return (
    <div className="risposta-overlay" role="dialog" aria-modal="true" aria-label="Rispondi al messaggio">
      <div className="risposta-modal">
        {/* ── Header ── */}
        <div className="risposta-header">
          <h3>Rispondi</h3>
          <button
            type="button"
            className="risposta-header-close"
            onClick={onClose}
            aria-label="Chiudi"
            disabled={loading}
          >
            &times;
          </button>
        </div>

        {/* ── Riepilogo messaggio originale ── */}
        <div className="risposta-originale">
          <div className="risposta-originale-riga">
            <span>In risposta a:</span>
            <strong>{messaggio.oggetto || '(nessun oggetto)'}</strong>
          </div>
          <div className="risposta-originale-riga">
            <span>Da:</span>
            <strong>{messaggio.da}</strong>
            {dataMessaggio && (
              <>
                <span>&bull;</span>
                <span>{dataMessaggio}</span>
              </>
            )}
          </div>
        </div>

        {/* ── Messaggio di errore ── */}
        {error && <div className="risposta-error">{error}</div>}

        {/* ── Step: composizione ── */}
        {step === 'compose' && (
          <form className="risposta-form" onSubmit={handleAnteprima} noValidate>
            <div className="risposta-field">
              <label htmlFor="risposta-destinatari">A</label>
              <input
                id="risposta-destinatari"
                type="text"
                value={destinatari}
                onChange={(e) => setDestinatari(e.target.value)}
                placeholder="indirizzo@esempio.it"
                autoComplete="off"
                required
              />
            </div>

            <div className="risposta-field">
              <label htmlFor="risposta-oggetto">Oggetto</label>
              <input
                id="risposta-oggetto"
                type="text"
                value={oggetto}
                onChange={(e) => setOggetto(e.target.value)}
                required
              />
            </div>

            <div className="risposta-field">
              <label htmlFor="risposta-corpo">Messaggio</label>
              <textarea
                id="risposta-corpo"
                value={corpo}
                onChange={(e) => setCorpo(e.target.value)}
                placeholder="Scrivi la tua risposta..."
                required
                minLength={10}
              />
            </div>

            <div className="risposta-actions">
              <button
                type="button"
                className="risposta-btn risposta-btn-secondary"
                onClick={onClose}
              >
                Annulla
              </button>
              <button type="submit" className="risposta-btn risposta-btn-primary">
                Anteprima
              </button>
            </div>
          </form>
        )}

        {/* ── Step: conferma ── */}
        {step === 'confirm' && (
          <RispostaConfirm
            casella={casella}
            destinatari={destinatari}
            oggetto={oggetto}
            corpo={corpo}
            onConferma={handleConferma}
            onIndietro={() => { setStep('compose'); setError(null); }}
            loading={loading}
          />
        )}
      </div>
    </div>
  );
}
