import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Pencil } from 'lucide-react';
import { unitaImmobiliariAPI } from '../../services/immobiliAPI';
import { formatApiError } from '../../../../utils/errorHandling';
import { LoadingSpinner } from '../../../../core/components/common/LoadingSpinner';
import { ExtensionPoint } from '../../../../core/modules/ExtensionPoint';
import { Button } from '../../../../components/UI';
import DocumentiPanel from '../../../../core/components/Documenti/DocumentiPanel';
import ScadenzeSection from '../../../../components/Platform/Scadenze/ScadenzeSection';
import DirittiImmobileSection from '../DirittiImmobile/DirittiImmobileSection';
import AssegnazioneConduttoreSection from '../Conduttori/AssegnazioneConduttoreSection';
import SpeseRicorrentiSection from '../SpeseRicorrenti/SpeseRicorrentiSection';
import UnitaImmobiliareForm from '../UnitaImmobiliari/UnitaImmobiliareForm';
import VariazioniCatastali from './VariazioniCatastali';
import { euro, mq } from './formatters';
import './ImmobileScheda.css';

function Dato({ label, children }) {
  return (
    <div className="scheda-dato">
      <dt>{label}</dt>
      <dd>{children || '—'}</dd>
    </div>
  );
}

function Sezione({ id, title, children }) {
  return (
    <section className="scheda-card" aria-labelledby={id}>
      {title && <h3 id={id} className="scheda-card__title">{title}</h3>}
      {children}
    </section>
  );
}

/**
 * Detail page of a unit (/unita-immobiliari/:id): data, documents with
 * history, catastal changes, rights, tenants, recurring expenses and
 * deadlines. Other modules can add sections through the
 * "immobile.detail.sections" extension point.
 */
export default function ImmobileScheda() {
  const { id } = useParams();
  const [unita, setUnita] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modifica, setModifica] = useState(false);
  const [versione, setVersione] = useState(0);

  const carica = useCallback(async () => {
    setLoading(true);
    try {
      const res = await unitaImmobiliariAPI.getById(id);
      setUnita(res.data);
      setError(null);
    } catch (err) {
      setError(err?.response?.status === 404 ? 'Unità immobiliare non trovata' : formatApiError(err));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { carica(); }, [carica]);

  if (loading && !unita) return <LoadingSpinner message="Caricamento immobile…" />;
  if (error) {
    return (
      <div className="immobile-scheda">
        <Link to="/unita-immobiliari" className="scheda-back"><ArrowLeft size={16} aria-hidden="true" /> Unità immobiliari</Link>
        <div className="scheda-error" role="alert">{error}</div>
      </div>
    );
  }

  const unitaId = Number(id);
  const identificativi = [unita.foglio, unita.particella, unita.subalterno].filter(Boolean).join(' / ');
  const luogo = [unita.cap, unita.citta, unita.provincia ? `(${unita.provincia})` : null].filter(Boolean).join(' ');

  return (
    <div className="immobile-scheda">
      <Link to="/unita-immobiliari" className="scheda-back"><ArrowLeft size={16} aria-hidden="true" /> Unità immobiliari</Link>

      <header className="scheda-header">
        <div>
          <h2>{unita.codice} · {unita.tipo}</h2>
          <p className="scheda-muted">{unita.indirizzo}{luogo ? `, ${luogo}` : ''}</p>
        </div>
        <Button variant="secondary" onClick={() => setModifica(true)}>
          <Pencil size={16} aria-hidden="true" /> Modifica
        </Button>
      </header>

      <Sezione id="scheda-dati" title="Dati">
        <dl className="scheda-dati">
          <Dato label="Foglio / particella / sub">{identificativi}</Dato>
          <Dato label="Categoria">{unita.categoria_catastale?.codice}</Dato>
          <Dato label="Rendita catastale">{unita.rendita_catastale != null ? euro(unita.rendita_catastale) : null}</Dato>
          <Dato label="Superficie">{unita.superficie_mq != null ? mq(unita.superficie_mq) : null}</Dato>
          <Dato label="Locali">{unita.locali}</Dato>
          <Dato label="Piano">{unita.piano}</Dato>
        </dl>
      </Sezione>

      <Sezione id="scheda-documenti">
        <DocumentiPanel key={versione} entityType="IMMOBILE" entityId={unitaId} title="Documenti" />
      </Sezione>

      <Sezione id="scheda-variazioni" title="Variazioni catastali">
        <VariazioniCatastali key={versione} unitaId={unitaId} />
      </Sezione>

      <Sezione id="scheda-diritti">
        <DirittiImmobileSection immobileId={unitaId} />
      </Sezione>
      <Sezione id="scheda-conduttori">
        <AssegnazioneConduttoreSection unitaImmobiliareId={unitaId} />
      </Sezione>
      <Sezione id="scheda-spese">
        <SpeseRicorrentiSection unitaImmobiliareId={unitaId} />
      </Sezione>
      <Sezione id="scheda-scadenze">
        <ScadenzeSection modulo="immobili" entityType="IMMOBILE" entityId={unitaId} />
      </Sezione>

      <ExtensionPoint name="immobile.detail.sections" immobileId={unitaId} />

      {modifica && (
        <UnitaImmobiliareForm
          unitaImmobiliare={unita}
          showSchedaLink={false}
          onClose={() => { setModifica(false); carica(); setVersione((v) => v + 1); }}
        />
      )}
    </div>
  );
}
