import { useEffect, useState } from 'react';
import { FileSearch, RefreshCcw } from 'lucide-react';
import { documentParsingDebugAPI } from '../../services/api';
import './DocumentParsingDebug.css';

export default function DocumentParsingDebug() {
  const [logs, setLogs] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingJobs, setLoadingJobs] = useState(true);
  const [error, setError] = useState('');
  const [jobsError, setJobsError] = useState('');
  const [filters, setFilters] = useState({
    job_uuid: '',
    tenant_schema: '',
    parsing_service: '',
    direction: '',
  });
  const [jobFilters, setJobFilters] = useState({
    job_uuid: '',
    tenant_schema: '',
    parsing_service: '',
    status: '',
    created_by: '',
  });

  const loadLogs = async () => {
    try {
      setLoading(true);
      setError('');
      const params = {
        limit: 200,
      };
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params[key] = value;
      });
      const response = await documentParsingDebugAPI.getLogs(params);
      setLogs(response.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadJobs = async () => {
    try {
      setLoadingJobs(true);
      setJobsError('');
      const params = {
        limit: 200,
      };
      Object.entries(jobFilters).forEach(([key, value]) => {
        if (value) params[key] = value;
      });
      const response = await documentParsingDebugAPI.getJobs(params);
      setJobs(response.data || []);
    } catch (err) {
      setJobsError(err.response?.data?.detail || err.message);
    } finally {
      setLoadingJobs(false);
    }
  };

  useEffect(() => {
    loadLogs();
    loadJobs();
  }, []);

  return (
    <div className="parsing-debug">
      <div className="parsing-debug-header">
        <div className="header-title">
          <FileSearch size={24} strokeWidth={1.7} />
          <h1>Debug Parsing Documenti</h1>
        </div>
        <button className="btn btn-secondary" onClick={loadLogs} disabled={loading}>
          <RefreshCcw size={16} strokeWidth={1.7} />
          Aggiorna log
        </button>
        <button className="btn btn-secondary" onClick={loadJobs} disabled={loadingJobs}>
          <RefreshCcw size={16} strokeWidth={1.7} />
          Aggiorna richieste
        </button>
      </div>

      <div className="parsing-debug-section">
        <h2>Richieste parsing</h2>
        <div className="parsing-debug-filters">
          <input
            type="text"
            placeholder="Job UUID"
            value={jobFilters.job_uuid}
            onChange={(e) => setJobFilters((prev) => ({ ...prev, job_uuid: e.target.value }))}
          />
          <input
            type="text"
            placeholder="Tenant schema"
            value={jobFilters.tenant_schema}
            onChange={(e) => setJobFilters((prev) => ({ ...prev, tenant_schema: e.target.value }))}
          />
          <input
            type="text"
            placeholder="Parsing service"
            value={jobFilters.parsing_service}
            onChange={(e) => setJobFilters((prev) => ({ ...prev, parsing_service: e.target.value }))}
          />
          <input
            type="text"
            placeholder="Status (PENDING/QUEUED/COMPLETED/FAILED)"
            value={jobFilters.status}
            onChange={(e) => setJobFilters((prev) => ({ ...prev, status: e.target.value }))}
          />
          <input
            type="text"
            placeholder="Created by (user id)"
            value={jobFilters.created_by}
            onChange={(e) => setJobFilters((prev) => ({ ...prev, created_by: e.target.value }))}
          />
          <button className="btn btn-primary" onClick={loadJobs} disabled={loadingJobs}>
            Applica filtri
          </button>
        </div>

        {jobsError && <div className="parsing-debug-error">{jobsError}</div>}
        {loadingJobs && <div className="parsing-debug-loading">Caricamento...</div>}

        {!loadingJobs && !jobsError && jobs.length === 0 && (
          <div className="parsing-debug-empty">Nessuna richiesta trovata</div>
        )}

        {!loadingJobs && !jobsError && jobs.length > 0 && (
          <div className="parsing-debug-table-wrapper">
            <table className="parsing-debug-table">
              <thead>
                <tr>
                  <th>Quando</th>
                  <th>Status</th>
                  <th>Servizio</th>
                  <th>Tenant</th>
                  <th>Job UUID</th>
                  <th>Polling</th>
                  <th>Utente</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.id}>
                    <td>{job.created_at ? new Date(job.created_at).toLocaleString() : '-'}</td>
                    <td>{job.status || '-'}</td>
                    <td>{job.parsing_service || '-'}</td>
                    <td>{job.tenant_schema || '-'}</td>
                    <td className="mono">{job.job_uuid || '-'}</td>
                    <td className="mono">
                      {job.job_uuid ? `/api/v1/document-parsing/status/${job.job_uuid}` : '-'}
                    </td>
                    <td>{job.created_by || '-'}</td>
                    <td>
                      <details>
                        <summary>Mostra</summary>
                        {job.parsing_error && (
                          <pre className="error-text">{job.parsing_error}</pre>
                        )}
                        {job.parsing_result && (
                          <pre>{JSON.stringify(job.parsing_result, null, 2)}</pre>
                        )}
                      </details>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="parsing-debug-section">
        <h2>Log chiamate</h2>
      <div className="parsing-debug-filters">
        <input
          type="text"
          placeholder="Job UUID"
          value={filters.job_uuid}
          onChange={(e) => setFilters((prev) => ({ ...prev, job_uuid: e.target.value }))}
        />
        <input
          type="text"
          placeholder="Tenant schema"
          value={filters.tenant_schema}
          onChange={(e) => setFilters((prev) => ({ ...prev, tenant_schema: e.target.value }))}
        />
        <input
          type="text"
          placeholder="Parsing service"
          value={filters.parsing_service}
          onChange={(e) => setFilters((prev) => ({ ...prev, parsing_service: e.target.value }))}
        />
        <input
          type="text"
          placeholder="Direction (REQUEST/RESPONSE/CALLBACK/ERROR)"
          value={filters.direction}
          onChange={(e) => setFilters((prev) => ({ ...prev, direction: e.target.value }))}
        />
        <button className="btn btn-primary" onClick={loadLogs} disabled={loading}>
          Applica filtri
        </button>
      </div>

      {error && <div className="parsing-debug-error">{error}</div>}
      {loading && <div className="parsing-debug-loading">Caricamento...</div>}

      {!loading && !error && logs.length === 0 && (
        <div className="parsing-debug-empty">Nessun log trovato</div>
      )}

      {!loading && !error && logs.length > 0 && (
        <div className="parsing-debug-table-wrapper">
          <table className="parsing-debug-table">
            <thead>
              <tr>
                <th>Quando</th>
                <th>Direzione</th>
                <th>Servizio</th>
                <th>Tenant</th>
                <th>Job UUID</th>
                <th>Status</th>
                <th>URL</th>
                <th>Payload</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{log.created_at ? new Date(log.created_at).toLocaleString() : '-'}</td>
                  <td>{log.direction}</td>
                  <td>{log.parsing_service || '-'}</td>
                  <td>{log.tenant_schema || '-'}</td>
                  <td className="mono">{log.job_uuid || '-'}</td>
                  <td>{log.status_code || '-'}</td>
                  <td className="mono">{log.url || '-'}</td>
                  <td>
                    <details>
                      <summary>Mostra</summary>
                      {log.request_payload && (
                        <pre>{JSON.stringify(log.request_payload, null, 2)}</pre>
                      )}
                      {log.response_payload && (
                        <pre>{JSON.stringify(log.response_payload, null, 2)}</pre>
                      )}
                      {log.error_text && (
                        <pre className="error-text">{log.error_text}</pre>
                      )}
                    </details>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      </div>
    </div>
  );
}
