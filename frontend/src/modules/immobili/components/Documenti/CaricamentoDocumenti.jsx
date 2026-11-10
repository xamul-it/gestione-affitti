import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { Badge, Button, FormField } from '../../../../components/UI';
import FileDropzone from '../../../../core/components/Documenti/FileDropzone';
import { useToast } from '../../../../core/hooks/useToast';
import { documentiAPI } from '../../../../services/documentiAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import { caricamentoDocumentiAPI, unitaImmobiliariAPI } from '../../services/immobiliAPI';
import ImportVisuraModal from '../ImportVisura/ImportVisuraModal';
import './CaricamentoDocumenti.css';

/**
 * Single upload point for unit documents (spec
 * 2026-11-10-caricamento-unico-documenti-immobili): one row per dropped file;
 * the backend recognises type and unit and reads the data; the user completes
 * what is missing and confirms. Nothing is saved before "Conferma".
 */
const ESITI = {
  analisi: { label: 'In analisi', variant: 'neutral' },
  pronto: { label: 'Letto', variant: 'success' },
  in_lettura: { label: 'In lettura', variant: 'brand' },
  scegli_tipo: { label: 'Scegli il tipo', variant: 'warning' },
  scegli_immobile: { label: "Scegli l'immobile", variant: 'warning' },
  gia_presente: { label: 'Già presente', variant: 'neutral' },
  scartato: { label: 'Scartato', variant: 'danger' },
  errore: { label: 'Errore', variant: 'danger' },
  visura: { label: 'Visura', variant: 'brand' },
  salvato: { label: 'Caricato', variant: 'success' },
};
const CAMPI = { indirizzo: 'Indirizzo', piano: 'Piano', foglio: 'Foglio', particella: 'Particella', subalterno: 'Subalterno' };
const CLASSI = ['A4', 'A3', 'A2', 'A1', 'B', 'C', 'D', 'E', 'F', 'G'];
const POLLING_MS = 10000;
const MAX_ERRORI_POLLING = 3;
const MSG_POLLING = 'Impossibile verificare la lettura: riprova più tardi o scegli tipo e immobile';
// Outcomes that need the user: the first such row opens by itself.
const DA_COMPLETARE = new Set(['pronto', 'scegli_tipo', 'scegli_immobile', 'gia_presente']);

let nextId = 0;
const numero = (v) => (typeof v === 'number' ? v.toLocaleString('it-IT') : v);
const data = (iso) => (iso ? new Date(`${iso}T00:00:00`).toLocaleDateString('it-IT') : '');
const etichettaUnita = (u) => `${u.codice} · ${u.indirizzo}, ${u.citta}`;

