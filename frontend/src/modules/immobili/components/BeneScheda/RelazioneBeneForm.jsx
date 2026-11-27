import { useEffect, useId, useState } from 'react';
import { Button } from '../../../../components/UI';
import { FormModal } from '../../../../core/components/FormBuilder/FormModal';
import { useToast } from '../../../../core/hooks/useToast';
import { relazioniAPI } from '../../../../services/relazioniAPI';
import { beniAPI } from '../../services/immobiliAPI';
import SoggettoPicker from '../../../anagrafica_italiana/components/SoggettiAnagrafici/SoggettoPicker';
import { formatApiError } from '../../../../utils/errorHandling';

const QUOTA = /^\s*(\d+)\s*\/\s*(\d+)\s*$/;

/** Same rule as the backend parse_quota: "n/d", 0 < n <= d. Returns the normalized text or throws. */
export function normalizzaQuota(testo) {
  const m = QUOTA.exec(testo || '');
  if (!m) throw new Error('Quota non valida: usa una frazione, per esempio 1/2');
  const num = Number(m[1]);
  const den = Number(m[2]);
  if (den === 0 || num === 0 || num > den) {
    throw new Error('Quota non valida: deve essere maggiore di zero e al massimo 1');
  }
  return `${num}/${den}`;
}

const CAMPI_REGISTRAZIONE = [
  { chiave: 'registrazione_data', label: 'Data di registrazione', type: 'date' },
  { chiave: 'registrazione_ufficio', label: 'Ufficio di registrazione', type: 'text' },
  { chiave: 'registrazione_numero', label: 'Numero di registrazione', type: 'text' },
];

/**
 * Add (or edit) a relation of a bene: the types are those of one family. The
 * quota field only shows for types that admit one; the comodato also asks for
 * the registration data. Warnings of the response are shown as toasts.
 */
