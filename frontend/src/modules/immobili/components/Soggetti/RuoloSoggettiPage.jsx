import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { OggettoRelazione } from '../../../../core/components/Relazioni/RelazioniSection';
import '../../../../core/components/Relazioni/RelazioniSection.css';
import { nomeSoggetto } from '../../../anagrafica_italiana/components/SoggettiAnagrafici/SoggettiTable';
import { getSoggettiAnagrafici } from '../../../anagrafica_italiana/services/anagraficaAPI';
import { EmptyState, ErrorMessage, LoadingSpinner } from '../../../../core/components/common';
import { formatDate } from '../../../../core/utils/formatters';
import { relazioniAPI } from '../../../../services/relazioniAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import './RuoloSoggettiPage.css';

const data = (iso) => (iso ? formatDate(iso) : '—');

function periodo(r) {
  if (!r.data_inizio && !r.data_fine) return '—';
  if (!r.data_fine) return `dal ${data(r.data_inizio)}`;
  if (!r.data_inizio) return `fino al ${data(r.data_fine)}`;
  return `${data(r.data_inizio)} – ${data(r.data_fine)}`;
}

/**
 * The relations of one family (diritti_reali, godimento…) over the beni, one
 * row per relation, newest first. Relations are added from the page of the
 * bene; here they are read, with the anagrafica and the bene linked.
 */
function RuoloSoggettiPage({ famiglia, title, colonnaTipo, conQuota = false, vuoto }) {
  const [righe, setRighe] = useState(null);
  const [nomi, setNomi] = useState({});
  const [error, setError] = useState(null);
  const [cessate, setCessate] = useState(false);

  useEffect(() => {
    let attivo = true;
    setRighe(null);
    setError(null);
    Promise.all([
      relazioniAPI.list({ famiglia, entity_type: 'IMMOBILE', solo_correnti: !cessate }),
      getSoggettiAnagrafici({ limit: 1000 }).catch(() => []),
    ]).then(([rel, soggetti]) => {
      if (!attivo) return;
      setNomi(Object.fromEntries((soggetti || []).map((s) => [s.id, nomeSoggetto(s)])));
      setRighe(rel.data || []);
    }).catch((err) => { if (attivo) setError(formatApiError(err)); });
    return () => { attivo = false; };
  }, [famiglia, cessate]);

  const ordinate = useMemo(() => [...(righe || [])].sort((a, b) => (
    (nomi[a.soggetto_id] || '').localeCompare(nomi[b.soggetto_id] || '', 'it')
  )), [righe, nomi]);

  return (
    <div className="ruolo-page">
      <div className="ruolo-page__head">
        <h2>{title}</h2>
        <label className="ruolo-page__cessate">
          <input type="checkbox" checked={cessate} onChange={(e) => setCessate(e.target.checked)} />
          Mostra cessate
        </label>
      </div>
      {error && <ErrorMessage message={error} />}
      {!error && righe === null && <LoadingSpinner message="Caricamento…" />}
      {righe && righe.length === 0 && <EmptyState title={vuoto} message="Si aggiungono dalla scheda del bene." />}
      {righe && righe.length > 0 && (
        <table className="relazioni-tabella">
          <thead>
            <tr>
              <th scope="col">Anagrafica</th>
              <th scope="col">{colonnaTipo}</th>
              <th scope="col">Immobile</th>
              {conQuota && <th scope="col">Quota</th>}
              <th scope="col">Periodo</th>
            </tr>
          </thead>
          <tbody>
            {ordinate.map((r, i) => (
              <tr key={`${r.relazione_id ?? r.record_id ?? 'm'}-${i}`} className={r.corrente ? undefined : 'ruolo-oggetti--cessato'}>
                <td data-label="Anagrafica">
                  <Link to={`/anagrafiche/${r.soggetto_id}`}>{nomi[r.soggetto_id] || `Anagrafica ${r.soggetto_id}`}</Link>
                </td>
                <td data-label={colonnaTipo}>{r.tipo_nome}{r.corrente ? '' : ' (cessato)'}</td>
                <td data-label="Immobile"><OggettoRelazione r={r} /></td>
                {conQuota && <td data-label="Quota">{r.quota || '—'}</td>}
                <td data-label="Periodo">{periodo(r)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default RuoloSoggettiPage;
