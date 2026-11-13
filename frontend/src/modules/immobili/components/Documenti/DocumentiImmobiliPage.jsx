import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Download, Eye } from 'lucide-react';
import { documentiAPI } from '../../../../services/documentiAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import { LoadingSpinner } from '../../../../core/components/common/LoadingSpinner';
import { Badge, FormField } from '../../../../components/UI';
import DocumentoPreview from '../../../../core/components/Documenti/DocumentoPreview';
import { scaricaDocumento } from '../../../../core/components/Documenti/scaricaDocumento';
import { formatDate, statoScadenza } from '../../../../core/components/Documenti/documentiUtils';
import '../../../../core/components/Documenti/Documenti.css';
import CaricamentoDocumenti from './CaricamentoDocumenti';
import './DocumentiImmobiliPage.css';

const SCADENZE = [
  { value: '', label: 'Tutte' },
  { value: '0', label: 'Scaduti' },
  { value: '90', label: 'Scaduti o in scadenza entro 90 giorni' },
  { value: '365', label: 'Entro un anno' },
];

/**
 * All the documents of the immobili module (/immobili/documenti), filterable
 * by type, history and expiry. Filters live in the URL (?tipo=APE&sostituiti=1&scadenza=90).
 */
export default function DocumentiImmobiliPage() {
  const [params, setParams] = useSearchParams();
  const tipo = params.get('tipo') || '';
  const sostituiti = params.get('sostituiti') === '1';
  const scadenza = params.get('scadenza') || '';

  const [tipi, setTipi] = useState([]);
  const [documenti, setDocumenti] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [preview, setPreview] = useState(null);
  const [versione, setVersione] = useState(0);

  const setFiltro = (key, value) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value); else next.delete(key);
    setParams(next, { replace: true });
  };

  useEffect(() => {
    documentiAPI.getTipi('IMMOBILE').then((r) => setTipi(r.data || [])).catch(() => setTipi([]));
  }, []);

  useEffect(() => {
    let attivo = true;
    setLoading(true);
    const query = { entity_type: 'IMMOBILE', modulo: 'immobili', includi_sostituiti: sostituiti, limit: 500 };
    if (tipo) query.tipo_codice = tipo;
    if (scadenza !== '') query.scadenza_entro_giorni = Number(scadenza);
    documentiAPI.list(query)
      .then((r) => { if (attivo) { setDocumenti(r.data || []); setError(null); } })
      .catch((err) => { if (attivo) setError(formatApiError(err)); })
      .finally(() => { if (attivo) setLoading(false); });
    return () => { attivo = false; };
  }, [tipo, sostituiti, scadenza, versione]);

  const tipiByCodice = useMemo(() => Object.fromEntries(tipi.map((t) => [t.codice, t])), [tipi]);

  return (
    <div className="documenti-immobili">
      <header className="documenti-immobili__header">
        <h2>Documenti</h2>
        <p className="doc-muted">Visure, APE, planimetrie e gli altri documenti di tutte le unità immobiliari.</p>
      </header>

      <CaricamentoDocumenti onCaricato={() => setVersione((v) => v + 1)} />

      <div className="documenti-immobili__filtri">
        <FormField label="Tipologia" htmlFor="doc-filtro-tipo">
          <select id="doc-filtro-tipo" className="doc-input" value={tipo} onChange={(e) => setFiltro('tipo', e.target.value)}>
            <option value="">Tutte</option>
            {tipi.map((t) => <option key={t.codice} value={t.codice}>{t.nome}</option>)}
          </select>
        </FormField>
        <FormField label="Scadenza" htmlFor="doc-filtro-scadenza">
          <select id="doc-filtro-scadenza" className="doc-input" value={scadenza} onChange={(e) => setFiltro('scadenza', e.target.value)}>
            {SCADENZE.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
        </FormField>
        <label className="documenti-immobili__check">
          <input type="checkbox" checked={sostituiti} onChange={(e) => setFiltro('sostituiti', e.target.checked ? '1' : '')} />
          Mostra anche i sostituiti
        </label>
      </div>

      {error && <div className="doc-error" role="alert">{error}</div>}
      {loading ? (
        <LoadingSpinner message="Caricamento documenti…" />
      ) : documenti.length === 0 ? (
        <p className="doc-empty">Nessun documento</p>
      ) : (
        <div className="documenti-immobili__table-wrap">
          <table className="documenti-immobili__table">
            <thead>
              <tr>
                <th scope="col">Immobile</th>
                <th scope="col">Tipologia</th>
                <th scope="col">Data</th>
                <th scope="col">Scadenza</th>
                <th scope="col"><span className="sr-only">Azioni</span></th>
              </tr>
            </thead>
            <tbody>
              {documenti.map((d) => {
                const badge = statoScadenza(d, tipiByCodice[d.tipo_codice]);
                return (
                  <tr key={d.id} className={d.stato === 'SOSTITUITO' ? 'is-sostituito' : ''}>
                    <td data-label="Immobile"><Link to={`/beni/${d.entity_id}`}>{d.entity_label || `Immobile #${d.entity_id}`}</Link></td>
                    <td data-label="Tipologia">
                      {d.tipo_nome || 'Altro documento'}
                      {d.sottotipo ? ` · ${d.sottotipo.charAt(0)}${d.sottotipo.slice(1).toLowerCase()}` : ''}
                      {d.stato === 'SOSTITUITO' && <> <Badge variant="neutral">Sostituito</Badge></>}
                    </td>
                    <td data-label="Data">{formatDate(d.data_riferimento)}</td>
                    <td data-label="Scadenza">
                      {d.data_scadenza_effettiva ? formatDate(d.data_scadenza_effettiva) : '—'}
                      {badge && d.stato !== 'SOSTITUITO' && <> <Badge variant={badge.variant}>{badge.label}</Badge></>}
                    </td>
                    <td className="documenti-immobili__azioni">
                      <button type="button" className="doc-icon-btn" onClick={() => setPreview(d)} aria-label={`Anteprima ${d.tipo_nome || 'documento'} ${d.entity_label || ''}`}>
                        <Eye size={18} aria-hidden="true" />
                      </button>
                      <button type="button" className="doc-icon-btn" onClick={() => scaricaDocumento(d)} aria-label={`Scarica ${d.tipo_nome || 'documento'} ${d.entity_label || ''}`}>
                        <Download size={18} aria-hidden="true" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {preview && <DocumentoPreview documento={preview} onClose={() => setPreview(null)} />}
    </div>
  );
}
