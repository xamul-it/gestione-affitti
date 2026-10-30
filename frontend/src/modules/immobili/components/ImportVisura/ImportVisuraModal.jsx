import { useState } from 'react';
import { visuraImportAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import './ImportVisuraModal.css';

/**
 * "Carica da documento" for unità immobiliari.
 *
 * Step 1: choose document type + PDF → backend builds a proposal (nothing saved).
 * Step 2: review: anagrafiche/immobili to add or update, rights, warnings;
 *         every row can be deselected, tipo is editable (required for new units).
 * Step 3: result counts.
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
      {avvisi.map((a) => <li key={a}>⚠️ {a}</li>)}
    </ul>
  );
}

function ImportVisuraModal({ onClose, onImported }) {
  const [tipoDocumento, setTipoDocumento] = useState('VISURA_CATASTALE');
  const [file, setFile] = useState(null);
  const [proposta, setProposta] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await visuraImportAPI.preview(file, tipoDocumento);
      setProposta(data);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
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
    setLoading(true);
    setError(null);
    try {
      const { data } = await visuraImportAPI.apply(proposta.upload_token, proposta);
      setResult(data);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (result && onImported) onImported(result);
    onClose();
  };

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
    <div className="modal-overlay">
      <div className="modal-content visura-modal" role="dialog" aria-label="Carica da documento">
        <div className="modal-header">
          <h2>Carica da documento</h2>
          <button className="close-btn" onClick={handleClose} aria-label="Chiudi">×</button>
        </div>

        <div className="modal-body">
          {error && <div className="visura-error" role="alert">{error}</div>}

          {!proposta && (
            <div className="visura-upload">
              <label className="visura-field">
                Tipo documento
                <select value={tipoDocumento} onChange={(e) => setTipoDocumento(e.target.value)}>
                  {TIPI_DOCUMENTO.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </label>
              <label className="visura-field">
                File PDF
                <input
                  type="file"
                  accept="application/pdf,.pdf"
                  onChange={(e) => { setFile(e.target.files[0] || null); setError(null); }}
                />
              </label>
              <p className="visura-muted">
                Visura catastale per soggetto (sintetica o analitica) scaricata dall&apos;Agenzia delle Entrate.
                Nulla viene salvato finché non confermi.
              </p>
            </div>
          )}

          {proposta && !result && (
            <div className="visura-review">
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
                        {s.campi_da_completare.map((c) => `${c.replace('_', ' ')} (${formatValue(s[c])})`).join(', ')}
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
                              value={u.tipo || ''}
                              onChange={(e) => setUnitaField(u.key, { tipo: e.target.value })}
                            />
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
            </div>
          )}

          {result && (
            <div className="visura-result">
              <h3>Import completato</h3>
              <ul>
                <li>Immobili creati: {result.unita_create.length}</li>
                <li>Immobili aggiornati: {result.unita_aggiornate.length}</li>
                <li>Anagrafiche create: {result.soggetti_creati}</li>
                <li>Anagrafiche completate: {result.soggetti_aggiornati}</li>
                <li>Diritti aggiunti: {result.diritti_creati}</li>
                <li>Visure allegate: {result.documenti_allegati}</li>
              </ul>
            </div>
          )}
        </div>

        <div className="modal-footer">
          {!result && (
            <button className="btn-secondary" onClick={proposta ? () => setProposta(null) : onClose}>
              {proposta ? 'Indietro' : 'Annulla'}
            </button>
          )}
          {!proposta && (
            <button className="btn-primary" onClick={handleAnalyze} disabled={!file || loading}>
              {loading ? 'Analisi in corso…' : 'Analizza'}
            </button>
          )}
          {proposta && !result && (
            <button
              className="btn-primary"
              onClick={handleImport}
              disabled={loading || tipoMancante}
              title={tipoMancante ? 'Indica il tipo per tutti gli immobili da aggiungere' : undefined}
            >
              {loading ? 'Importazione…' : 'Importa'}
            </button>
          )}
          {result && <button className="btn-primary" onClick={handleClose}>Chiudi</button>}
        </div>
      </div>
    </div>
  );
}

export default ImportVisuraModal;
