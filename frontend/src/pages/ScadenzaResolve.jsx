import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { renderIcon } from '../components/Navigation/iconRegistry.jsx';
import './ScadenzaResolve.css';

const buildTarget = ({ modulo, entityType, entityId, scadenzaId }) => {
  if (!modulo || !entityType || !entityId) return null;
  const normalizedModule = String(modulo);
  const normalizedType = String(entityType).toUpperCase();

  if (normalizedModule === 'anagrafica_italiana' && normalizedType === 'SOGGETTO_ANAGRAFICO') {
    const params = new URLSearchParams({
      entity_id: String(entityId),
      entity_type: normalizedType,
      scadenza_id: scadenzaId ? String(scadenzaId) : '',
    });
    return `/anagrafiche/scadenze/resolve?${params.toString()}`;
  }

  return null;
};

const ScadenzaResolve = () => {
  const navigate = useNavigate();
  const [params] = useSearchParams();

  const payload = useMemo(() => ({
    modulo: params.get('modulo'),
    entityType: params.get('entity_type'),
    entityId: params.get('entity_id'),
    scadenzaId: params.get('scadenza_id'),
  }), [params]);

  const [resolvedPayload, setResolvedPayload] = useState(payload);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const target = useMemo(() => buildTarget(resolvedPayload), [resolvedPayload]);

  useEffect(() => {
    if (target) {
      navigate(target, { replace: true });
    }
  }, [target, navigate]);

  useEffect(() => {
    const entityType = String(payload.entityType || '').toUpperCase();
    if (entityType !== 'DOCUMENT_JOB') {
      setResolvedPayload(payload);
      return;
    }
    if (!payload.entityId) {
      setResolvedPayload(payload);
      return;
    }

    const loadJob = async () => {
      try {
        setLoading(true);
        setError('');
        const token = localStorage.getItem('access_token');
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
        const response = await fetch(`${baseUrl}/document-parsing/job/${payload.entityId}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (!response.ok) {
          throw new Error(`Errore recupero job (${response.status})`);
        }
        const job = await response.json();
        const nextModulo = payload.modulo || (job.document_type_key?.split('.')?.[0] ?? '');
        setResolvedPayload({
          modulo: nextModulo,
          entityType: job.entity_type,
          entityId: job.entity_id,
          scadenzaId: payload.scadenzaId,
        });
      } catch (err) {
        setError(err.message || 'Errore nel recupero del job');
      } finally {
        setLoading(false);
      }
    };

    loadJob();
  }, [payload]);

  if (target) {
    return null;
  }

  return (
    <div className="scadenza-resolve">
      <div className="scadenza-resolve__card">
        <div className="scadenza-resolve__title">
          {renderIcon('alert-triangle', { size: 20, className: 'resolve-icon' })}
          Nessuna pagina di completamento configurata
        </div>
        <p className="scadenza-resolve__subtitle">
          Il modulo richiesto non ha ancora definito la pagina di gestione dell&apos;evento.
        </p>
        {loading && (
          <div className="scadenza-resolve__loading">
            {renderIcon('calendar', { size: 16, className: 'resolve-icon' })}
            Verifica job in corso...
          </div>
        )}
        {error && <div className="scadenza-resolve__error">{error}</div>}
        <div className="scadenza-resolve__meta">
          <div><strong>Modulo:</strong> {resolvedPayload.modulo || '-'}</div>
          <div><strong>Entity Type:</strong> {resolvedPayload.entityType || '-'}</div>
          <div><strong>Entity ID:</strong> {resolvedPayload.entityId || '-'}</div>
          <div><strong>Scadenza ID:</strong> {resolvedPayload.scadenzaId || '-'}</div>
        </div>
        <Link to="/test/scadenze" className="btn btn-secondary scadenza-resolve__link">
          {renderIcon('list', { size: 16, className: 'resolve-icon' })}
          Torna alle scadenze
        </Link>
      </div>
    </div>
  );
};

export default ScadenzaResolve;
