import { useEffect, useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { unitaImmobiliariAPI, categorieCatastaliAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import { LoadingSpinner } from '../../../../core/components/common/LoadingSpinner';
import { Badge } from '../../../../components/UI';
import { formatDate } from '../../../../core/components/Documenti/documentiUtils';
import { euro, mq } from './formatters';

const CAMPI = {
  categoria_catastale_id: 'Categoria catastale',
  rendita_catastale: 'Rendita catastale',
  superficie_mq: 'Superficie',
  foglio: 'Foglio',
  particella: 'Particella',
  subalterno: 'Subalterno',
  indirizzo: 'Indirizzo',
  piano: 'Piano',
};

/** Catastal changes of a unit (from imported visure and manual edits), newest first. */
export default function VariazioniCatastali({ unitaId }) {
  const [righe, setRighe] = useState([]);
  const [categorie, setCategorie] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let attivo = true;
    setLoading(true);
    unitaImmobiliariAPI.getVariazioniCatastali(unitaId)
      .then((r) => { if (attivo) { setRighe(r.data || []); setError(null); } })
      .catch((err) => { if (attivo) setError(formatApiError(err)); })
      .finally(() => { if (attivo) setLoading(false); });
    categorieCatastaliAPI.getAll()
      .then((r) => { if (attivo) setCategorie(Object.fromEntries((r.data || []).map((c) => [String(c.id), c.codice]))); })
      .catch(() => {});
    return () => { attivo = false; };
  }, [unitaId]);

  const valore = (campo, v) => {
    if (v === null || v === undefined || v === '') return '—';
    if (campo === 'rendita_catastale') return euro(v);
    if (campo === 'superficie_mq') return mq(v);
    if (campo === 'categoria_catastale_id') return categorie[String(v)] || `#${v}`;
    return v;
  };

  if (loading) return <LoadingSpinner message="Caricamento variazioni…" />;
  if (error) return <div className="scheda-error" role="alert">{error}</div>;
  if (!righe.length) return <p className="scheda-empty">Nessuna variazione registrata</p>;

  return (
    <div className="scheda-table-wrap">
      <table className="scheda-table">
        <thead>
          <tr>
            <th scope="col">Data</th>
            <th scope="col">Dato</th>
            <th scope="col">Prima</th>
            <th scope="col" aria-label="Diventa" />
            <th scope="col">Dopo</th>
            <th scope="col">Origine</th>
          </tr>
        </thead>
        <tbody>
          {righe.map((r) => (
            <tr key={r.id}>
              <td>{formatDate(r.data_riferimento)}</td>
              <td>{CAMPI[r.campo] || r.campo}</td>
              <td className="scheda-old">{valore(r.campo, r.valore_precedente)}</td>
              <td aria-hidden="true"><ArrowRight size={14} /></td>
              <td className="scheda-new">{valore(r.campo, r.valore_nuovo)}</td>
              <td>
                <Badge variant={r.origine === 'VISURA' ? 'brand' : 'neutral'}>
                  {r.origine === 'VISURA' ? 'Da visura' : 'Modifica manuale'}
                </Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
