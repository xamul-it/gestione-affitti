import { useCallback, useEffect, useId, useMemo, useState } from 'react';
import { useToast } from '../../hooks/useToast';
import { ChevronDown, ChevronRight, Download, Eye, FileText, Plus, Trash2 } from 'lucide-react';
import { documentiAPI } from '../../../services/documentiAPI';
import { formatApiError } from '../../../utils/errorHandling';
import { FormModal } from '../FormBuilder/FormModal';
import { ConfirmDialog } from '../common/ConfirmDialog';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { Badge, Button } from '../../../components/UI';
import DocumentoUpload from './DocumentoUpload';
import DocumentoPreview from './DocumentoPreview';
import { formatDate, statoScadenza } from './documentiUtils';
import { scaricaDocumento as scarica } from './scaricaDocumento';
import './Documenti.css';

const ALTRO = '__altro__';

function groupKey(d) {
  return `${d.tipo_codice || ALTRO}|${d.sottotipo || ''}`;
}

function RigaDocumento({ documento, tipo, storico = [], onPreview, onDelete }) {
  const [aperto, setAperto] = useState(false);
  const badge = statoScadenza(documento, tipo);
  const titolo = documento.tipo_nome || 'Altro documento';
  const sottotipo = documento.sottotipo ? ` · ${documento.sottotipo.charAt(0)}${documento.sottotipo.slice(1).toLowerCase()}` : '';

  return (
    <li className="doc-row">
      <div className="doc-row__main">
        <FileText size={18} className="doc-row__icon" aria-hidden="true" />
        <div className="doc-row__info">
          <span className="doc-row__titolo">{titolo}{sottotipo}</span>
          <span className="doc-muted">
            {documento.data_riferimento ? `del ${formatDate(documento.data_riferimento)}` : ''}
            {documento.data_scadenza_effettiva ? ` · scade il ${formatDate(documento.data_scadenza_effettiva)}` : ''}
            {documento.descrizione ? ` · ${documento.descrizione}` : ''}
          </span>
        </div>
        {badge && <Badge variant={badge.variant}>{badge.label}</Badge>}
        <div className="doc-row__actions">
          <button type="button" className="doc-icon-btn" onClick={() => onPreview(documento)} aria-label={`Anteprima ${titolo}`}>
            <Eye size={18} aria-hidden="true" />
          </button>
          <button type="button" className="doc-icon-btn" onClick={() => scarica(documento)} aria-label={`Scarica ${titolo}`}>
            <Download size={18} aria-hidden="true" />
          </button>
          <button type="button" className="doc-icon-btn doc-icon-btn--danger" onClick={() => onDelete(documento)} aria-label={`Elimina ${titolo}`}>
            <Trash2 size={18} aria-hidden="true" />
          </button>
        </div>
      </div>
      {storico.length > 0 && (
        <div className="doc-storico">
          <button type="button" className="doc-link" onClick={() => setAperto((v) => !v)} aria-expanded={aperto}>
            {aperto ? <ChevronDown size={16} aria-hidden="true" /> : <ChevronRight size={16} aria-hidden="true" />}
            Storico ({storico.length})
          </button>
          {aperto && (
            <ul className="doc-storico__list">
              {storico.map((s) => (
                <li key={s.id}>
                  <Badge variant="neutral">Sostituito</Badge>
                  <span>{formatDate(s.data_riferimento)}</span>
                  <span className="doc-muted doc-storico__file">{s.nome_file}</span>
                  <button type="button" className="doc-icon-btn" onClick={() => onPreview(s)} aria-label={`Anteprima del ${formatDate(s.data_riferimento)}`}>
                    <Eye size={16} aria-hidden="true" />
                  </button>
                  <button type="button" className="doc-icon-btn" onClick={() => scarica(s)} aria-label={`Scarica del ${formatDate(s.data_riferimento)}`}>
                    <Download size={16} aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </li>
  );
}

/**
 * Documents of one entity (core): the documents in force grouped by type,
 * the history of the superseded ones, preview, download and typed upload.
 */
export default function DocumentiPanel({ entityType, entityId, title = 'Documenti' }) {
  const [tipi, setTipi] = useState([]);
  const [documenti, setDocumenti] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [upload, setUpload] = useState(false);
  const [preview, setPreview] = useState(null);
  const [daEliminare, setDaEliminare] = useState(null);
  const titleId = useId();
  const toast = useToast();

  const carica = useCallback(async () => {
    if (!entityId) return;
    setLoading(true);
    try {
      const [t, d] = await Promise.all([
        documentiAPI.getTipi(entityType),
        documentiAPI.list({ entity_type: entityType, entity_id: entityId, includi_sostituiti: true }),
      ]);
      setTipi(t.data || []);
      setDocumenti(d.data || []);
      setError(null);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }, [entityType, entityId]);

  useEffect(() => { carica(); }, [carica]);

  const tipiByCodice = useMemo(() => Object.fromEntries(tipi.map((t) => [t.codice, t])), [tipi]);

  const righe = useMemo(() => {
    const storicoByKey = {};
    documenti.filter((d) => d.stato === 'SOSTITUITO').forEach((d) => {
      (storicoByKey[groupKey(d)] ||= []).push(d);
    });
    const correnti = documenti.filter((d) => d.stato !== 'SOSTITUITO');
    const ordine = (d) => tipi.findIndex((t) => t.codice === d.tipo_codice);
    return correnti
      .sort((a, b) => (ordine(a) - ordine(b)) || (b.data_riferimento || '').localeCompare(a.data_riferimento || ''))
      .map((d) => ({
        documento: d,
        storico: d.regime === 'SOSTITUTIVO' ? (storicoByKey[groupKey(d)] || []) : [],
      }));
  }, [documenti, tipi]);

  const elimina = async () => {
    try {
      await documentiAPI.remove(daEliminare.id);
      setDaEliminare(null);
      toast.success('Documento eliminato');
      carica();
    } catch (err) {
      setDaEliminare(null);
      setError(formatApiError(err));
    }
  };

  if (!entityId) return null;

  return (
    <section className="doc-panel" aria-labelledby={titleId}>
      <header className="doc-panel__header">
        <h3 id={titleId}>{title}</h3>
        <Button variant="secondary" size="sm" onClick={() => setUpload(true)}>
          <Plus size={16} aria-hidden="true" /> Carica documento
        </Button>
      </header>

      {error && <div className="doc-error" role="alert">{error}</div>}
      {loading ? (
        <LoadingSpinner message="Caricamento documenti…" />
      ) : righe.length === 0 ? (
        <p className="doc-empty">Nessun documento</p>
      ) : (
        <ul className="doc-list">
          {righe.map(({ documento, storico }) => (
            <RigaDocumento
              key={documento.id}
              documento={documento}
              tipo={tipiByCodice[documento.tipo_codice]}
              storico={storico}
              onPreview={setPreview}
              onDelete={setDaEliminare}
            />
          ))}
        </ul>
      )}

      {upload && (
        <FormModal title="Carica documento" onClose={() => setUpload(false)} closeOnBackdrop={false} size="large">
          <DocumentoUpload
            entityType={entityType}
            entityId={entityId}
            tipi={tipi}
            onSaved={() => { setUpload(false); toast.success('Documento caricato'); carica(); }}
            onCancel={() => setUpload(false)}
          />
        </FormModal>
      )}
      {preview && <DocumentoPreview documento={preview} onClose={() => setPreview(null)} />}
      <ConfirmDialog
        isOpen={Boolean(daEliminare)}
        title="Eliminare il documento?"
        message={daEliminare?.regime === 'SOSTITUTIVO' && daEliminare?.stato === 'CORRENTE'
          ? 'Il file viene eliminato. Se c’è una versione precedente, torna in vigore.'
          : 'Il file viene eliminato definitivamente.'}
        confirmLabel="Elimina"
        variant="danger"
        onConfirm={elimina}
        onCancel={() => setDaEliminare(null)}
      />
    </section>
  );
}
