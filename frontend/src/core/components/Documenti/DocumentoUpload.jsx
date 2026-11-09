import { useEffect, useRef, Suspense, useMemo, useState } from 'react';
import { FileText, X } from 'lucide-react';
import { documentiAPI } from '../../../services/documentiAPI';
import { formatApiError } from '../../../utils/errorHandling';
import { getDocumentForm } from '../../documenti/documentForms';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { Button, FormField } from '../../../components/UI';
import FileDropzone from './FileDropzone';
import { addMonthsIso, fileSize, formatDate, todayIso } from './documentiUtils';
import './Documenti.css';

/**
 * Typed document upload (core). The document types come from the API
 * (GET /documenti/tipi), as declared by the modules' manifests:
 * - a type with a `form` opens the form its module registered
 *   (core/documenti/documentForms.js), receiving the files dropped here;
 * - otherwise: files, date of the document, sottotipo and expiry date
 *   (required when the type's scadenza is manual, computed when it is N months).
 */
export default function DocumentoUpload({ entityType, entityId, tipi = [], initialTipoCodice = '', onSaved, onCancel }) {
  const [tipoCodice, setTipoCodice] = useState(initialTipoCodice);
  const [files, setFiles] = useState([]);
  const [dataRiferimento, setDataRiferimento] = useState(todayIso());
  const [sottotipo, setSottotipo] = useState('');
  const [dataScadenza, setDataScadenza] = useState('');
  const [descrizione, setDescrizione] = useState('');
  const [error, setError] = useState(null);
  const errorRef = useRef(null);
  // Bring the validation/API error into view in tall modals.
  useEffect(() => { if (error) errorRef.current?.focus(); }, [error]);
  const [saving, setSaving] = useState(false);

  const tipo = tipi.find((t) => t.codice === tipoCodice) || null;
  const ModuleForm = tipo?.form ? getDocumentForm(tipo.form) : null;

  const gruppi = useMemo(() => {
    const byCat = {};
    tipi.forEach((t) => { (byCat[t.categoria || 'altro'] ||= []).push(t); });
    return Object.entries(byCat).sort(([a], [b]) => a.localeCompare(b));
  }, [tipi]);

  const scadenzaManuale = Boolean(tipo?.scadenza?.manuale);
  const scadenzaCalcolata = tipo?.scadenza?.mesi ? addMonthsIso(dataRiferimento, tipo.scadenza.mesi) : null;

  const addFiles = (nuovi) => setFiles((prev) => [...prev, ...nuovi]);
  const removeFile = (idx) => setFiles((prev) => prev.filter((_, i) => i !== idx));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!tipo) return setError('Scegli la tipologia del documento');
    if (!files.length) return setError('Aggiungi almeno un file');
    if (scadenzaManuale && !dataScadenza) return setError('Indica la data di scadenza');
    if (tipo.sottotipi?.length && !sottotipo) return setError('Scegli il sottotipo');

    const fd = new FormData();
    fd.append('entity_type', entityType);
    fd.append('entity_id', entityId);
    fd.append('tipo_codice', tipo.codice);
    fd.append('data_riferimento', dataRiferimento);
    files.forEach((f) => fd.append('files', f));
    if (sottotipo) fd.append('sottotipo', sottotipo);
    if (scadenzaManuale) fd.append('data_scadenza', dataScadenza);
    if (descrizione.trim()) fd.append('descrizione', descrizione.trim());

    setSaving(true);
    try {
      const res = await documentiAPI.upload(fd);
      onSaved?.(res.data);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="doc-upload">
      <FormField label="Tipologia" htmlFor="doc-upload-tipo">
        <select
          id="doc-upload-tipo"
          className="doc-input"
          value={tipoCodice}
          onChange={(e) => { setTipoCodice(e.target.value); setSottotipo(''); setError(null); }}
          required
        >
          <option value="" disabled>Scegli…</option>
          {gruppi.map(([categoria, lista]) => (
            <optgroup key={categoria} label={categoria.charAt(0).toUpperCase() + categoria.slice(1)}>
              {lista.map((t) => <option key={t.codice} value={t.codice}>{t.nome}</option>)}
            </optgroup>
          ))}
        </select>
      </FormField>

      {!ModuleForm && (
        <>
          <FileDropzone onFiles={addFiles} disabled={saving} />
          {files.length > 0 && (
            <ul className="doc-filelist">
              {files.map((f, idx) => (
                <li key={`${f.name}-${idx}`}>
                  <FileText size={16} aria-hidden="true" />
                  <span className="doc-filelist__nome">{f.name}</span>
                  <span className="doc-muted">{fileSize(f.size)}</span>
                  <button type="button" className="doc-icon-btn" onClick={() => removeFile(idx)} aria-label={`Rimuovi ${f.name}`}>
                    <X size={16} aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </>
      )}

      {ModuleForm ? (
        <Suspense fallback={<LoadingSpinner message="Caricamento modulo…" />}>
          <ModuleForm
            entityType={entityType}
            entityId={entityId}
            tipo={tipo}
            initialFiles={files}
            onSaved={onSaved}
            onCancel={onCancel}
          />
        </Suspense>
      ) : (
        <form className="doc-upload__form" onSubmit={handleSubmit} noValidate>
          {tipo?.descrizione && <p className="doc-muted">{tipo.descrizione}</p>}
          <div className="doc-upload__row">
            <FormField label="Data del documento" htmlFor="doc-upload-data">
              <input id="doc-upload-data" type="date" className="doc-input" value={dataRiferimento}
                onChange={(e) => setDataRiferimento(e.target.value)} required />
            </FormField>
            {tipo?.sottotipi?.length > 0 && (
              <FormField label="Sottotipo" htmlFor="doc-upload-sottotipo">
                <select id="doc-upload-sottotipo" className="doc-input" value={sottotipo}
                  onChange={(e) => setSottotipo(e.target.value)} required>
                  <option value="" disabled>Scegli…</option>
                  {tipo.sottotipi.map((s) => (
                    <option key={s} value={s}>{s.charAt(0) + s.slice(1).toLowerCase()}</option>
                  ))}
                </select>
              </FormField>
            )}
            {scadenzaManuale && (
              <FormField label="Data di scadenza" htmlFor="doc-upload-scadenza">
                <input id="doc-upload-scadenza" type="date" className="doc-input" value={dataScadenza}
                  onChange={(e) => setDataScadenza(e.target.value)} required />
              </FormField>
            )}
          </div>
          {scadenzaCalcolata && (
            <p className="doc-muted">Scade il {formatDate(scadenzaCalcolata)}</p>
          )}
          {tipo?.regime === 'SOSTITUTIVO' && (
            <p className="doc-muted">
              Se è più recente, sostituisce il documento in vigore, che resta nello storico.
            </p>
          )}
          <FormField label="Descrizione (facoltativa)" htmlFor="doc-upload-descrizione">
            <input id="doc-upload-descrizione" type="text" className="doc-input" value={descrizione}
              maxLength={500} onChange={(e) => setDescrizione(e.target.value)} />
          </FormField>
          {error && <div className="doc-error" role="alert" ref={errorRef} tabIndex={-1}>{error}</div>}
          <div className="doc-actions">
            <Button type="button" variant="secondary" onClick={onCancel} disabled={saving}>Annulla</Button>
            <Button type="submit" variant="primary" disabled={saving}>{saving ? 'Caricamento…' : 'Carica'}</Button>
          </div>
        </form>
      )}
    </div>
  );
}
