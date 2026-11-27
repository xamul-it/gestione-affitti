import { useEffect, useId, useRef, useState } from 'react';
import { Button } from '../../../../components/UI';
import { raggruppamentiAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import { opzioniRami } from './rami';

/**
 * Inline picker of a ramo (flat list from the tree of active rami). escludiId leaves out a ramo and
 * its sub-rami. onConferma(id | null) does the move and may throw: its error is shown here.
 */
export default function SceltaRamo({ label, vuoto, attuale = null, escludiId = null, onConferma, onAnnulla }) {
  const uid = useId();
  const [opzioni, setOpzioni] = useState(null);
  const [scelta, setScelta] = useState(attuale == null ? '' : String(attuale));
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const selectRef = useRef(null);

  useEffect(() => {
    let attivo = true;
    raggruppamentiAPI.getAll({ vista: 'albero' })
      .then((r) => { if (attivo) setOpzioni(opzioniRami(r.data || [], escludiId)); })
      .catch((err) => { if (attivo) setError(formatApiError(err)); });
    return () => { attivo = false; };
  }, [escludiId]);

  // The choice gets the focus as soon as it can be used.
  useEffect(() => { if (opzioni) selectRef.current?.focus(); }, [opzioni]);

  const conferma = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await onConferma(scelta === '' ? null : Number(scelta));
    } catch (err) {
      setError(formatApiError(err));
      setSaving(false);
    }
  };

  return (
    <form className="scelta-ramo" onSubmit={conferma}>
      {error && <div className="scheda-error" role="alert">{error}</div>}
      <label htmlFor={`${uid}-ramo`}>{label}</label>
      <select id={`${uid}-ramo`} ref={selectRef} value={scelta} disabled={!opzioni}
        onChange={(e) => setScelta(e.target.value)}>
        <option value="">{opzioni ? vuoto : 'Caricamento…'}</option>
        {(opzioni || []).map((o) => <option key={o.id} value={o.id}>{o.percorso}</option>)}
      </select>
      <Button type="submit" size="sm" disabled={saving || !opzioni}>Conferma spostamento</Button>
      <Button type="button" variant="ghost" size="sm" onClick={onAnnulla} disabled={saving}>Annulla</Button>
    </form>
  );
}
