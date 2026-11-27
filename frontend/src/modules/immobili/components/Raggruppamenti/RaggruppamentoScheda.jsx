import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Pencil, Plus } from 'lucide-react';
import { Button } from '../../../../components/UI';
import { ConfirmDialog } from '../../../../core/components/common/ConfirmDialog';
import { EmptyState } from '../../../../core/components/common/EmptyState';
import { LoadingSpinner } from '../../../../core/components/common/LoadingSpinner';
import { raggruppamentiAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import { useToast } from '../../../../core/hooks/useToast';
import SoggettiSection from '../BeneScheda/SoggettiSection';
import PercorsoRamo from './PercorsoRamo';
import RaggruppamentoForm from './RaggruppamentoForm';
import SceltaRamo from './SceltaRamo';
import { etichettaTipo } from './rami';
import '../BeneScheda/BeneScheda.css';
import './Raggruppamenti.css';

const FAMIGLIE_RAMO = ['godimento', 'incarichi']; // rights in rem stay on the beni

function cosaSale(ramo) {
  const rami = ramo.figli.length === 1 ? '1 sottoraggruppamento' : `${ramo.figli.length} sottoraggruppamenti`;
  const beni = ramo.beni.length === 1 ? '1 bene' : `${ramo.beni.length} beni`;
  const dove = ramo.percorso.length > 1
    ? `salgono in ${ramo.percorso[ramo.percorso.length - 2].nome}`
    : 'restano al livello più alto';
  return `${rami} e ${beni} ${dove}. Se il raggruppamento ha relazioni o documenti non si può eliminare: archivialo.`;
}

/** /raggruppamenti/:id: path, sub-rami, beni and the ramo's own relations (inherited by its beni). */
export default function RaggruppamentoScheda() {
  const { id } = useParams();
  const ramoId = Number(id);
  const navigate = useNavigate();
  const [ramo, setRamo] = useState(null);
  const [error, setError] = useState(null);
  const [azioneErr, setAzioneErr] = useState(null);
  const [modifica, setModifica] = useState(false);
  const [nuovoFiglio, setNuovoFiglio] = useState(false);
  const [sposta, setSposta] = useState(false);
  const [elimina, setElimina] = useState(false);
  const [occupato, setOccupato] = useState(false);
  const occupatoRef = useRef(false); // blocks a double click before the re-render
  const spostaRef = useRef(null);
  const toast = useToast();

  const carica = useCallback(async () => {
    try {
      const r = await raggruppamentiAPI.getById(ramoId);
      setRamo(r.data);
      setError(null);
    } catch (err) {
      setError(err?.response?.status === 404 ? 'Raggruppamento non trovato' : formatApiError(err));
    }
  }, [ramoId]);

  useEffect(() => { carica(); }, [carica]);

  const caricaRelazioni = useCallback((opzioni) => raggruppamentiAPI.getRelazioni(ramoId, opzioni), [ramoId]);
  const creaRelazione = useCallback((dati) => raggruppamentiAPI.createRelazione(ramoId, dati), [ramoId]);

  const esegui = async (azione, messaggio) => {
    if (occupatoRef.current) return;
    occupatoRef.current = true;
    setOccupato(true);
    setAzioneErr(null);
    try {
      await azione();
      if (messaggio) toast.success(messaggio);
    } catch (err) {
      setAzioneErr(formatApiError(err));
    } finally {
      occupatoRef.current = false;
      setOccupato(false);
    }
  };

  if (error) {
    return (
      <div className="immobile-scheda raggruppamenti">
        <Link to="/raggruppamenti" className="scheda-back"><ArrowLeft size={16} aria-hidden="true" /> Raggruppamenti</Link>
        <div className="scheda-error" role="alert">{error}</div>
      </div>
    );
  }
  if (!ramo) return <LoadingSpinner message="Caricamento raggruppamento…" />;

  return (
    <div className="immobile-scheda raggruppamenti">
      <Link to="/raggruppamenti" className="scheda-back"><ArrowLeft size={16} aria-hidden="true" /> Raggruppamenti</Link>

      <header className="scheda-header">
        <div>
          <h2>{ramo.nome}</h2>
          <p className="scheda-muted">
            {etichettaTipo(ramo.tipo)}{!ramo.attivo && ' · archiviato'}
          </p>
          <PercorsoRamo percorso={ramo.percorso} ultimoLink={false} />
        </div>
        <div className="raggruppamento__azioni">
          <Button onClick={() => setModifica(true)} disabled={occupato}><Pencil size={16} aria-hidden="true" /> Modifica</Button>
          <Button ref={spostaRef} variant="secondary" aria-expanded={sposta} disabled={occupato}
            onClick={() => setSposta((v) => !v)}>Sposta</Button>
          {ramo.attivo ? (
            <Button variant="secondary" disabled={occupato} onClick={() => esegui(async () => {
              const r = await raggruppamentiAPI.update(ramoId, { attivo: false });
              setRamo(r.data);
            }, 'Raggruppamento archiviato')}>Archivia</Button>
          ) : (
            <Button variant="secondary" disabled={occupato} onClick={() => esegui(async () => {
              const r = await raggruppamentiAPI.update(ramoId, { attivo: true });
              setRamo(r.data);
            }, 'Raggruppamento riattivato')}>Riattiva</Button>
          )}
          <Button variant="danger" disabled={occupato} onClick={() => setElimina(true)}>Elimina</Button>
        </div>
      </header>

      {azioneErr && <div className="scheda-error" role="alert">{azioneErr}</div>}
      {sposta && (
        <SceltaRamo
          label="Raggruppamento superiore"
          vuoto="Nessuno (livello più alto)"
          attuale={ramo.padre_id}
          escludiId={ramoId}
          onAnnulla={() => { setSposta(false); spostaRef.current?.focus(); }}
          onConferma={async (padreId) => {
            const r = await raggruppamentiAPI.sposta(ramoId, padreId);
            setRamo(r.data);
            setSposta(false);
            spostaRef.current?.focus();
            toast.success('Raggruppamento spostato: le relazioni ereditate dai suoi beni sono cambiate');
          }}
        />
      )}
      {ramo.descrizione && <p>{ramo.descrizione}</p>}

      <section className="scheda-card" aria-labelledby="ramo-contenuto">
        <div className="collegamenti__head">
          <h3 id="ramo-contenuto" className="scheda-card__title">Contenuto</h3>
          {ramo.attivo && (
            <Button variant="secondary" size="sm" onClick={() => setNuovoFiglio(true)}>
              <Plus size={16} aria-hidden="true" /> Sottoraggruppamento
            </Button>
          )}
        </div>
        {ramo.figli.length === 0 && ramo.beni.length === 0 ? (
          <EmptyState variant="compact" title="Vuoto"
            description="Aggiungi un sottoraggruppamento, o sposta qui un bene dalla sua scheda." />
        ) : (
          <ul className="raggruppamento__contenuto">
            {ramo.figli.map((f) => (
              <li key={`r-${f.id}`}>
                <Link to={`/raggruppamenti/${f.id}`}>{f.nome}</Link>
                <span className="albero-rami__tipo">{etichettaTipo(f.tipo)}</span>
                {!f.attivo && <span className="scheda-muted">(archiviato)</span>}
              </li>
            ))}
            {ramo.beni.map((b) => (
              <li key={`b-${b.id}`}>
                <Link to={`/beni/${b.id}`}>{b.codice}{b.descrizione ? ` · ${b.descrizione}` : ''}</Link>
                <span className="scheda-muted">{b.tipo_bene === 'TERRENO' ? 'Terreno' : 'Unità'}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <div className="scheda-card">
        <SoggettiSection
          key={ramoId}
          caricaRelazioni={caricaRelazioni}
          creaRelazione={creaRelazione}
          entityType="RAGGRUPPAMENTO"
          famiglie={FAMIGLIE_RAMO}
        />
        <p className="scheda-muted">Godimenti e incarichi del raggruppamento valgono per tutti i beni che contiene.</p>
      </div>

      {modifica && (
        <RaggruppamentoForm ramo={ramo} onClose={(salvato) => {
          setModifica(false);
          if (salvato) { toast.success('Raggruppamento salvato'); carica(); }
        }} />
      )}
      {nuovoFiglio && (
        <RaggruppamentoForm padreId={ramoId} onClose={(salvato) => {
          setNuovoFiglio(false);
          if (salvato) { toast.success('Sottoraggruppamento creato'); carica(); }
        }} />
      )}
      <ConfirmDialog
        isOpen={elimina}
        title="Eliminare il raggruppamento?"
        message={cosaSale(ramo)}
        confirmLabel="Elimina definitivamente"
        cancelLabel="Annulla"
        variant="danger"
        onConfirm={() => {
          setElimina(false);
          esegui(async () => {
            await raggruppamentiAPI.delete(ramoId);
            navigate('/raggruppamenti');
          }, 'Raggruppamento eliminato');
        }}
        onCancel={() => setElimina(false)}
      />
    </div>
  );
}
