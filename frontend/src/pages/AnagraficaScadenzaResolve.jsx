import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { renderIcon } from '../components/Navigation/iconRegistry.jsx';
import { getSoggettoById } from '../modules/anagrafica_italiana/services/anagraficaAPI.js';
import { DocumentoParsingPending, DocumentoList } from '../modules/anagrafica_italiana/components/Documenti';
import './AnagraficaScadenzaResolve.css';

const getAnagraficaDetailLink = (soggetto, fallbackId) => {
  const id = soggetto?.id ?? fallbackId;
  if (!id) return null;
  if (soggetto?.tipo_soggetto === 'PERSONA_GIURIDICA') {
    return `/anagrafiche/persone-giuridiche/${id}?tab=documenti`;
  }
  if (soggetto?.tipo_soggetto === 'PERSONA_FISICA') {
    return `/anagrafiche/persone-fisiche/${id}?tab=documenti`;
  }
  return `/anagrafiche/${id}?tab=documenti`;
};

const AnagraficaScadenzaResolve = () => {
  const [params] = useSearchParams();
  const entityId = params.get('entity_id');
  const entityType = params.get('entity_type');
  const scadenzaId = params.get('scadenza_id');

  const [soggetto, setSoggetto] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const parsedId = useMemo(() => (entityId ? parseInt(entityId, 10) : null), [entityId]);

  useEffect(() => {
    if (!parsedId || String(entityType).toUpperCase() !== 'SOGGETTO_ANAGRAFICO') {
      setLoading(false);
      return;
    }
    const load = async () => {
      try {
        setLoading(true);
        const data = await getSoggettoById(parsedId);
        setSoggetto(data);
      } catch (err) {
        setError(err.response?.data?.detail || err.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [parsedId, entityType]);

  if (!parsedId || String(entityType).toUpperCase() !== 'SOGGETTO_ANAGRAFICO') {
    return (
      <div className="anagrafica-resolve">
        <div className="anagrafica-resolve__card">
          <div className="anagrafica-resolve__title">
            {renderIcon('alert-triangle', { size: 20, className: 'resolve-icon' })}
            Parametri non validi
          </div>
          <p className="anagrafica-resolve__subtitle">
            Questa pagina gestisce solo l&apos;indicizzazione per soggetti anagrafici.
          </p>
          <Link to="/test/scadenze" className="btn btn-secondary resolve-link">
            {renderIcon('list', { size: 16, className: 'resolve-icon' })}
            Torna alle scadenze
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="anagrafica-resolve">
      <div className="anagrafica-resolve__header">
        <div>
          <h1 className="anagrafica-resolve__title">
            {renderIcon('id-card', { size: 22, className: 'resolve-icon' })}
            Completa indicizzazione documento
          </h1>
          <p className="anagrafica-resolve__subtitle">
            Scadenza #{scadenzaId || '-'}
          </p>
        </div>
        {parsedId && (
          <Link
            to={getAnagraficaDetailLink(soggetto, parsedId)}
            className="btn btn-secondary resolve-link"
          >
            {renderIcon('link', { size: 16, className: 'resolve-icon' })}
            Apri scheda completa
          </Link>
        )}
      </div>

      {loading && (
        <div className="anagrafica-resolve__loading">
          {renderIcon('calendar', { size: 16, className: 'resolve-icon' })}
          Caricamento...
        </div>
      )}
      {error && <div className="anagrafica-resolve__error">{error}</div>}

      {!loading && soggetto && (
        <div className="anagrafica-resolve__summary">
          <div className="summary-card">
            <div className="summary-label">Soggetto</div>
            <div className="summary-value">
              {soggetto.tipo_soggetto === 'PERSONA_GIURIDICA'
                ? soggetto.ragione_sociale
                : `${soggetto.nome || ''} ${soggetto.cognome || ''}`.trim()}
            </div>
          </div>
          <div className="summary-card">
            <div className="summary-label">Codice Fiscale / P.IVA</div>
            <div className="summary-value">{soggetto.codice_fiscale || '-'}</div>
          </div>
        </div>
      )}

      {parsedId && (
        <>
          <DocumentoParsingPending
            soggettoId={parsedId}
            onCompleted={() => {
              window.dispatchEvent(new CustomEvent('scadenze:updated'));
            }}
          />
          <div className="anagrafica-resolve__docs">
            <DocumentoList soggettoId={parsedId} />
          </div>
        </>
      )}
    </div>
  );
};

export default AnagraficaScadenzaResolve;
