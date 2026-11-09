import { useRef, useState } from 'react';
import { AlertTriangle, CircleCheck, FileText, FileUp, X } from 'lucide-react';
import { visuraImportAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import { FormModal } from '../../../../core/components/FormBuilder/FormModal';
import { ConfirmDialog } from '../../../../core/components/common/ConfirmDialog';
import { LoadingSpinner } from '../../../../core/components/common/LoadingSpinner';
import { Badge, Button, FormField } from '../../../../components/UI';
import './ImportVisuraModal.css';

/**
 * "Carica da documento" for unità immobiliari.
 *
 * Step 1: choose document type + one or more PDFs (drag & drop or picker).
 * Step 2: the files are processed as a queue, one at a time: the backend
 *         builds a proposal (nothing saved), the user reviews it (every row
 *         can be deselected, tipo is required for new units) and imports or
 *         skips it, then the next file is analysed. Analysing only after the
 *         previous import keeps anagrafiche shared by several visure from
 *         being proposed twice.
 * Step 3: per-file outcome and totals.
 */

const TIPI_DOCUMENTO = [{ value: 'VISURA_CATASTALE', label: 'Visura catastale' }];

const TIPO_DIRITTO_LABELS = {
  PROPRIETARIO: 'Proprietà',
  COMPROPRIETARIO: 'Comproprietà',
  USUFRUTTUARIO: 'Usufrutto',
  NUDA_PROPRIETA: 'Nuda proprietà',
  USO: 'Uso',
  ABITAZIONE: 'Abitazione',
  SUPERFICIE: 'Superficie',
  ENFITEUSI: 'Enfiteusi',
  ALTRO: 'Altro',
};

const CAMPO_LABELS = {
  categoria_catastale_id: 'Categoria catastale',
  rendita_catastale: 'Rendita',
  superficie_mq: 'Superficie (m²)',
  indirizzo: 'Indirizzo',
  piano: 'Piano',
  note_catastali: 'Dati catastali (note)',
};

const CAMPI_SOGGETTO_LABELS = {
  codice_fiscale: 'codice fiscale',
  data_nascita: 'data di nascita',
  luogo_nascita: 'luogo di nascita',
};

const TIPI_SUGGERITI = ['Appartamento', 'Ufficio', 'Negozio', 'Magazzino', 'Box', 'Posto auto', 'Cantina', 'Laboratorio'];

const unitLabel = (u) => `foglio ${u.foglio} particella ${u.particella} sub ${u.subalterno || '-'}`;

const formatValue = (v) => (v === null || v === undefined || v === '' ? '—' : String(v));

function DirittiList({ unita, onToggle }) {
  if (!unita.diritti.length) return null;
  return (
    <ul className="visura-diritti">
      {unita.diritti.map((d, idx) => (
        <li key={`${d.soggetto_key}-${d.tipo_diritto}`}>
          {d.azione === 'crea' ? (
            <label>
              <input
                type="checkbox"
                checked={d.selezionato}
                disabled={!unita.selezionato}
                onChange={(e) => onToggle(idx, e.target.checked)}
              />
              {' '}{d.nominativo}: {TIPO_DIRITTO_LABELS[d.tipo_diritto] || d.tipo_diritto}
              {d.quota_percentuale != null ? ` ${d.quota_percentuale}%` : ''}
            </label>
          ) : (
            <span className="visura-muted">
              {d.nominativo}: {TIPO_DIRITTO_LABELS[d.tipo_diritto] || d.tipo_diritto} (già presente)
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}

function Avvisi({ avvisi }) {
  if (!avvisi?.length) return null;
  return (
    <ul className="visura-avvisi">
      {avvisi.map((a) => (
        <li key={a}>
          <AlertTriangle size={14} strokeWidth={1.7} aria-hidden="true" />
          <span>{a}</span>
        </li>
      ))}
    </ul>
  );
}

const MAX_SIZE = 10 * 1024 * 1024;

const STATO = {
  attesa: { label: 'In attesa', variant: 'neutral' },
  analisi: { label: 'Analisi…', variant: 'neutral' },
  revisione: { label: 'Da rivedere', variant: 'warning' },
  importazione: { label: 'Importazione…', variant: 'neutral' },
  importata: { label: 'Importata', variant: 'success' },
  saltata: { label: 'Saltata', variant: 'neutral' },
  errore: { label: 'Errore', variant: 'danger' },
};

const TOTALI_VUOTI = {
  unita_create: [], unita_aggiornate: [], soggetti_creati: 0, soggetti_aggiornati: 0,
  diritti_creati: 0, documenti_allegati: 0,
};

let nextItemId = 0;

const isPdf = (file) => file.type === 'application/pdf' || /\.pdf$/i.test(file.name);

function makeItem(file) {
  nextItemId += 1;
  let errore = null;
  if (!isPdf(file)) errore = 'Non è un file PDF';
  else if (file.size > MAX_SIZE) errore = 'File troppo grande (massimo 10 MB)';
  return { id: nextItemId, file, stato: errore ? 'errore' : 'attesa', errore, risultato: null };
}

function sommaRisultati(items) {
  return items.reduce((tot, it) => {
    const r = it.risultato;
    if (!r) return tot;
    return {
      unita_create: [...tot.unita_create, ...r.unita_create],
      unita_aggiornate: [...tot.unita_aggiornate, ...r.unita_aggiornate],
      soggetti_creati: tot.soggetti_creati + r.soggetti_creati,
      soggetti_aggiornati: tot.soggetti_aggiornati + r.soggetti_aggiornati,
      diritti_creati: tot.diritti_creati + r.diritti_creati,
      documenti_allegati: tot.documenti_allegati + r.documenti_allegati,
    };
  }, TOTALI_VUOTI);
}

function Dropzone({ onFiles, disabled }) {
  const inputRef = useRef(null);
  const [over, setOver] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setOver(false);
    if (!disabled) onFiles(Array.from(e.dataTransfer.files || []));
  };

  return (
    <div
      className={`visura-dropzone${over ? ' visura-dropzone--over' : ''}`}
      onDragOver={(e) => { e.preventDefault(); if (!disabled) setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); inputRef.current?.click(); }
      }}
      role="button"
      tabIndex={0}
      aria-label="Scegli i PDF delle visure"
      aria-describedby="visura-dropzone-hint"
    >
      <FileUp size={32} strokeWidth={1.7} className="visura-dropzone__icon" aria-hidden="true" />
      <p className="visura-dropzone__title">Trascina qui i PDF delle visure</p>
      <p id="visura-dropzone-hint" className="visura-muted">oppure fai clic per sceglierli · più file insieme</p>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept="application/pdf,.pdf"
        aria-label="File PDF"
        tabIndex={-1}
        className="visura-dropzone__input"
        onClick={(e) => e.stopPropagation()}
        onChange={(e) => { onFiles(Array.from(e.target.files || [])); e.target.value = ''; }}
      />
    </div>
  );
}

function CodaFile({ items, corrente, onRemove }) {
  if (!items.length) return null;
  return (
    <ol className="visura-coda" aria-label="File da importare">
      {items.map((it, idx) => {
        const stato = STATO[it.stato];
        return (
          <li key={it.id} className={`visura-coda__item${idx === corrente ? ' visura-coda__item--corrente' : ''}`}>
            <FileText size={16} strokeWidth={1.7} className="visura-coda__icon" aria-hidden="true" />
            <span className="visura-coda__nome" title={it.file.name}>{it.file.name}</span>
            <Badge variant={stato.variant}>{stato.label}</Badge>
            {onRemove && (
              <button
                type="button"
                className="visura-coda__remove"
                onClick={() => onRemove(it.id)}
                aria-label={`Rimuovi ${it.file.name}`}
              >
                <X size={16} strokeWidth={1.7} aria-hidden="true" />
              </button>
            )}
            {it.errore && <span className="visura-coda__errore">{it.errore}</span>}
          </li>
        );
      })}
    </ol>
  );
}

function ImportVisuraModal({ onClose, onImported }) {
  const [tipoDocumento, setTipoDocumento] = useState('VISURA_CATASTALE');
  const [items, setItems] = useState([]);
  const [fase, setFase] = useState('scelta'); // scelta | revisione | fine
  const [corrente, setCorrente] = useState(-1);
  const [proposta, setProposta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [confermaChiusura, setConfermaChiusura] = useState(false);

  const setStato = (id, patch) => setItems((prev) => prev.map((it) => (it.id === id ? { ...it, ...patch } : it)));

  const addFiles = (files) => {
    setError(null);
    setItems((prev) => {
      const presenti = new Set(prev.map((it) => `${it.file.name}|${it.file.size}`));
      const nuovi = files.filter((f) => !presenti.has(`${f.name}|${f.size}`)).map(makeItem);
      return [...prev, ...nuovi];
    });
  };

  const removeFile = (id) => setItems((prev) => prev.filter((it) => it.id !== id));

  // Analyse the queue one file at a time: each preview runs only after the
  // previous visura has been imported or skipped, so anagrafiche and units
  // created by an earlier visura are recognised by the next one.
  const analizzaDa = async (startIdx, lista) => {
    setProposta(null);
    setError(null);
    for (let idx = startIdx; idx < lista.length; idx += 1) {
      const it = lista[idx];
      if (it.stato !== 'attesa') continue;
      setCorrente(idx);
      setStato(it.id, { stato: 'analisi' });
      setLoading(true);
      try {
        const { data } = await visuraImportAPI.preview(it.file, tipoDocumento);
        setStato(it.id, { stato: 'revisione' });
        setProposta(data);
        setFase('revisione');
        return;
      } catch (err) {
        setStato(it.id, { stato: 'errore', errore: formatApiError(err) });
      } finally {
        setLoading(false);
      }
    }
    setCorrente(-1);
    setFase('fine');
  };

  const avvia = () => analizzaDa(0, items);

  const prossima = () => analizzaDa(corrente + 1, items);

  const salta = () => {
    setStato(items[corrente].id, { stato: 'saltata' });
    prossima();
  };

  const updateSoggetto = (key, patch) => setProposta((p) => ({
    ...p,
    soggetti: p.soggetti.map((s) => (s.key === key ? { ...s, ...patch } : s)),
  }));

  const updateUnita = (key, update) => setProposta((p) => ({
    ...p,
    unita: p.unita.map((u) => (u.key === key ? update(u) : u)),
  }));

  const setUnitaField = (key, patch) => updateUnita(key, (u) => ({ ...u, ...patch }));

  const toggleModifica = (key, idx, selezionato) => updateUnita(key, (u) => ({
    ...u,
    modifiche: u.modifiche.map((m, i) => (i === idx ? { ...m, selezionato } : m)),
  }));

  const toggleDiritto = (key, idx, selezionato) => updateUnita(key, (u) => ({
    ...u,
    diritti: u.diritti.map((d, i) => (i === idx ? { ...d, selezionato } : d)),
  }));

  const handleImport = async () => {
    const it = items[corrente];
    setLoading(true);
    setError(null);
    setStato(it.id, { stato: 'importazione' });
    let data;
    try {
      ({ data } = await visuraImportAPI.apply(proposta.upload_token, proposta));
    } catch (err) {
      setStato(it.id, { stato: 'revisione' });
      setError(formatApiError(err));
      setLoading(false);
      return;
    }
    const aggiornati = items.map((x) => (x.id === it.id ? { ...x, stato: 'importata', risultato: data } : x));
    setItems(aggiornati);
    setLoading(false);
    await analizzaDa(corrente + 1, aggiornati);
  };

  const importate = items.filter((it) => it.stato === 'importata');
  const totali = sommaRisultati(items);

  const handleClose = () => {
    if (importate.length && onImported) onImported(totali);
    onClose();
  };

  // Mid-queue, closing would silently drop the review in progress and the
  // files still waiting: ask first.
  const requestClose = () => {
    if (fase === 'revisione') setConfermaChiusura(true);
    else if (!loading) handleClose();
  };

  const fileInAnalisi = items.find((it) => it.stato === 'analisi');

  const daAnalizzare = items.filter((it) => it.stato === 'attesa').length;

  const soggettiNuovi = proposta?.soggetti.filter((s) => s.azione === 'crea') || [];
  const soggettiDaCompletare = proposta?.soggetti.filter((s) => s.azione === 'aggiorna') || [];
  const unitaNuove = proposta?.unita.filter((u) => u.azione === 'crea') || [];
  const unitaDaAggiornare = proposta?.unita.filter((u) => u.azione === 'aggiorna') || [];
  const invariati = [
    ...(proposta?.soggetti.filter((s) => s.azione === 'invariato').map((s) => s.nominativo) || []),
    ...(proposta?.unita.filter((u) => u.azione === 'invariato').map((u) => `Immobile ${unitLabel(u)}`) || []),
  ];
  const tipoMancante = unitaNuove.some((u) => u.selezionato && !(u.tipo || '').trim());

  return (
    <FormModal title="Carica da documento" size="large" onClose={requestClose} closeOnBackdrop={false}>
      <div className="visura-import">
        {error && <div className="visura-error" role="alert">{error}</div>}

        {fileInAnalisi && <LoadingSpinner message={`Analisi di ${fileInAnalisi.file.name}…`} />}

        {fase === 'scelta' && !fileInAnalisi && (
          <div className="visura-upload">
            <FormField label="Tipo documento" htmlFor="visura-tipo-documento">
              <select
                id="visura-tipo-documento"
                className="visura-select"
                value={tipoDocumento}
                onChange={(e) => setTipoDocumento(e.target.value)}
              >
                {TIPI_DOCUMENTO.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </FormField>
            <Dropzone onFiles={addFiles} disabled={loading} />
            <CodaFile items={items} corrente={-1} onRemove={loading ? null : removeFile} />
            <p className="visura-muted">
              Visure catastali per soggetto (sintetiche o analitiche) o per immobile, scaricate
              dall&apos;Agenzia delle Entrate. I file vengono analizzati uno alla volta: per ciascuno
              rivedi la proposta e confermi. Nulla viene salvato finché non confermi.
            </p>
          </div>
        )}

        {fase === 'revisione' && proposta && (
          <div className="visura-review">
            <div className="visura-progress">
              <span className="visura-progress__step">Visura {corrente + 1} di {items.length}</span>
              <span className="visura-progress__file" title={items[corrente]?.file.name}>
                {items[corrente]?.file.name}
              </span>
            </div>
            <p className="visura-summary">
              Visura {proposta.formato.toLowerCase()} n. {proposta.numero_visura} del{' '}
              {new Date(proposta.data_visura).toLocaleDateString('it-IT')}
            </p>
            <Avvisi avvisi={proposta.avvisi} />

            {soggettiNuovi.length > 0 && (
              <section>
                <h3>Anagrafiche da aggiungere</h3>
                {soggettiNuovi.map((s) => (
                  <label key={s.key} className="visura-row">
                    <input
                      type="checkbox"
                      aria-label={`Seleziona ${s.nominativo}`}
                      checked={s.selezionato}
                      onChange={(e) => updateSoggetto(s.key, { selezionato: e.target.checked })}
                    />
                    <span>
                      <strong>{s.nominativo}</strong>{' '}
                      {s.persona_giuridica ? '(ente/società)' : ''}
                      {s.codice_fiscale ? ` · CF ${s.codice_fiscale}` : ''}
                      {s.data_nascita ? ` · nato/a il ${new Date(s.data_nascita).toLocaleDateString('it-IT')}` : ''}
                      {s.luogo_nascita ? ` a ${s.luogo_nascita}` : ''}
                    </span>
                  </label>
                ))}
              </section>
            )}

            {soggettiDaCompletare.length > 0 && (
              <section>
                <h3>Anagrafiche da completare</h3>
                {soggettiDaCompletare.map((s) => (
                  <label key={s.key} className="visura-row">
                    <input
                      type="checkbox"
                      aria-label={`Seleziona ${s.nominativo}`}
                      checked={s.selezionato}
                      onChange={(e) => updateSoggetto(s.key, { selezionato: e.target.checked })}
                    />
                    <span>
                      <strong>{s.nominativo}</strong>: aggiungi{' '}
                      {s.campi_da_completare.map((c) => `${CAMPI_SOGGETTO_LABELS[c] || c.replaceAll('_', ' ')} (${formatValue(s[c])})`).join(', ')}
                    </span>
                  </label>
                ))}
              </section>
            )}

            {unitaNuove.length > 0 && (
              <section>
                <h3>Immobili da aggiungere</h3>
                {unitaNuove.map((u) => (
                  <div key={u.key} className="visura-unit">
                    <label className="visura-row">
                      <input
                        type="checkbox"
                        aria-label={`Seleziona immobile ${unitLabel(u)}`}
                        checked={u.selezionato}
                        onChange={(e) => setUnitaField(u.key, { selezionato: e.target.checked })}
                      />
                      <span>
                        <strong>{u.citta} · {unitLabel(u)}</strong> · cat. {u.categoria}
                        {u.rendita_catastale != null ? ` · rendita € ${u.rendita_catastale}` : ''}
                        {u.superficie_mq != null ? ` · ${u.superficie_mq} m²` : ''}
                      </span>
                    </label>
                    {u.selezionato && (
                      <div className="visura-unit-fields">
                        <label className={`visura-field ${!(u.tipo || '').trim() ? 'visura-field--missing' : ''}`}>
                          Tipo *
                          <input
                            list="visura-tipi"
                            aria-label={`Tipo immobile ${unitLabel(u)}`}
                            aria-invalid={!(u.tipo || '').trim()}
                            value={u.tipo || ''}
                            onChange={(e) => setUnitaField(u.key, { tipo: e.target.value })}
                          />
                          {!(u.tipo || '').trim() && <span className="visura-field__error">Obbligatorio</span>}
                        </label>
                        <label className="visura-field">
                          Indirizzo
                          <input
                            value={u.indirizzo}
                            onChange={(e) => setUnitaField(u.key, { indirizzo: e.target.value })}
                          />
                        </label>
                        <label className="visura-field visura-field--small">
                          Piano
                          <input
                            value={u.piano || ''}
                            onChange={(e) => setUnitaField(u.key, { piano: e.target.value })}
                          />
                        </label>
                      </div>
                    )}
                    <DirittiList unita={u} onToggle={(idx, v) => toggleDiritto(u.key, idx, v)} />
                    <Avvisi avvisi={u.avvisi} />
                  </div>
                ))}
                <datalist id="visura-tipi">
                  {TIPI_SUGGERITI.map((t) => <option key={t} value={t} />)}
                </datalist>
              </section>
            )}

            {unitaDaAggiornare.length > 0 && (
              <section>
                <h3>Immobili da aggiornare</h3>
                {unitaDaAggiornare.map((u) => (
                  <div key={u.key} className="visura-unit">
                    <label className="visura-row">
                      <input
                        type="checkbox"
                        aria-label={`Seleziona immobile ${unitLabel(u)}`}
                        checked={u.selezionato}
                        onChange={(e) => setUnitaField(u.key, { selezionato: e.target.checked })}
                      />
                      <span><strong>{u.citta} · {unitLabel(u)}</strong> · {u.tipo}</span>
                    </label>
                    {u.modifiche.length > 0 && (
                      <ul className="visura-modifiche">
                        {u.modifiche.map((m, idx) => (
                          <li key={m.campo}>
                            <label>
                              <input
                                type="checkbox"
                                checked={m.selezionato}
                                disabled={!u.selezionato}
                                onChange={(e) => toggleModifica(u.key, idx, e.target.checked)}
                              />
                              {' '}{CAMPO_LABELS[m.campo] || m.campo}:{' '}
                              {m.campo === 'note_catastali' ? 'aggiorna dati catastali da visura' : (
                                <>
                                  <span className="visura-old">{formatValue(m.attuale)}</span>
                                  {' → '}
                                  <span className="visura-new">{formatValue(m.nuovo)}</span>
                                </>
                              )}
                            </label>
                          </li>
                        ))}
                      </ul>
                    )}
                    <DirittiList unita={u} onToggle={(idx, v) => toggleDiritto(u.key, idx, v)} />
                    <Avvisi avvisi={u.avvisi} />
                  </div>
                ))}
              </section>
            )}

            {invariati.length > 0 && (
              <details className="visura-invariati">
                <summary>Già presenti, nessuna modifica ({invariati.length})</summary>
                <ul>{invariati.map((n) => <li key={n}>{n}</li>)}</ul>
                <p className="visura-muted">La visura verrà comunque allegata agli immobili che non la hanno già.</p>
              </details>
            )}

            {items.length > 1 && <CodaFile items={items} corrente={corrente} />}
          </div>
        )}

        {fase === 'fine' && (
          <div className="visura-result">
            <h3>
              {importate.length ? (
                <CircleCheck size={20} strokeWidth={1.7} className="visura-result__ok" aria-hidden="true" />
              ) : null}
              {importate.length
                ? `Import completato: ${importate.length} di ${items.length} visure importate`
                : 'Nessuna visura importata'}
            </h3>
            <CodaFile items={items} corrente={-1} />
            {importate.length > 0 && (
              <ul className="visura-result__totali">
                <li>Immobili creati: {totali.unita_create.length}</li>
                <li>Immobili aggiornati: {totali.unita_aggiornate.length}</li>
                <li>Anagrafiche create: {totali.soggetti_creati}</li>
                <li>Anagrafiche completate: {totali.soggetti_aggiornati}</li>
                <li>Diritti aggiunti: {totali.diritti_creati}</li>
                <li>Visure allegate: {totali.documenti_allegati}</li>
              </ul>
            )}
          </div>
        )}

        <div className="visura-actions">
          {fase === 'scelta' && (
            <>
              <Button variant="secondary" onClick={handleClose} disabled={loading}>Annulla</Button>
              <Button variant="primary" onClick={avvia} disabled={!daAnalizzare || loading} loading={loading}>
                {loading ? 'Analisi in corso…' : (daAnalizzare > 1 ? `Analizza ${daAnalizzare} file` : 'Analizza')}
              </Button>
            </>
          )}
          {fase === 'revisione' && (
            <>
              {tipoMancante && !loading && (
                <span className="visura-actions__hint">Indica il tipo per ogni immobile da aggiungere</span>
              )}
              <Button variant="secondary" onClick={salta} disabled={loading}>
                {corrente < items.length - 1 ? 'Salta questa visura' : 'Salta'}
              </Button>
              <Button
                variant="primary"
                onClick={handleImport}
                disabled={loading || tipoMancante}
                loading={loading}
                title={tipoMancante ? 'Indica il tipo per tutti gli immobili da aggiungere' : undefined}
              >
                {loading ? 'Importazione…' : 'Importa'}
              </Button>
            </>
          )}
          {fase === 'fine' && <Button variant="primary" onClick={handleClose}>Chiudi</Button>}
        </div>
      </div>
      <ConfirmDialog
        isOpen={confermaChiusura}
        title="Interrompere l'importazione?"
        message="La visura in revisione e quelle ancora in coda non verranno importate. Quelle già importate restano salvate."
        confirmLabel="Interrompi"
        cancelLabel="Continua"
        onConfirm={() => { setConfermaChiusura(false); handleClose(); }}
        onCancel={() => setConfermaChiusura(false)}
      />
    </FormModal>
  );
}

export default ImportVisuraModal;
