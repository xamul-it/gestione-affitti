import { useEffect, useState } from 'react';
import axios from 'axios';
import { useTenant } from '../../contexts/TenantContext';
import './TenantModules.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export default function TenantModules() {
  const { currentTenant } = useTenant();
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [configEditor, setConfigEditor] = useState(null);
  const [configValue, setConfigValue] = useState('');
  const [configSaving, setConfigSaving] = useState(false);

  useEffect(() => {
    if (!currentTenant) {
      setLoading(false);
      return;
    }
    loadTenantModules(currentTenant.id);
  }, [currentTenant?.id]);

  const loadTenantModules = async (tenantId) => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('Sessione scaduta. Effettua di nuovo il login.');
        return;
      }
      const response = await axios.get(`${API_BASE_URL}/tenants/${tenantId}/modules`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setModules(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore nel caricamento moduli');
    } finally {
      setLoading(false);
    }
  };

  const toggleTenantModule = async (moduleId, enabled) => {
    if (!currentTenant) return;
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        alert('Sessione scaduta. Effettua di nuovo il login.');
        return;
      }
      if (enabled) {
        await axios.post(
          `${API_BASE_URL}/tenants/${currentTenant.id}/modules/${moduleId}/disable`,
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        );
      } else {
        await axios.post(
          `${API_BASE_URL}/tenants/${currentTenant.id}/modules/install`,
          { module_id: moduleId },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }
      await loadTenantModules(currentTenant.id);
    } catch (err) {
      alert(`Errore moduli: ${err.response?.data?.detail || 'Operazione fallita'}`);
    }
  };

  const openConfigEditor = (module) => {
    setConfigEditor({ moduleId: module.module_id });
    setConfigValue(JSON.stringify(module.config || {}, null, 2));
  };

  const saveModuleConfig = async () => {
    if (!configEditor || !currentTenant) return;
    let parsedConfig = {};
    try {
      parsedConfig = configValue ? JSON.parse(configValue) : {};
    } catch (err) {
      alert('Config non valida: inserisci JSON valido.');
      return;
    }

    try {
      setConfigSaving(true);
      const token = localStorage.getItem('access_token');
      if (!token) {
        alert('Sessione scaduta. Effettua di nuovo il login.');
        return;
      }
      await axios.put(
        `${API_BASE_URL}/tenants/${currentTenant.id}/modules/${configEditor.moduleId}/config`,
        { config: parsedConfig },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      await loadTenantModules(currentTenant.id);
      setConfigEditor(null);
      setConfigValue('');
    } catch (err) {
      alert(`Errore configurazione: ${err.response?.data?.detail || 'Salvataggio fallito'}`);
    } finally {
      setConfigSaving(false);
    }
  };

  if (!currentTenant && !loading) {
    return (
      <div className="tenant-modules">
        <div className="tenant-modules-empty">
          <h2>Nessun tenant selezionato</h2>
          <p>Seleziona un tenant per gestire le sue funzionalità.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="tenant-modules">
        <div className="loading">Caricamento moduli...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="tenant-modules">
        <div className="tenant-modules-error">
          <h2>Errore</h2>
          <p>{error}</p>
          {currentTenant && (
            <button className="btn btn-primary" onClick={() => loadTenantModules(currentTenant.id)}>
              Riprova
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="tenant-modules">
      <div className="tenant-modules-header">
        <div>
          <h1>Funzionalità Tenant</h1>
          {currentTenant && (
            <p className="tenant-modules-subtitle">
              Gestione moduli per: <strong>{currentTenant.nome_display}</strong>
            </p>
          )}
        </div>
      </div>

      {modules.length === 0 ? (
        <div className="tenant-modules-empty">
          <p>Nessun modulo disponibile.</p>
        </div>
      ) : (
        <div className="tenant-modules-list">
          {modules.map((module) => (
            <div key={module.module_id} className="tenant-modules-item">
              <div className="module-main">
                <div className="module-title">
                  <strong>{module.name}</strong>
                  <span className={`module-status ${module.enabled ? 'enabled' : 'disabled'}`}>
                    {module.enabled ? 'Attivo' : 'Disattivo'}
                  </span>
                </div>
                <div className="module-meta">
                  <code>{module.module_id}</code>
                  <span className="module-meta-sep">•</span>
                  <span>Tabelle: {module.table_count}</span>
                </div>
              </div>
              <div className="module-actions">
                <button
                  className={`btn btn-sm ${module.enabled ? 'btn-outline' : 'btn-primary'}`}
                  onClick={() => toggleTenantModule(module.module_id, module.enabled)}
                >
                  {module.enabled ? 'Disabilita' : 'Abilita'}
                </button>
                <button
                  className="btn btn-sm btn-secondary"
                  onClick={() => openConfigEditor(module)}
                >
                  Config
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {configEditor && (
        <div className="tenant-config-editor">
          <h3>Configurazione modulo</h3>
          <textarea
            rows="8"
            value={configValue}
            onChange={(e) => setConfigValue(e.target.value)}
          />
          <div className="tenant-config-actions">
            <button
              className="btn btn-secondary"
              onClick={() => {
                setConfigEditor(null);
                setConfigValue('');
              }}
              disabled={configSaving}
            >
              Annulla
            </button>
            <button
              className="btn btn-primary"
              onClick={saveModuleConfig}
              disabled={configSaving}
            >
              {configSaving ? 'Salvataggio...' : 'Salva'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
