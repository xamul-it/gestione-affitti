import { useCallback, useEffect, useId, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { Button } from '../../../../components/UI';
import { ConfirmDialog } from '../../../../core/components/common/ConfirmDialog';
import { LoadingSpinner } from '../../../../core/components/common/LoadingSpinner';
import { formatDate, todayIso } from '../../../../core/components/Documenti/documentiUtils';
import { beniAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import { opzioniCollegamento } from './opzioniCollegamento';
import CollegamentoForm from './CollegamentoForm';


function periodo(c) {
  if (c.data_inizio && c.data_fine) return `dal ${formatDate(c.data_inizio)} al ${formatDate(c.data_fine)}`;
  if (c.data_inizio) return `dal ${formatDate(c.data_inizio)}`;
  if (c.data_fine) return `fino al ${formatDate(c.data_fine)}`;
  return null;
}

/** "Beni collegati": pertinenze, building on a parcel, farm parcels, in both directions. */
export default function CollegamentiSection({ beneId, bene }) {
  const uid = useId();
  const [dati, setDati] = useState({ collegamenti: [], avvisi: [] });
  const [storico, setStorico] = useState(false);
  const [loading, setLoading] = useState(true);
  const [caricato, setCaricato] = useState(false);
  const [error, setError] = useState(null);
  const [nuovo, setNuovo] = useState(false);
  const [chiusura, setChiusura] = useState(null); // { id, data }
  const [daEliminare, setDaEliminare] = useState(null);

  const carica = useCallback(async () => {
    setLoading(true);
    try {
      const r = await beniAPI.getCollegamenti(beneId, storico);
      setDati(r.data || { collegamenti: [], avvisi: [] });
      setCaricato(true);
      setError(null);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }, [beneId, storico]);

  useEffect(() => { carica(); }, [carica]);

  const esegui = async (azione) => {
    try {
      await azione();
      await carica();
    } catch (err) {
      setError(formatApiError(err));
    }
  };

  const chiudi = (e) => {
    e.preventDefault();
    const { id, data } = chiusura;
    setChiusura(null);
    esegui(() => beniAPI.aggiornaCollegamento(beneId, id, { data_fine: data }));
  };

  const elimina = () => {
    const id = daEliminare.id;
    setDaEliminare(null);
    esegui(() => beniAPI.eliminaCollegamento(beneId, id));
  };

  const gruppi = dati.collegamenti.reduce((acc, c) => {
    (acc[c.etichetta] = acc[c.etichetta] || []).push(c);
    return acc;
  }, {});
  const titoloId = `${uid}-titolo`;

  return (
    <section aria-labelledby={titoloId} className="collegamenti">
      <div className="collegamenti__head">
        <h3 id={titoloId} className="scheda-card__title">Beni collegati</h3>
        {opzioniCollegamento(bene).length > 0 && (
          <Button variant="secondary" size="sm" onClick={() => setNuovo(true)}>
            <Plus size={16} aria-hidden="true" /> Collega
          </Button>
        )}
      </div>

      {dati.avvisi.length > 0 && (
        <ul className="scheda-avvisi" role="status">
          {dati.avvisi.map((a) => <li key={a}>{a}</li>)}
        </ul>
      )}
      {error && <div className="scheda-error" role="alert">{error}</div>}

      {loading && !caricato ? <LoadingSpinner message="Caricamento collegamenti…" /> : (
        Object.keys(gruppi).length === 0
          ? !error && caricato && <p className="scheda-empty">Nessun bene collegato</p>
          : Object.entries(gruppi).map(([etichetta, righe]) => (
            <div key={etichetta} className="collegamenti__gruppo">
              <h4 className="collegamenti__etichetta">{etichetta}</h4>
              <ul className="collegamenti__lista">
                {righe.map((c) => (
                  <li key={c.id} className={c.aperto ? undefined : 'is-chiuso'}>
                    <div className="collegamenti__bene">
                      <Link to={`/beni/${c.altro_bene.id}`}>
                        {c.altro_bene.codice}
                        {c.altro_bene.descrizione || c.altro_bene.indirizzo
                          ? ` · ${c.altro_bene.descrizione || c.altro_bene.indirizzo}` : ''}
                      </Link>
                      {periodo(c) && <span className="scheda-muted"> {periodo(c)}</span>}
                      {c.note && <span className="scheda-muted"> — {c.note}</span>}
                    </div>
                    {chiusura?.id === c.id ? (
                      <form className="collegamenti__chiusura" onSubmit={chiudi}>
                        <label htmlFor={`${uid}-fine-${c.id}`}>Fino al</label>
                        <input id={`${uid}-fine-${c.id}`} type="date" required value={chiusura.data}
                          onChange={(e) => setChiusura({ id: c.id, data: e.target.value })} />
                        <Button type="submit" size="sm">Conferma</Button>
                        <Button type="button" variant="ghost" size="sm" onClick={() => setChiusura(null)}>Annulla</Button>
                      </form>
                    ) : (
                      <div className="collegamenti__azioni">
                        {c.aperto && (
                          <Button variant="ghost" size="sm" onClick={() => setChiusura({ id: c.id, data: todayIso() })}
                            aria-label={`Chiudi il collegamento con ${c.altro_bene.codice}`}>Chiudi</Button>
                        )}
                        <Button variant="ghost" size="sm" onClick={() => setDaEliminare(c)}
                          aria-label={`Elimina il collegamento con ${c.altro_bene.codice}`}>Elimina</Button>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))
      )}

      <label className="collegamenti__storico">
        <input type="checkbox" checked={storico} onChange={(e) => setStorico(e.target.checked)} />
        Mostra storico
      </label>

      {nuovo && (
        <CollegamentoForm beneId={beneId} bene={bene}
          onClose={(salvato) => { setNuovo(false); if (salvato) carica(); }} />
      )}
      <ConfirmDialog
        isOpen={!!daEliminare}
        title="Eliminare il collegamento?"
        message={daEliminare ? `Il collegamento con ${daEliminare.altro_bene.codice} sparisce del tutto. Per un bene venduto o che non è più una pertinenza usa Chiudi: resta nello storico.` : ''}
        confirmLabel="Elimina"
        variant="danger"
        onConfirm={elimina}
        onCancel={() => setDaEliminare(null)}
      />
    </section>
  );
}
