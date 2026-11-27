import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { Button } from '../../../../components/UI';
import { EmptyState } from '../../../../core/components/common/EmptyState';
import { ErrorMessage } from '../../../../core/components/common/ErrorMessage';
import { LoadingSpinner } from '../../../../core/components/common/LoadingSpinner';
import { raggruppamentiAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import { useToast } from '../../../../core/hooks/useToast';
import RaggruppamentoForm from './RaggruppamentoForm';
import { etichettaTipo } from './rami';
import '../BeneScheda/BeneScheda.css';
import './Raggruppamenti.css';

function Nodo({ ramo }) {
  return (
    <li className={ramo.attivo ? undefined : 'is-archiviato'}>
      <div className="albero-rami__ramo">
        <Link to={`/raggruppamenti/${ramo.id}`}>{ramo.nome}</Link>
        <span className="albero-rami__tipo">{etichettaTipo(ramo.tipo)}</span>
        {!ramo.attivo && <span className="scheda-muted">(archiviato)</span>}
      </div>
      {(ramo.figli.length > 0 || ramo.beni.length > 0) && (
        <ul>
          {ramo.figli.map((f) => <Nodo key={f.id} ramo={f} />)}
          {ramo.beni.map((b) => (
            <li key={`b-${b.id}`} className="albero-rami__bene">
              <Link to={`/beni/${b.id}`}>{b.codice}{b.descrizione ? ` · ${b.descrizione}` : ''}</Link>
              <span className="scheda-muted">{b.tipo_bene === 'TERRENO' ? 'Terreno' : 'Unità immobiliare'}</span>
            </li>
          ))}
        </ul>
      )}
    </li>
  );
}

/** /raggruppamenti: tree of the rami (complexes, buildings, farms…) with the beni inside. */
export default function RaggruppamentiAlbero() {
  const [albero, setAlbero] = useState([]);
  const [archiviati, setArchiviati] = useState(false);
  const [loading, setLoading] = useState(true);
  const [caricato, setCaricato] = useState(false);
  const [error, setError] = useState(null);
  const [nuovo, setNuovo] = useState(false);
  const toast = useToast();

  const carica = useCallback(async () => {
    setLoading(true);
    try {
      const r = await raggruppamentiAPI.getAll({ vista: 'albero', includi_archiviati: archiviati });
      setAlbero(r.data || []);
      setCaricato(true);
      setError(null);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }, [archiviati]);

  useEffect(() => { carica(); }, [carica]);

  return (
    <div className="immobile-scheda raggruppamenti">
      <header className="scheda-header">
        <div>
          <h2>Raggruppamenti</h2>
          <p className="scheda-muted">Complessi, edifici e fondi con i beni che contengono.</p>
        </div>
        <Button onClick={() => setNuovo(true)}><Plus size={16} aria-hidden="true" /> Nuovo raggruppamento</Button>
      </header>
      <div className="scheda-card">
        <label className="collegamenti__storico">
          <input type="checkbox" checked={archiviati} onChange={(e) => setArchiviati(e.target.checked)} />
          Mostra archiviati
        </label>
        {error && !caricato && <ErrorMessage message={error} onRetry={carica} />}
        {error && caricato && <div className="scheda-error" role="alert">{error}</div>}
        {loading && !caricato && !error && <LoadingSpinner message="Caricamento raggruppamenti…" />}
        {caricato && albero.length === 0 && (
          <EmptyState title="Nessun raggruppamento"
            description="Crea un complesso, un edificio o un fondo e sposta dentro i beni dalla loro scheda." />
        )}
        {caricato && albero.length > 0 && (
          <ul className="albero-rami">
            {albero.map((r) => <Nodo key={r.id} ramo={r} />)}
          </ul>
        )}
      </div>
      {nuovo && (
        <RaggruppamentoForm onClose={(salvato) => {
          setNuovo(false);
          if (salvato) { toast.success('Raggruppamento creato'); carica(); }
        }} />
      )}
    </div>
  );
}
