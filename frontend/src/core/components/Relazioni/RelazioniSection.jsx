import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { relazioniAPI } from '../../../services/relazioniAPI';
import { formatDate } from '../../utils/formatters';
import { EmptyState, ErrorMessage, LoadingSpinner } from '../common';
import Badge from '../../../components/UI/Badge';
import './RelazioniSection.css';

const data = (iso) => (iso ? formatDate(iso) : '—');

/** Route of the page showing the object of a relation, per entity type. */
export const LINK_OGGETTO = {
  IMMOBILE: (id) => `/unita-immobiliari/${id}`,
  CONDOMINIO: () => '/condomini',
  SOGGETTO_ANAGRAFICO: (id) => `/anagrafiche/${id}`,
};

export function OggettoRelazione({ r }) {
  if (!r.descrizione) return '—';
  const link = r.entity_id != null && LINK_OGGETTO[r.entity_type];
  return link ? <Link to={link(r.entity_id)}>{r.descrizione}</Link> : r.descrizione;
}

function periodo(r) {
  if (!r.data_inizio && !r.data_fine) return '—';
  if (!r.data_fine) return `dal ${data(r.data_inizio)}`;
  if (!r.data_inizio) return `fino al ${data(r.data_fine)}`;
  return `${data(r.data_inizio)} – ${data(r.data_fine)}`;
}

/**
 * Every role relation of an anagrafica (core and module-derived), grouped by
 * relation type: object, period, expiry, state.
 */
function RelazioniSection({ soggettoId }) {
  const [relazioni, setRelazioni] = useState(null);
  const [errore, setErrore] = useState(null);

  const carica = useCallback(() => {
    setErrore(null);
    setRelazioni(null);
    return relazioniAPI.list({ soggetto_id: soggettoId })
      .then((res) => setRelazioni(res.data || []))
      .catch(() => setErrore('Impossibile caricare le relazioni'));
  }, [soggettoId]);

  useEffect(() => { carica(); }, [carica]);

  const gruppi = useMemo(() => {
    const out = new Map();
    (relazioni || []).forEach((r) => {
      if (!out.has(r.tipo)) out.set(r.tipo, { nome: r.tipo_nome, righe: [] });
      out.get(r.tipo).righe.push(r);
    });
    return [...out.values()];
  }, [relazioni]);

  if (errore) return <ErrorMessage message={errore} onRetry={carica} />;
  if (relazioni === null) return <LoadingSpinner message="Caricamento relazioni..." />;
  if (!gruppi.length) {
    return (
      <EmptyState
        title="Nessuna relazione"
        message="Nessuna relazione: questa anagrafica non è ancora proprietaria, conduttrice o collegata ad altri oggetti."
      />
    );
  }

  return (
    <div className="relazioni">
      {gruppi.map((g) => (
        <section key={g.nome} className="relazioni-gruppo">
          <h3>{g.nome}</h3>
          <table className="relazioni-tabella">
            <thead>
              <tr><th scope="col">Oggetto</th><th scope="col">Periodo</th><th scope="col">Scadenza</th><th scope="col">Stato</th></tr>
            </thead>
            <tbody>
              {g.righe.map((r, i) => (
                <tr key={`${r.relazione_id ?? r.record_id ?? 'm'}-${r.entity_id ?? 'x'}-${i}`}>
                  <td data-label="Oggetto"><OggettoRelazione r={r} /></td>
                  <td data-label="Periodo">{periodo(r)}</td>
                  <td data-label="Scadenza">{data(r.data_scadenza)}</td>
                  <td data-label="Stato">
                    <Badge variant={r.corrente ? 'success' : 'neutral'}>{r.corrente ? 'In corso' : 'Cessata'}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
    </div>
  );
}

export default RelazioniSection;
