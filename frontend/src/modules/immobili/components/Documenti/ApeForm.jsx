import { useEffect, useState } from 'react';
import { FileText, X } from 'lucide-react';
import { documentiAPI } from '../../../../services/documentiAPI';
import { tecniciAPI } from '../../../../services/api';
import { formatApiError } from '../../../../utils/errorHandling';
import { Button, FormField } from '../../../../components/UI';
import FileDropzone from '../../../../core/components/Documenti/FileDropzone';
import { addMonthsIso, formatDate } from '../../../../core/components/Documenti/documentiUtils';
import './ApeForm.css';

const CLASSI = ['A4', 'A3', 'A2', 'A1', 'B', 'C', 'D', 'E', 'F', 'G'];

function parseDecimal(value) {
  if (value === '' || value == null) return null;
  const n = Number(String(value).replace(',', '.'));
  return Number.isFinite(n) ? n : NaN;
}

/**
 * Document form of the APE type (attestato di prestazione energetica):
 * energy class, EPgl,nren, identification code, certifier, emission date
 * (the expiry is 10 years later, computed by the server) and the optional
 * date from which it lapsed because the heating system checks were not done.
 */
export default function ApeForm({ entityType, entityId, tipo, initialFiles = [], onSaved, onCancel }) {
  const [files, setFiles] = useState(initialFiles);
  const [classe, setClasse] = useState('');
  const [epgl, setEpgl] = useState('');
  const [codice, setCodice] = useState('');
  const [tecnicoId, setTecnicoId] = useState('');
  const [emissione, setEmissione] = useState('');
  const [decaduto, setDecaduto] = useState('');
  const [tecnici, setTecnici] = useState([]);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    tecniciAPI.getAll(true).then((r) => setTecnici(r.data || [])).catch(() => setTecnici([]));
  }, []);

  const mesi = tipo?.scadenza?.mesi || 120;
  const scadenza = emissione ? addMonthsIso(emissione, mesi) : null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!classe) return setError('Indica la classe energetica');
    if (!emissione) return setError("Indica la data di emissione dell'APE");
    const ep = parseDecimal(epgl);
    if (Number.isNaN(ep)) return setError('EPgl,nren deve essere un numero');
    if (!files.length) return setError("Aggiungi il file dell'APE");

    const fd = new FormData();
    fd.append('entity_type', entityType);
    fd.append('entity_id', entityId);
    fd.append('tipo_codice', 'APE');
    fd.append('data_riferimento', emissione);
    fd.append('dati', JSON.stringify({
      classe,
      ep_gl_nren: ep,
      codice_identificativo: codice.trim() || null,
      tecnico_id: tecnicoId ? Number(tecnicoId) : null,
      decaduto_il: decaduto || null,
    }));
    fd.append('descrizione', `APE classe ${classe}`);
    files.forEach((f) => fd.append('files', f));

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
    <form className="ape-form" onSubmit={handleSubmit} noValidate>
      {files.length ? (
        <ul className="doc-filelist">
          {files.map((f, idx) => (
            <li key={`${f.name}-${idx}`}>
              <FileText size={16} aria-hidden="true" />
              <span className="doc-filelist__nome">{f.name}</span>
              <button type="button" className="doc-icon-btn" aria-label={`Rimuovi ${f.name}`}
                onClick={() => setFiles((prev) => prev.filter((_, i) => i !== idx))}>
                <X size={16} aria-hidden="true" />
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <FileDropzone onFiles={(nuovi) => setFiles((prev) => [...prev, ...nuovi])} title="Trascina qui il PDF dell'APE"
          inputLabel="File dell'APE" id="ape-dropzone" />
      )}

      <div className="ape-form__grid">
        <FormField label="Classe energetica" htmlFor="ape-classe">
          <select id="ape-classe" className="doc-input" value={classe} onChange={(e) => setClasse(e.target.value)} required>
            <option value="">Scegli…</option>
            {CLASSI.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </FormField>
        <FormField label="EPgl,nren (kWh/m² anno)" htmlFor="ape-epgl">
          <input id="ape-epgl" className="doc-input" inputMode="decimal" value={epgl} onChange={(e) => setEpgl(e.target.value)} />
        </FormField>
        <FormField label="Codice identificativo" htmlFor="ape-codice">
          <input id="ape-codice" className="doc-input" value={codice} maxLength={100} onChange={(e) => setCodice(e.target.value)} />
        </FormField>
        <FormField label="Certificatore" htmlFor="ape-tecnico">
          <select id="ape-tecnico" className="doc-input" value={tecnicoId} onChange={(e) => setTecnicoId(e.target.value)}>
            <option value="">Non indicato</option>
            {tecnici.map((t) => <option key={t.id} value={t.id}>{`${t.nome} ${t.cognome}`}</option>)}
          </select>
        </FormField>
        <FormField label="Data di emissione" htmlFor="ape-emissione">
          <input id="ape-emissione" type="date" className="doc-input" value={emissione} onChange={(e) => setEmissione(e.target.value)} required />
        </FormField>
        <FormField label="Decaduto il (facoltativo)" htmlFor="ape-decaduto">
          <input id="ape-decaduto" type="date" className="doc-input" value={decaduto} onChange={(e) => setDecaduto(e.target.value)}
            aria-describedby="ape-decaduto-hint" />
        </FormField>
      </div>
      <p id="ape-decaduto-hint" className="doc-muted">
        Compila &laquo;Decaduto il&raquo; se i controlli dell&apos;impianto termico non sono stati fatti: l&apos;APE perde validità prima dei 10 anni.
      </p>
      {scadenza && <p className="ape-form__scadenza">Scade il {formatDate(scadenza)}</p>}

      {error && <div className="doc-error" role="alert">{error}</div>}
      <div className="doc-actions">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={saving}>Annulla</Button>
        <Button type="submit" variant="primary" disabled={saving}>{saving ? 'Salvataggio…' : 'Salva'}</Button>
      </div>
    </form>
  );
}
