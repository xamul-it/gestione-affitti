import { useEffect, useState } from 'react';
import axios from 'axios';
import './TenantMaintenance.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export default function TenantMaintenance() {
  const [tenants, setTenants] = useState([]);
  const [selectedTenant, setSelectedTenant] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    loadTenants();
  }, []);

  const loadTenants = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('Sessione scaduta. Effettua di nuovo il login.');
        return;
      }
      const response = await axios.get(`${API_BASE_URL}/tenants`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { active_only: true }
      });
      setTenants(response.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore nel caricamento dei tenant');
    } finally {
      setLoading(false);
    }
  };

  const handleClearTables = async () => {
    if (!selectedTenant) {
      setError('Seleziona un tenant.');
      return;
    }
    const target = tenants.find((tenant) => String(tenant.id) === String(selectedTenant));
    const label = target?.nome_display || target?.schema_name || selectedTenant;

    const confirmed = window.confirm(
      `Confermi la cancellazione di TUTTE le tabelle per il tenant "${label}"? Questa operazione elimina tutti i dati tenant.`
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
        `${API_BASE_URL}/tenants/${selectedTenant}/clear-tables`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const dropped = response.data?.tables_dropped || [];
      setResult({
        label,
        droppedCount: dropped.length,
        droppedTables: dropped,
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Operazione fallita');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="tenant-maintenance">
      <div className="tenant-maintenance-header">
        <h1>Reset Tenant</h1>
        <p>Operazioni distruttive sui dati tenant (solo admin).</p>
      </div>

      {loading ? (
        <div className="tenant-maintenance-loading">Caricamento tenant...</div>
      ) : (
        <div className="tenant-maintenance-card">
          <div className="tenant-maintenance-row">
            <label htmlFor="tenant-select">Tenant</label>
            <select
              id="tenant-select"
              value={selectedTenant}
              onChange={(event) => setSelectedTenant(event.target.value)}
            >
              <option value="">Seleziona un tenant</option>
              {tenants.map((tenant) => (
                <option key={tenant.id} value={tenant.id}>
                  {tenant.nome_display} ({tenant.schema_name})
                </option>
              ))}
            </select>
          </div>

          <div className="tenant-maintenance-actions">
            <button
              type="button"
              className="btn btn-danger"
              onClick={handleClearTables}
              disabled={actionLoading || !selectedTenant}
            >
              {actionLoading ? 'Cancellazione...' : 'Cancella tutte le tabelle'}
            </button>
          </div>

          {error && <div className="tenant-maintenance-error">{error}</div>}

          {result && (
            <div className="tenant-maintenance-result">
              <strong>Tenant:</strong> {result.label} <br />
              <strong>Tabelle eliminate:</strong> {result.droppedCount}
              {result.droppedTables.length > 0 && (
                <div className="tenant-maintenance-table-list">
                  {result.droppedTables.map((table) => (
                    <span key={table} className="tenant-maintenance-table-pill">{table}</span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
