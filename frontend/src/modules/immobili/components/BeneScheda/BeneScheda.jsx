import { useCallback, useEffect, useState } from 'react';
import { Link, Navigate, useParams } from 'react-router-dom';
import { ArrowLeft, Pencil } from 'lucide-react';
import { beniAPI, terreniAPI, unitaImmobiliariAPI } from '../../services/immobiliAPI';
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
import TerrenoForm from '../Terreni/TerrenoForm';
import VariazioniCatastali from './VariazioniCatastali';
import DatiUnita from './DatiUnita';
import DatiTerreno from './DatiTerreno';
import './BeneScheda.css';

function Sezione({ id, title, children }) {
  // Untitled cards wrap components that render their own labelled heading.
  if (!title) return <div className="scheda-card">{children}</div>;
  return (
    <section className="scheda-card" aria-labelledby={id}>
      <h3 id={id} className="scheda-card__title">{title}</h3>
      {children}
    </section>
  );
}

// What changes with the type of bene; every other section is the same.
const TIPI = {
  UNITA: {
    carica: (id) => unitaImmobiliariAPI.getById(id),
    lista: { to: '/unita-immobiliari', label: 'Unità immobiliari' },
    titolo: (b) => `${b.codice} · ${b.tipo}`,
    luogo: (b) => [b.cap, b.citta, b.provincia ? `(${b.provincia})` : null].filter(Boolean).join(' '),
    Dati: ({ bene }) => <DatiUnita unita={bene} />,
    Form: ({ bene, onClose }) => <UnitaImmobiliareForm unitaImmobiliare={bene} showSchedaLink={false} onClose={onClose} />,
  },
  TERRENO: {
    carica: (id) => terreniAPI.getById(id),
    lista: { to: '/terreni', label: 'Terreni' },
    titolo: (b) => `${b.codice} · ${b.nome || 'Terreno'}`,
    luogo: (b) => [b.cap, b.comune, b.provincia ? `(${b.provincia})` : null].filter(Boolean).join(' '),
    Dati: ({ bene }) => <DatiTerreno terreno={bene} />,
    Form: ({ bene, onClose }) => <TerrenoForm terreno={bene} onClose={onClose} />,
  },
};

/** Old links /unita-immobiliari/:id and /terreni/:id lead to the bene's page. */
export function RedirectABene() {
  const { id } = useParams();
  return <Navigate to={`/beni/${id}`} replace />;
}

/**
 * Detail page of a bene (/beni/:id), unit or land parcel: data of its type,
 * documents with history, catastal changes, rights, tenants, recurring
 * expenses and deadlines. Other modules can add sections through the
 * "immobile.detail.sections" extension point.
 */
export default function BeneScheda() {
  const { id } = useParams();
  const [bene, setBene] = useState(null);
  const [tipo, setTipo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modifica, setModifica] = useState(false);
  const [versione, setVersione] = useState(0);

  const carica = useCallback(async () => {
    setLoading(true);
    try {
      const base = await beniAPI.getById(id);
      const tipoBene = TIPI[base.data.tipo_bene] ? base.data.tipo_bene : 'UNITA';
      const res = await TIPI[tipoBene].carica(id);
      setTipo(tipoBene);
      setBene(res.data);
      setError(null);
    } catch (err) {
      setError(err?.response?.status === 404 ? 'Bene non trovato' : formatApiError(err));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { carica(); }, [carica]);

  if (loading && !bene) return <LoadingSpinner message="Caricamento bene…" />;
  if (error) {
    const lista = TIPI[tipo || 'UNITA'].lista;
    return (
      <div className="immobile-scheda">
        <Link to={lista.to} className="scheda-back"><ArrowLeft size={16} aria-hidden="true" /> {lista.label}</Link>
        <div className="scheda-error" role="alert">{error}</div>
      </div>
    );
  }

  const config = TIPI[tipo];
  const { Dati, Form } = config;
  const beneId = Number(id);
  const luogo = config.luogo(bene);
  const indirizzo = [bene.indirizzo, luogo].filter(Boolean).join(', ');

  return (
    <div className="immobile-scheda">
      <Link to={config.lista.to} className="scheda-back"><ArrowLeft size={16} aria-hidden="true" /> {config.lista.label}</Link>

      <header className="scheda-header">
        <div>
          <h2>{config.titolo(bene)}</h2>
          <p className="scheda-muted">{indirizzo}</p>
        </div>
        <Button variant="secondary" onClick={() => setModifica(true)}>
          <Pencil size={16} aria-hidden="true" /> Modifica
        </Button>
      </header>

      <Sezione id="scheda-dati" title="Dati">
        <Dati bene={bene} />
      </Sezione>

      <Sezione id="scheda-documenti">
        <DocumentiPanel key={versione} entityType="IMMOBILE" entityId={beneId} title="Documenti" />
      </Sezione>

      <Sezione id="scheda-variazioni" title="Variazioni catastali">
        <VariazioniCatastali key={versione} beneId={beneId} />
      </Sezione>

      <Sezione id="scheda-diritti">
        <DirittiImmobileSection immobileId={beneId} />
      </Sezione>
      <Sezione id="scheda-conduttori">
        <AssegnazioneConduttoreSection unitaImmobiliareId={beneId} />
      </Sezione>
      <Sezione id="scheda-spese">
        <SpeseRicorrentiSection unitaImmobiliareId={beneId} />
      </Sezione>
      <Sezione id="scheda-scadenze">
        <ScadenzeSection modulo="immobili" entityType="IMMOBILE" entityId={beneId} />
      </Sezione>

      <ExtensionPoint name="immobile.detail.sections" immobileId={beneId} />

      {modifica && (
        <Form
          bene={bene}
          onClose={() => { setModifica(false); carica(); setVersione((v) => v + 1); }}
        />
      )}
    </div>
  );
}