export default function RelazioneBeneForm({
  beneId, famiglia, titolo, relazione, onClose, entityType = 'IMMOBILE', crea,
}) {
  const uid = useId();
  const toast = useToast();
  const modifica = Boolean(relazione);
  const [tipi, setTipi] = useState([]);
  const [tipo, setTipo] = useState(relazione?.tipo || '');
  const [soggetto, setSoggetto] = useState(null);
  const [quota, setQuota] = useState(relazione?.quota || '');
  const [dataInizio, setDataInizio] = useState(relazione?.data_inizio || '');
  const [dataFine, setDataFine] = useState(relazione?.data_fine || '');
  const [note, setNote] = useState(relazione?.note || '');
  const [dati, setDati] = useState(relazione?.dati || {});
  const [error, setError] = useState(null);
  const [errQuota, setErrQuota] = useState(null);
  const [manca, setManca] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let attivo = true;
    relazioniAPI.getTipi(entityType, famiglia)
      .then((r) => {
        if (!attivo) return;
        const lista = r.data || [];
        setTipi(lista);
        setTipo((corrente) => corrente || lista[0]?.codice || '');
      })
      .catch((err) => { if (attivo) setError(formatApiError(err)); });
    return () => { attivo = false; };
  }, [famiglia, entityType]);

  const tipoScelto = tipi.find((t) => t.codice === tipo);
  const conQuota = Boolean(tipoScelto?.ammette_quota);
  const comodato = tipo === 'comodatario';

  const salva = async (e) => {
    e.preventDefault();
    setError(null);
    setErrQuota(null);
    if (!modifica && !soggetto) {
      setManca(true);
      return;
    }
    let quotaOut = null;
    if (conQuota && quota.trim()) {
      try {
        quotaOut = normalizzaQuota(quota);
      } catch (err) {
        setErrQuota(err.message);
        return;
      }
    }
    if (dataInizio && dataFine && dataFine < dataInizio) {
      setError('La data di fine non può precedere la data di inizio');
      return;
    }
    // Keep the other keys of dati: only the registration ones are edited here.
    const datiOut = { ...(relazione?.dati || {}) };
    if (comodato) {
      CAMPI_REGISTRAZIONE.forEach(({ chiave }) => {
        if (dati[chiave]) datiOut[chiave] = dati[chiave]; else delete datiOut[chiave];
      });
    }
    const corpo = {
      data_inizio: dataInizio || null,
      data_fine: dataFine || null,
      note: note.trim() || null,
      ...(conQuota ? { quota: quotaOut } : {}),
      ...(comodato ? { dati: datiOut } : {}),
    };
    setSaving(true);
    try {
      if (modifica) {
        await relazioniAPI.update(relazione.id, corpo);
      } else {
        const nuova = { soggetto_id: soggetto.id, tipo, ...corpo };
        const r = await (crea ? crea(nuova) : beniAPI.createRelazione(beneId, nuova));
        (r.data?.avvisi || []).forEach((a) => toast.warning(a));
      }
      toast.success('Relazione salvata');
      onClose(true);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <FormModal title={modifica ? `Modifica · ${titolo}` : `Aggiungi · ${titolo}`} size="small" onClose={() => onClose(false)}>
      <form className="collegamento-form" onSubmit={salva} noValidate>
        {error && <div className="collegamento-form__errore" role="alert">{error}</div>}
        <div className="collegamento-form__campo">
          <label htmlFor={`${uid}-tipo`}>Tipo</label>
          <select id={`${uid}-tipo`} value={tipo} disabled={modifica} onChange={(e) => setTipo(e.target.value)}>
            {tipi.map((t) => <option key={t.codice} value={t.codice}>{t.nome}</option>)}
            {modifica && !tipoScelto && <option value={tipo}>{relazione.tipo_nome}</option>}
          </select>
        </div>
        {!modifica && (
          <div className="collegamento-form__campo">
            <SoggettoPicker label="Anagrafica" value={soggetto}
              onSelect={(s) => { setSoggetto(s); setManca(false); }} />
            {manca && <p className="collegamento-form__errore-campo">Scegli l&apos;anagrafica</p>}
          </div>
        )}
        {conQuota && (
          <div className="collegamento-form__campo">
            <label htmlFor={`${uid}-quota`}>Quota (frazione, es. 1/2)</label>
            <input id={`${uid}-quota`} type="text" inputMode="text" value={quota}
              aria-invalid={errQuota ? true : undefined}
              aria-describedby={errQuota ? `${uid}-errquota` : undefined}
              onChange={(e) => setQuota(e.target.value)} />
            {errQuota && <p id={`${uid}-errquota`} className="collegamento-form__errore-campo">{errQuota}</p>}
          </div>
        )}
        <div className="collegamento-form__campo">
          <label htmlFor={`${uid}-inizio`}>Dal</label>
          <input id={`${uid}-inizio`} type="date" value={dataInizio} onChange={(e) => setDataInizio(e.target.value)} />
        </div>
        <div className="collegamento-form__campo">
          <label htmlFor={`${uid}-fine`}>Fino al</label>
          <input id={`${uid}-fine`} type="date" value={dataFine} onChange={(e) => setDataFine(e.target.value)} />
        </div>
        {comodato && CAMPI_REGISTRAZIONE.map(({ chiave, label, type }) => (
          <div key={chiave} className="collegamento-form__campo">
            <label htmlFor={`${uid}-${chiave}`}>{label}</label>
            <input id={`${uid}-${chiave}`} type={type} value={dati[chiave] || ''}
              onChange={(e) => setDati({ ...dati, [chiave]: e.target.value })} />
          </div>
        ))}
        <div className="collegamento-form__campo">
          <label htmlFor={`${uid}-note`}>Note</label>
          <textarea id={`${uid}-note`} rows={2} value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
        <div className="collegamento-form__azioni">
          <Button variant="secondary" type="button" onClick={() => onClose(false)} disabled={saving}>Annulla</Button>
          <Button type="submit" disabled={saving || !tipo}>{saving ? 'Salvataggio…' : 'Salva'}</Button>
        </div>
      </form>
    </FormModal>
  );
}
