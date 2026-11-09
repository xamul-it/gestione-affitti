import { useEffect, useState } from 'react';
import { documentiAPI } from '../../../services/documentiAPI';
import { FormModal } from '../FormBuilder/FormModal';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { formatDate } from './documentiUtils';
import './Documenti.css';

/**
 * Preview of a document's first file. The API serves inline only PDFs and
 * images (detected server-side); anything else gets a download hint.
 */
export default function DocumentoPreview({ documento, onClose }) {
  const [url, setUrl] = useState(null);
  const [tipo, setTipo] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let objectUrl = null;
    let cancelled = false;
    documentiAPI.view(documento.id)
      .then((res) => {
        if (cancelled) return;
        const blob = res.data;
        objectUrl = window.URL.createObjectURL(blob);
        setTipo(blob.type || '');
        setUrl(objectUrl);
      })
      .catch(() => { if (!cancelled) setError('Anteprima non disponibile: scarica il documento per aprirlo.'); });
    return () => {
      cancelled = true;
      if (objectUrl) window.URL.revokeObjectURL(objectUrl);
    };
  }, [documento.id]);

  const titolo = `${documento.tipo_nome || 'Documento'}${documento.data_riferimento ? ` del ${formatDate(documento.data_riferimento)}` : ''}`;
  const anteprimabile = tipo === 'application/pdf' || tipo?.startsWith('image/');

  return (
    <FormModal title={titolo} onClose={onClose} size="large">
      <div className="doc-preview">
        {error && <div className="doc-error" role="alert">{error}</div>}
        {!error && !url && <LoadingSpinner message="Caricamento anteprima…" />}
        {url && anteprimabile && tipo === 'application/pdf' && (
          <iframe title={titolo} src={url} className="doc-preview__frame" />
        )}
        {url && anteprimabile && tipo !== 'application/pdf' && (
          <img src={url} alt={titolo} className="doc-preview__img" />
        )}
        {url && !anteprimabile && (
          <p className="doc-muted">Anteprima non disponibile per questo tipo di file: scaricalo per aprirlo.</p>
        )}
      </div>
    </FormModal>
  );
}