function RigaDocumento({ riga, tipi, unita, onAggiorna, onConfermato, onChiudi }) {
  const toast = useToast();
  const a = riga.analisi;
  const [classe, setClasse] = useState('');
  const [differenze, setDifferenze] = useState([]);
  const [forza, setForza] = useState(false);
  const [saving, setSaving] = useState(false);
  const [errore, setErrore] = useState(null);

  useEffect(() => {
    setDifferenze(a?.differenze || []);
    setClasse(a?.dati?.classe || '');
  }, [a]);

  const rianalizza = async (modifiche) => {
    setErrore(null);
    try {
      const res = await caricamentoDocumentiAPI.rianalizza({
        upload_token: a.upload_token,
        tipo_codice: a.tipo_codice || null,
        unita_id: a.unita_id || null,
        ...modifiche,
      });
      onAggiorna(res.data);
    } catch (err) {
      setErrore(formatApiError(err));
    }
  };

  const conferma = async () => {
    setSaving(true);
    setErrore(null);
    try {
      await caricamentoDocumentiAPI.conferma({
        upload_token: a.upload_token,
        tipo_codice: a.tipo_codice,
        unita_id: a.unita_id,
        dati: a.tipo_codice === 'APE' ? { classe } : {},
        differenze,
        forza_duplicato: forza,
      });
      toast.success(`${a.nome_file}: documento caricato`);
      onConfermato();
    } catch (err) {
      setErrore(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  if (!a) return null;
  if (a.esito === 'visura') {
    return <ImportVisuraModal embedded initialFiles={[riga.file]} onImported={onConfermato} onClose={onChiudi} />;
  }

  const tipoNome = tipi.find((t) => t.codice === a.tipo_codice)?.nome || a.tipo_codice;
  const unitaScelta = unita.find((u) => u.id === a.unita_id);
  const scelteUnita = [...(a.candidati || []), ...unita.filter((u) => !(a.candidati || []).some((c) => c.id === u.id))];
  const puoConfermare = ['pronto', 'gia_presente'].includes(a.esito) && (a.tipo_codice !== 'APE' || classe)
    && (a.esito !== 'gia_presente' || forza);

  return (
    <div className="caricamento__dettaglio">
      {a.messaggio && !['scartato', 'errore'].includes(a.esito) && <p className="doc-muted">{a.messaggio}</p>}
      {a.esito === 'in_lettura' && <p className="doc-muted">Lettura del testo in corso: il riepilogo arriva da solo, anche se lasci la pagina.</p>}
      {a.esito !== 'scartato' && a.esito !== 'in_lettura' && (
        <div className="caricamento__scelte">
          <FormField label="Tipo di documento" htmlFor={`tipo-${riga.id}`}>
            <select id={`tipo-${riga.id}`} className="doc-input" value={a.tipo_codice || ''}
              onChange={(e) => rianalizza({ tipo_codice: e.target.value || null })}>
              <option value="">Scegli…</option>
              {tipi.filter((t) => t.codice !== 'VISURA_CATASTALE').map((t) => <option key={t.codice} value={t.codice}>{t.nome}</option>)}
            </select>
          </FormField>
          <FormField label="Immobile" htmlFor={`unita-${riga.id}`}>
            <select id={`unita-${riga.id}`} className="doc-input" value={a.unita_id || ''}
              onChange={(e) => rianalizza({ unita_id: e.target.value ? Number(e.target.value) : null })}>
              <option value="">Scegli…</option>
              {scelteUnita.map((u) => <option key={u.id} value={u.id}>{etichettaUnita(u)}</option>)}
            </select>
          </FormField>
        </div>
      )}
      {['pronto', 'gia_presente'].includes(a.esito) && (
        <>
          <dl className="caricamento__riepilogo">
            <dt>Tipo</dt><dd>{tipoNome}</dd>
            <dt>Immobile</dt><dd>{unitaScelta ? etichettaUnita(unitaScelta) : 'Immobile scelto (non presente in elenco)'}</dd>
            {a.dati?.ep_gl_nren != null && <><dt>EP gl,nren</dt><dd>{numero(a.dati.ep_gl_nren)} kWh/m² anno</dd></>}
            {a.dati?.data_emissione && <><dt>Emesso il</dt><dd>{data(a.dati.data_emissione)}</dd></>}
          </dl>
          {a.tipo_codice === 'APE' && (
            <FormField label="Classe energetica" htmlFor={`classe-${riga.id}`}>
              <select id={`classe-${riga.id}`} className="doc-input" value={classe} required
                disabled={Boolean(a.dati?.classe)} onChange={(e) => setClasse(e.target.value)}>
                <option value="">Indica la classe…</option>
                {CLASSI.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </FormField>
          )}
          {differenze.length > 0 && (
            <fieldset className="caricamento__differenze">
              <legend>Aggiorna i dati dell'immobile con quelli del documento</legend>
              {differenze.map((d, i) => (
                <label key={d.campo}>
                  <input type="checkbox" checked={d.selezionato}
                    onChange={() => setDifferenze(differenze.map((x, j) => (j === i ? { ...x, selezionato: !x.selezionato } : x)))} />
                  {`${CAMPI[d.campo] || d.campo}: da ${d.attuale ?? 'vuoto'} a ${d.nuovo}`}
                </label>
              ))}
            </fieldset>
          )}
          {(a.avvisi || []).map((m) => <p key={m} className="caricamento__avviso">{m}</p>)}
          {a.esito === 'gia_presente' && (
            <label className="caricamento__forza">
              <input type="checkbox" checked={forza} onChange={(e) => setForza(e.target.checked)} />
              Carica comunque
            </label>
          )}
          <div className="caricamento__azioni">
            <Button onClick={conferma} disabled={!puoConfermare || saving}>Conferma</Button>
          </div>
        </>
      )}
      {errore && <div className="doc-error" role="alert">{errore}</div>}
    </div>
  );
}

export default function CaricamentoDocumenti({ onCaricato }) {
  const [righe, setRighe] = useState([]);
  const [aperta, setAperta] = useState(null);
  const [tipi, setTipi] = useState([]);
  const [unita, setUnita] = useState([]);
  const righeRef = useRef(righe);
  righeRef.current = righe;
  const erroriPolling = useRef({});

  useEffect(() => {
    documentiAPI.getTipi('IMMOBILE').then((r) => setTipi(r.data || [])).catch(() => setTipi([]));
    unitaImmobiliariAPI.getAll().then((r) => setUnita(r.data || [])).catch(() => setUnita([]));
  }, []);

  const aggiorna = useCallback((id, modifiche) => {
    setRighe((rs) => rs.map((r) => (r.id === id ? { ...r, ...modifiche } : r)));
  }, []);

  // Open by itself the first row that needs the user, when none is open.
  useEffect(() => {
    if (aperta !== null) return;
    const prima = righe.find((r) => DA_COMPLETARE.has(r.esito));
    if (prima) setAperta(prima.id);
  }, [righe, aperta]);

  const aggiungi = (files) => {
    files.forEach((file) => {
      const id = ++nextId;
      setRighe((rs) => [...rs, { id, file, analisi: null, esito: 'analisi' }]);
      caricamentoDocumentiAPI.analizza(file)
        .then((res) => aggiorna(id, { analisi: res.data, esito: res.data.esito }))
        .catch((err) => aggiorna(id, {
          analisi: { nome_file: file.name, esito: 'errore', messaggio: formatApiError(err) }, esito: 'errore',
        }));
    });
  };

  const inLettura = useMemo(() => righe.some((r) => r.esito === 'in_lettura'), [righe]);
  useEffect(() => {
    if (!inLettura) return undefined;
    const timer = setInterval(() => {
      righeRef.current.filter((r) => r.esito === 'in_lettura').forEach((r) => {
        caricamentoDocumentiAPI.stato(r.analisi.upload_token)
          .then((res) => {
            erroriPolling.current[r.id] = 0;
            if (res.data.esito !== 'in_lettura') aggiorna(r.id, { analisi: res.data, esito: res.data.esito });
          })
          .catch(() => {
            const n = (erroriPolling.current[r.id] || 0) + 1;
            erroriPolling.current[r.id] = n;
            if (n >= MAX_ERRORI_POLLING) {
              aggiorna(r.id, { analisi: { ...r.analisi, esito: 'errore', messaggio: MSG_POLLING }, esito: 'errore' });
            }
          });
      });
    }, POLLING_MS);
    return () => clearInterval(timer);
  }, [inLettura, aggiorna]);

  return (
    <section className="caricamento" aria-label="Carica documenti">
      <p className="caricamento__annuncio" aria-live="polite">
        {righe.map((r) => `${r.file.name}: ${(ESITI[r.esito] || ESITI.errore).label}`).join('. ')}
      </p>
      <FileDropzone onFiles={aggiungi} title="Trascina qui i documenti degli immobili"
        hint="Visure, APE, planimetrie…: tipo e immobile vengono riconosciuti, tu confermi" />
      {righe.length > 0 && (
        <ul className="caricamento__righe">
          {righe.map((r) => {
            const esito = ESITI[r.esito] || ESITI.errore;
            const nome = r.file.name;
            return (
              <li key={r.id} className="caricamento__riga">
                <button type="button" className="caricamento__intestazione" aria-expanded={aperta === r.id}
                  onClick={() => r.esito !== 'salvato' && setAperta(aperta === r.id ? null : r.id)}>
                  {aperta === r.id
                    ? <ChevronDown size={18} aria-hidden="true" />
                    : <ChevronRight size={18} aria-hidden="true" />}
                  <span className="caricamento__nome">{nome}</span>
                  <Badge variant={esito.variant}>{esito.label}</Badge>
                </button>
                {['scartato', 'errore'].includes(r.esito) && r.analisi?.messaggio && (
                  <p className="caricamento__motivo">{r.analisi.messaggio}</p>
                )}
                {/* Kept mounted while closed: a half-done visura import keeps its state. */}
                {r.esito !== 'salvato' && r.analisi && (
                  <div hidden={aperta !== r.id}>
                    <RigaDocumento riga={r} tipi={tipi} unita={unita}
                      onAggiorna={(analisi) => aggiorna(r.id, { analisi, esito: analisi.esito })}
                      onChiudi={() => setAperta(null)}
                      onConfermato={() => { aggiorna(r.id, { esito: 'salvato' }); setAperta(null); onCaricato?.(); }} />
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
