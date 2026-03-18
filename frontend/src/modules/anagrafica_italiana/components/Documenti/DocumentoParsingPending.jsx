import { useEffect, useMemo, useState } from 'react';
import { getParsingJobsForEntity, completeParsedDocumento } from '../../services/anagraficaAPI';
import './DocumentoParsingPending.css';

const mapParsedData = (result = {}) => ({
  apply_to_soggetto: true,
  nome: result.given_names || result.nome || '',
  cognome: result.surname || result.cognome || '',
  codice_fiscale: result.codice_fiscale || '',
  data_nascita: result.birth_date || '',
  luogo_nascita: result.birth_place || '',
  document_number: result.document_number || '',
  document_expiry: result.expiry_date || '',
  note: '',
});

const formatDateTime = (value) => {
  if (!value) return '-';
  return new Date(value).toLocaleString('it-IT');
};

export default function DocumentoParsingPending({ soggettoId, onCompleted }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [forms, setForms] = useState({});
  const [submitting, setSubmitting] = useState({});

  const loadJobs = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getParsingJobsForEntity('SOGGETTO_ANAGRAFICO', soggettoId, {
        pending_only: true,
      });
      setJobs(data || []);

      const nextForms = {};
      (data || []).forEach((job) => {
        nextForms[job.job_uuid] = mapParsedData(job.parsing_result || {});
      });
      setForms(nextForms);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!soggettoId) return;
    loadJobs();
  }, [soggettoId]);

  const handleChange = (jobUuid, field, value) => {
    setForms((prev) => ({
      ...prev,
      [jobUuid]: {
        ...prev[jobUuid],
        [field]: value,
      },
    }));
  };

  const handleSubmit = async (jobUuid) => {
    const payload = {
      job_uuid: jobUuid,
      ...(forms[jobUuid] || {}),
    };
    try {
      setSubmitting((prev) => ({ ...prev, [jobUuid]: true }));
      await completeParsedDocumento(payload);
      await loadJobs();
      window.dispatchEvent(new CustomEvent('scadenze:updated'));
      if (onCompleted) {
        onCompleted();
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setSubmitting((prev) => ({ ...prev, [jobUuid]: false }));
    }
  };

  const hasJobs = useMemo(() => jobs.length > 0, [jobs]);

  return (
    <div className="doc-parsing-pending">
      <div className="doc-parsing-header">
        <div>
          <h3>Parsing documenti da validare</h3>
          <p>Conferma i dati estratti prima di chiudere il processo.</p>
        </div>
        <button className="btn btn-secondary" onClick={loadJobs} disabled={loading}>
          Aggiorna
        </button>
      </div>

      {error && <div className="doc-parsing-error">{error}</div>}
      {loading && <div className="doc-parsing-loading">Caricamento...</div>}

      {!loading && !error && !hasJobs && (
        <div className="doc-parsing-empty">Nessun parsing in attesa.</div>
      )}

      {!loading && !error && hasJobs && (
        <div className="doc-parsing-list">
          {jobs.map((job) => {
            const form = forms[job.job_uuid] || {};
            return (
              <div key={job.job_uuid} className="doc-parsing-card">
                <div className="doc-parsing-meta">
                  <div>
                    <strong>{job.document_type_key}</strong>
                    <div className="doc-parsing-sub">
                      {job.parsing_service} • {formatDateTime(job.created_at)}
                    </div>
                  </div>
                  <div className={`doc-parsing-status status-${(job.status || '').toLowerCase()}`}>
                    {job.status || '-'}
                  </div>
                </div>

                <div className="doc-parsing-grid">
                  <label>
                    Nome
                    <input
                      value={form.nome || ''}
                      onChange={(e) => handleChange(job.job_uuid, 'nome', e.target.value)}
                    />
                  </label>
                  <label>
                    Cognome
                    <input
                      value={form.cognome || ''}
                      onChange={(e) => handleChange(job.job_uuid, 'cognome', e.target.value)}
                    />
                  </label>
                  <label>
                    Codice Fiscale
                    <input
                      value={form.codice_fiscale || ''}
                      onChange={(e) => handleChange(job.job_uuid, 'codice_fiscale', e.target.value)}
                    />
                  </label>
                  <label>
                    Data nascita
                    <input
                      type="date"
                      value={form.data_nascita || ''}
                      onChange={(e) => handleChange(job.job_uuid, 'data_nascita', e.target.value)}
                    />
                  </label>
                  <label>
                    Luogo nascita
                    <input
                      value={form.luogo_nascita || ''}
                      onChange={(e) => handleChange(job.job_uuid, 'luogo_nascita', e.target.value)}
                    />
                  </label>
                  <label>
                    Numero documento
                    <input
                      value={form.document_number || ''}
                      onChange={(e) => handleChange(job.job_uuid, 'document_number', e.target.value)}
                    />
                  </label>
                  <label>
                    Scadenza documento
                    <input
                      type="date"
                      value={form.document_expiry || ''}
                      onChange={(e) => handleChange(job.job_uuid, 'document_expiry', e.target.value)}
                    />
                  </label>
                  <label className="doc-parsing-note">
                    Note
                    <input
                      value={form.note || ''}
                      onChange={(e) => handleChange(job.job_uuid, 'note', e.target.value)}
                    />
                  </label>
                </div>

                <div className="doc-parsing-actions">
                  <label className="doc-parsing-checkbox">
                    <input
                      type="checkbox"
                      checked={form.apply_to_soggetto !== false}
                      onChange={(e) => handleChange(job.job_uuid, 'apply_to_soggetto', e.target.checked)}
                    />
                    Aggiorna dati anagrafici
                  </label>
                  <button
                    className="btn btn-primary"
                    onClick={() => handleSubmit(job.job_uuid)}
                    disabled={submitting[job.job_uuid]}
                  >
                    Conferma e chiudi
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
