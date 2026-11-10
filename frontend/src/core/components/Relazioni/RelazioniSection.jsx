import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { relazioniAPI } from '../../../services/relazioniAPI';
import './RelazioniSection.css';

const formatData = (iso) => {
  if (!iso) return '—';
  const [y, m, d] = iso.slice(0, 10).split('-');
  return `${d}/${m}/${y}`;
};

const LINK_OGGETTO = {
  IMMOBILE: (id) => `/unita-immobiliari/${id}`,
  CONDOMINIO: () => '/condomini',
  SOGGETTO_ANAGRAFICO: (id) => `/anagrafiche/${id}`,
};

function Oggetto({ r }) {
  if (!r.descrizione) return '—';
  const link = r.entity_id != null && LINK_OGGETTO[r.entity_type];
  return link ? <Link to={link(r.entity_id)}>{r.descrizione}</Link> : r.descrizione;
}

function periodo(r) {
  if (!r.data_inizio && !r.data_fine) return '—';
  if (!r.data_fine) return `dal ${formatData(r.data_inizio)}`;
  if (!r.data_inizio) return `fino al ${formatData(r.data_fine)}`;
  return `${formatData(r.data_inizio)} – ${formatData(r.data_fine)}`;
}

/**
 * Every role relation of an anagrafica (core and module-derived), grouped by
 * relation type: object, period, expiry, state.
 */
function RelazioniSection({ soggettoId }) {
  const [relazioni, setRelazioni] = useState(null);
  const [errore, setErrore] = useState(null);

  useEffect(() => {
    let attivo = true;
    relazioniAPI.list({ soggetto_id: soggettoId })
      .then((res) => attivo && setRelazioni(res.data || []))
      .catch(() => attivo && setErrore('Impossibile caricare le relazioni'));
    return () => { attivo = false; };
  }, [soggettoId]);

  const gruppi = useMemo(() => {
    const out = new Map();
    (relazioni || []).forEach((r) => {
      if (!out.has(r.tipo)) out.set(r.tipo, { nome: r.tipo_nome, righe: [] });
      out.get(r.tipo).righe.push(r);
    });
    return [...out.values()];
  }, [relazioni]);

  if (errore) return <p className="relazioni-errore" role="alert">{errore}</p>;
  if (relazioni === null) return <p className="relazioni-vuoto">Caricamento relazioni…</p>;
  if (!gruppi.length) {
    return (
      <p className="relazioni-vuoto">
        Nessuna relazione: questa anagrafica non è ancora proprietaria, conduttrice o collegata ad altri oggetti.
      </p>
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
                  <td><Oggetto r={r} /></td>
                  <td>{periodo(r)}</td>
                  <td>{r.data_scadenza ? formatData(r.data_scadenza) : '—'}</td>
                  <td>
                    <span className={`relazioni-stato relazioni-stato--${r.corrente ? 'corrente' : 'cessata'}`}>
                      {r.corrente ? 'In corso' : 'Cessata'}
                    </span>
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
