import { useEffect, useId, useRef, useState } from 'react';
import { Button } from '../../../../components/UI';
import { FormModal } from '../../../../core/components/FormBuilder/FormModal';
import { beniAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import { opzioniCollegamento } from './opzioniCollegamento';

const MAX_RISULTATI = 20;

/**
 * Modal to link the bene to another one: pick what to link, search the other
 * bene, optional start date and notes. The search is local to this form; the
 * shared bene picker of phase 3 can replace it.
 */
export default function CollegamentoForm({ beneId, bene, onClose }) {
  const opzioni = opzioniCollegamento(bene);
  const uid = useId();
  const cercaRef = useRef(null);
  const [scelta, setScelta] = useState(0);
  const [q, setQ] = useState('');
  const [risultati, setRisultati] = useState(null); // null = no search yet
  const [altro, setAltro] = useState(null);
  const [dataInizio, setDataInizio] = useState('');
  const [note, setNote] = useState('');
  const [error, setError] = useState(null);
  const [manca, setManca] = useState(false);
  const [saving, setSaving] = useState(false);
  const tipoAltro = opzioni[scelta]?.tipoAltro;

  useEffect(() => {
    setAltro(null);
    if (!q.trim() || !tipoAltro) { setRisultati(null); return undefined; }
    let attivo = true;
    const t = setTimeout(() => {
      beniAPI.getAll({ q: q.trim(), tipo_bene: tipoAltro })
        .then((r) => { if (attivo) setRisultati((r.data || []).filter((b) => b.id !== beneId).slice(0, MAX_RISULTATI)); })
        .catch((err) => { if (attivo) setError(formatApiError(err)); });
    }, 250);
    return () => { attivo = false; clearTimeout(t); };
  }, [q, tipoAltro, beneId]);

  const salva = async (e) => {
    e.preventDefault();
    if (!altro) {
      setManca(true);
      cercaRef.current?.focus();
      return;
    }
    const opzione = opzioni[scelta];
    setSaving(true);
    setError(null);
    try {
      await beniAPI.creaCollegamento(beneId, {
        altro_bene_id: altro.id,
        tipo: opzione.tipo,
        questo_e: opzione.questo_e,
        data_inizio: dataInizio || null,
        note: note.trim() || null,
      });
      onClose(true);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  const descrizione = (b) => (b.descrizione || b.indirizzo ? ` · ${b.descrizione || b.indirizzo}` : '');

  return (
    <FormModal title="Collega un bene" size="small" onClose={() => onClose(false)}>
      <form className="collegamento-form" onSubmit={salva}>
        {error && <div className="collegamento-form__errore" role="alert">{error}</div>}
        <fieldset className="collegamento-form__campo">
          <legend>Collegamento</legend>
          {opzioni.map((o, i) => (
            <label key={`${o.tipo}-${o.questo_e}`} className="collegamento-opzione">
              <input type="radio" name={`${uid}-opzione`} checked={scelta === i}
                onChange={() => { setScelta(i); setQ(''); }} />
              {o.etichetta}
            </label>
          ))}
        </fieldset>
        <div className="collegamento-form__campo">
          <label htmlFor={`${uid}-cerca`}>Cerca il bene (codice, indirizzo, comune o foglio/particella)</label>
          <input id={`${uid}-cerca`} ref={cercaRef} type="search" value={q}
            aria-describedby={manca ? `${uid}-manca` : undefined}
            aria-invalid={manca || undefined}
            onChange={(e) => setQ(e.target.value)} />
          {manca && !altro && (
            <p id={`${uid}-manca`} className="collegamento-form__errore-campo">Scegli il bene da collegare</p>
          )}
          {risultati && risultati.length === 0 && (
            <p className="scheda-muted" role="status">Nessun bene trovato</p>
          )}
          {risultati && risultati.length > 0 && (
            <ul className="collegamento-risultati" aria-label="Risultati">
              {risultati.map((b) => (
                <li key={b.id}>
                  <button type="button" aria-pressed={altro?.id === b.id}
                    className={altro?.id === b.id ? 'is-selected' : undefined}
                    onClick={() => { setAltro(b); setManca(false); }}>
                    {b.codice}{descrizione(b)}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="collegamento-form__campo">
          <label htmlFor={`${uid}-inizio`}>Dal</label>
          <input id={`${uid}-inizio`} type="date" value={dataInizio} onChange={(e) => setDataInizio(e.target.value)} />
        </div>
        <div className="collegamento-form__campo">
          <label htmlFor={`${uid}-note`}>Note</label>
          <textarea id={`${uid}-note`} rows={2} value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
        <div className="collegamento-form__azioni">
          <Button variant="secondary" type="button" onClick={() => onClose(false)} disabled={saving}>Annulla</Button>
          <Button type="submit" disabled={saving}>{saving ? 'Salvataggio…' : 'Salva'}</Button>
        </div>
      </form>
    </FormModal>
  );
}
