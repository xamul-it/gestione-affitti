import { useState } from 'react';
import axios from 'axios';
import './CoreCleanup.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export default function CoreCleanup() {
  const [schemaName, setSchemaName] = useState('public');
  const [forceClose, setForceClose] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleCleanup = async () => {
    const target = schemaName.trim();
    if (!target) {
      setError('Inserisci uno schema.');
      return;
    }
    const confirmed = window.confirm(
      `Confermi la pulizia core sullo schema "${target}"? Verranno eliminate tutte le tabelle NON core.`
    );
    if (!confirmed) {
      return;
    }

    try {
      setActionLoading(true);
      setError(null);
      setResult(null);
      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('Sessione scaduta. Effettua di nuovo il login.');
        return;
      }
      const response = await axios.post(
        `${API_BASE_URL}/admin/core/cleanup`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { schema_name: target, force: forceClose }
        }
      );
      const dropped = response.data?.tables_dropped || [];
      setResult({
        schema: response.data?.schema || target,
        droppedCount: dropped.length,
        droppedTables: dropped,
        terminatedConnections: response.data?.terminated_connections ?? 0,
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Operazione fallita');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="core-cleanup">
      <div className="core-cleanup-header">
        <h1>Pulizia Core</h1>
        <p>Elimina tutte le tabelle NON core (prefisso diverso da core_).</p>
      </div>

      <div className="core-cleanup-card">
        <div className="core-cleanup-row">
          <label htmlFor="schema-name">Schema</label>
          <input
            id="schema-name"
            type="text"
            value={schemaName}
            onChange={(event) => setSchemaName(event.target.value)}
          />
        </div>
        <label className="core-cleanup-force">
          <input
            type="checkbox"
            checked={forceClose}
            onChange={(event) => setForceClose(event.target.checked)}
          />
          Forza chiusura connessioni al DB
        </label>

        <div className="core-cleanup-actions">
          <button
            type="button"
            className="btn btn-danger"
            onClick={handleCleanup}
            disabled={actionLoading}
          >
            {actionLoading ? 'Pulizia...' : 'Pulizia core'}
          </button>
        </div>

        {error && <div className="core-cleanup-error">{error}</div>}

        {result && (
          <div className="core-cleanup-result">
            <strong>Schema:</strong> {result.schema} <br />
            <strong>Tabelle eliminate:</strong> {result.droppedCount}
            <br />
            <strong>Connessioni terminate:</strong> {result.terminatedConnections}
            {result.droppedTables.length > 0 && (
              <div className="core-cleanup-table-list">
                {result.droppedTables.map((table) => (
                  <span key={table} className="core-cleanup-table-pill">{table}</span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
