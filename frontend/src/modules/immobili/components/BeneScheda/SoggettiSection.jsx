import { useCallback, useEffect, useId, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { Button } from '../../../../components/UI';
import { ConfirmDialog } from '../../../../core/components/common/ConfirmDialog';
import { EmptyState } from '../../../../core/components/common/EmptyState';
import { LoadingSpinner } from '../../../../core/components/common/LoadingSpinner';
import DocumentiPanel from '../../../../core/components/Documenti/DocumentiPanel';
import { formatDate, todayIso } from '../../../../core/components/Documenti/documentiUtils';
import { ErrorMessage } from '../../../../core/components/common/ErrorMessage';
import { useToast } from '../../../../core/hooks/useToast';
import { relazioniAPI } from '../../../../services/relazioniAPI';
import { beniAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import RelazioneBeneForm from './RelazioneBeneForm';


const BLOCCHI = [
  { famiglia: 'diritti_reali', titolo: 'Diritti reali', vuoto: 'Nessun diritto reale registrato', conQuota: true },
  { famiglia: 'godimento', titolo: 'Godimento', vuoto: 'Nessun godimento registrato', conQuota: false },
  { famiglia: 'incarichi', titolo: 'Incarichi', vuoto: 'Nessun incarico', conQuota: false },
];

function periodo(r) {
  if (r.data_inizio && r.data_fine) return `dal ${formatDate(r.data_inizio)} al ${formatDate(r.data_fine)}`;
  if (r.data_inizio) return `dal ${formatDate(r.data_inizio)}`;
  if (r.data_fine) return `fino al ${formatDate(r.data_fine)}`;
  return '—';
}

/**
 * "Soggetti" of a bene: rights in rem, enjoyment (tenancies, loans) and
 * assignments, all core relations of the bene grouped by family.
 */
export default function SoggettiSection({ beneId, onChange }) {
  const uid = useId();
  const toast = useToast();
  const [dati, setDati] = useState({ diritti_reali: [], godimento: [], incarichi: [] });
  const [chiuse, setChiuse] = useState(false);
  const [loading, setLoading] = useState(true);
  const [caricato, setCaricato] = useState(false);
  const [error, setError] = useState(null);
  const [form, setForm] = useState(null); // { blocco, relazione? }
  const [chiusura, setChiusura] = useState(null); // { id, data }
  const [daEliminare, setDaEliminare] = useState(null);
  const [conDocumenti, setConDocumenti] = useState(null);

  const carica = useCallback(async () => {
    setLoading(true);
    try {
      const r = await beniAPI.getRelazioni(beneId, { soloCorrenti: !chiuse });
      setDati({ diritti_reali: [], godimento: [], incarichi: [], ...(r.data || {}) });
      setCaricato(true);
      setError(null);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }, [beneId, chiuse]);

  useEffect(() => { carica(); }, [carica]);

  const esegui = async (azione) => {
    try {
      await azione();
      await carica();
      onChange?.();
    } catch (err) {
      toast.error(formatApiError(err));
    }
  };

  const chiudi = (e) => {
    e.preventDefault();
    const { id, data } = chiusura;
    setChiusura(null);
    esegui(() => relazioniAPI.update(id, { data_fine: data }));
  };

  const elimina = () => {
    const id = daEliminare.id;
    setDaEliminare(null);
    esegui(() => relazioniAPI.remove(id));
  };

  const titoloId = `${uid}-titolo`;

  return (
    <section aria-labelledby={titoloId} className="soggetti-bene">
      <div className="collegamenti__head">
        <h3 id={titoloId} className="scheda-card__title">Soggetti</h3>
        <label className="collegamenti__storico soggetti-bene__chiuse">
          <input type="checkbox" checked={chiuse} onChange={(e) => setChiuse(e.target.checked)} />
          Mostra chiuse
        </label>
      </div>

      {error && !caricato && <ErrorMessage message={error} onRetry={carica} />}
      {error && caricato && <div className="scheda-error" role="alert">{error}</div>}
      {loading && !caricato && !error && <LoadingSpinner message="Caricamento soggetti…" />}

      {caricato && BLOCCHI.map((b) => {
        const righe = dati[b.famiglia] || [];
        const bloccoId = `${uid}-${b.famiglia}`;
        const colonne = b.conQuota ? 5 : 4;
        return (
          <section key={b.famiglia} aria-labelledby={bloccoId} className="soggetti-bene__blocco">
            <div className="collegamenti__head">
              <h4 id={bloccoId} className="collegamenti__etichetta">{b.titolo}</h4>
              <Button variant="secondary" size="sm" onClick={() => setForm({ blocco: b })}>
                <Plus size={16} aria-hidden="true" /> Aggiungi
              </Button>
            </div>
            {righe.length === 0 ? (
              <EmptyState variant="compact" title={b.vuoto} />
            ) : (
              <div className="scheda-table-wrap">
                <table className="scheda-table">
                  <thead>
                    <tr>
                      <th scope="col">Anagrafica</th>
                      <th scope="col">Tipo</th>
                      {b.conQuota && <th scope="col">Quota</th>}
                      <th scope="col">Periodo</th>
                      <th scope="col">Azioni</th>
                    </tr>
                  </thead>
                  <tbody>
                    {righe.flatMap((r) => {
                      const chiusa = Boolean(r.data_fine) && r.data_fine < todayIso();
                      return [
                        <tr key={r.id} className={chiusa ? 'is-chiuso' : undefined}>
                          <td data-label="Anagrafica">
                            <Link to={`/anagrafiche/${r.soggetto_id}`}>{r.soggetto_nome}</Link>
                            {chiusa && <span className="scheda-muted"> (chiusa)</span>}
                          </td>
                          <td data-label="Tipo">{r.tipo_nome}</td>
                          {b.conQuota && <td data-label="Quota">{r.quota || '—'}</td>}
                          <td data-label="Periodo">{periodo(r)}</td>
                          <td data-label="Azioni">
                            {chiusura?.id === r.id ? (
                              <form className="collegamenti__chiusura" onSubmit={chiudi}>
                                <label htmlFor={`${uid}-fine-${r.id}`}>Fino al</label>
                                <input id={`${uid}-fine-${r.id}`} type="date" required value={chiusura.data}
                                  onChange={(e) => setChiusura({ id: r.id, data: e.target.value })} />
                                <Button type="submit" size="sm">Conferma</Button>
                                <Button type="button" variant="ghost" size="sm" onClick={() => setChiusura(null)}>Annulla</Button>
                              </form>
                            ) : (
                              <div className="collegamenti__azioni">
                                <Button variant="ghost" size="sm" onClick={() => setForm({ blocco: b, relazione: r })}
                                  aria-label={`Modifica la relazione di ${r.soggetto_nome}`}>Modifica</Button>
                                {!r.data_fine && (
                                  <Button variant="ghost" size="sm" onClick={() => setChiusura({ id: r.id, data: todayIso() })}
                                    aria-label={`Chiudi la relazione di ${r.soggetto_nome}`}>Chiudi</Button>
                                )}
                                <Button variant="ghost" size="sm"
                                  onClick={() => setConDocumenti(conDocumenti === r.id ? null : r.id)}
                                  aria-expanded={conDocumenti === r.id}
                                  aria-label={`Documenti della relazione di ${r.soggetto_nome}`}>Documenti</Button>
                                <Button variant="ghost" size="sm" onClick={() => setDaEliminare(r)}
                                  aria-label={`Elimina la relazione di ${r.soggetto_nome}`}>Elimina</Button>
                              </div>
                            )}
                          </td>
                        </tr>,
                        conDocumenti === r.id && (
                          <tr key={`${r.id}-doc`}>
                            <td colSpan={colonne}>
                              <DocumentiPanel entityType="RELAZIONE" entityId={r.id} title="Documenti" />
                            </td>
                          </tr>
                        ),
                      ];
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        );
      })}

      {form && (
        <RelazioneBeneForm
          beneId={beneId}
          famiglia={form.blocco.famiglia}
          titolo={form.blocco.titolo}
          relazione={form.relazione}
          onClose={(salvato) => {
            setForm(null);
            if (salvato) { carica(); onChange?.(); }
          }}
        />
      )}
      <ConfirmDialog
        isOpen={!!daEliminare}
        title="Eliminare la relazione?"
        message={daEliminare ? `La relazione di ${daEliminare.soggetto_nome} sparisce del tutto. Per un rapporto terminato usa Chiudi: resta nello storico.` : ''}
        confirmLabel="Elimina"
        cancelLabel="Annulla"
        variant="danger"
        onConfirm={elimina}
        onCancel={() => setDaEliminare(null)}
      />
    </section>
  );
}
