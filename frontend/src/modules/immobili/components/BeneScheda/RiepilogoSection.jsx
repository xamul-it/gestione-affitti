import { useEffect, useId, useState } from 'react';
import { LoadingSpinner } from '../../../../core/components/common/LoadingSpinner';
import { beniAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';

const oggi = () => new Date().toISOString().slice(0, 10);

function quota(q) {
  if (q === null || q === undefined) return '—';
  return `${Number(q).toLocaleString('it-IT', { maximumFractionDigits: 2 })}%`;
}

/**
 * "Chi paga cosa": who each item goes to at a date (rights and tenants),
 * never how much. Hidden without permission on owners' and tenants' names.
 */
export default function RiepilogoSection({ beneId }) {
  const uid = useId();
  const [data, setData] = useState(oggi());
  const [riepilogo, setRiepilogo] = useState(null);
  const [nascosta, setNascosta] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let attivo = true;
    setLoading(true);
    beniAPI.getRiepilogo(beneId, data || undefined)
      .then((r) => { if (attivo) { setRiepilogo(r.data); setError(null); } })
      .catch((err) => {
        if (!attivo) return;
        if (err?.response?.status === 403) setNascosta(true);
        else setError(formatApiError(err));
      })
      .finally(() => { if (attivo) setLoading(false); });
    return () => { attivo = false; };
  }, [beneId, data]);

  if (nascosta) return null;
  const titoloId = `${uid}-titolo`;

  return (
    <section aria-labelledby={titoloId} className="riepilogo">
      <div className="collegamenti__head">
        <h3 id={titoloId} className="scheda-card__title">Chi paga cosa</h3>
        <div className="riepilogo__data">
          <label htmlFor={`${uid}-data`}>Alla data</label>
          <input id={`${uid}-data`} type="date" value={data} onChange={(e) => setData(e.target.value)} />
        </div>
      </div>
      <p className="scheda-muted">Indica a chi spetta ciascuna voce, non calcola importi.</p>

      {riepilogo?.avvisi?.length > 0 && (
        <ul className="scheda-avvisi" role="status">
          {riepilogo.avvisi.map((a) => <li key={a}>{a}</li>)}
        </ul>
      )}
      {error && <div className="scheda-error" role="alert">{error}</div>}

      {loading && !riepilogo ? <LoadingSpinner message="Caricamento riepilogo…" /> : riepilogo && (
        <div className="scheda-table-wrap">
          <table className="scheda-table">
            <thead>
              <tr>
                <th scope="col">Voce</th>
                <th scope="col">A chi</th>
                <th scope="col">Quota</th>
                <th scope="col">Riferimento</th>
              </tr>
            </thead>
            <tbody>
              {riepilogo.voci.flatMap((v) => {
                const soggetti = v.soggetti.length ? v.soggetti : [null];
                return soggetti.map((s, i) => (
                  <tr key={`${v.codice}-${s?.soggetto_id ?? 'nessuno'}-${i}`}>
                    <td data-label="Voce">{i === 0 ? v.etichetta : ''}</td>
                    <td data-label="A chi">{s ? s.nome : '—'}</td>
                    <td data-label="Quota">{s ? quota(s.quota) : '—'}</td>
                    <td data-label="Riferimento" className="scheda-muted">{i === 0 ? v.norma : ''}</td>
                  </tr>
                ));
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
