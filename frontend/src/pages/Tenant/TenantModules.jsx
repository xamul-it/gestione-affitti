import { useEffect, useState } from 'react';
import axios from 'axios';
import { renderIcon } from '../../components/Navigation/iconRegistry.jsx';
import { useTenant } from '../../contexts/TenantContext';
import { useNavigation } from '../../contexts/NavigationContext';
import { loadLocalModuleManifests } from '../../core/modules/localManifests.js';
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
  const [localManifests, setLocalManifests] = useState({});
  const [dropTablesByModule, setDropTablesByModule] = useState({});
  const [seedTestDataByModule, setSeedTestDataByModule] = useState({});
  const { loadMenu } = useNavigation();

  useEffect(() => {
    if (!currentTenant) {
      setLoading(false);
      return;
    }
    loadTenantModules(currentTenant.id);
    loadLocalModuleManifests().then(setLocalManifests);
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

  const toggleTenantModule = async (
    moduleId,
    enabled,
    dropTables = false,
    seedTestData = false
  ) => {
    if (!currentTenant) return;
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        alert('Sessione scaduta. Effettua di nuovo il login.');
        return;
      }
      if (enabled) {
        if (dropTables) {
          const confirmed = window.confirm(
            'Confermi la disabilitazione con cancellazione delle tabelle? Questa operazione elimina i dati del modulo per il tenant.'
          );
          if (!confirmed) {
            return;
          }
        }
        const response = await axios.post(
          `${API_BASE_URL}/tenants/${currentTenant.id}/modules/${moduleId}/disable`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` },
            params: dropTables ? { drop_tables: true } : undefined,
          }
        );
        if (dropTables) {
          const failed = response.data?.tables_failed || [];
          if (failed.length > 0) {
            alert(
              `Disabilitazione completata, ma non tutte le tabelle sono state rimosse.\n` +
              `Tabelle rimaste: ${failed.map((item) => item.table).join(', ')}`
            );
          }
        }
      } else {
        await axios.post(
          `${API_BASE_URL}/tenants/${currentTenant.id}/modules/install`,
          { module_id: moduleId, seed_test_data: seedTestData },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }
      setDropTablesByModule((prev) => ({ ...prev, [moduleId]: false }));
      setSeedTestDataByModule((prev) => ({ ...prev, [moduleId]: false }));
      await loadTenantModules(currentTenant.id);
      await loadMenu();
    } catch (err) {
      alert(`Errore moduli: ${err.response?.data?.detail || 'Operazione fallita'}`);
    }
  };

  const forceUpdateModule = async (moduleId) => {
    if (!currentTenant) return;
    try {
      const token = localStorage.getItem('access_token');
      await axios.post(
        `${API_BASE_URL}/tenants/${currentTenant.id}/modules/${moduleId}/force-update`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      await loadTenantModules(currentTenant.id);
      await loadMenu();
    } catch (err) {
      alert(`Errore aggiornamento: ${err.response?.data?.detail || 'Operazione fallita'}`);
    }
  };

  const reseedModule = async (moduleId) => {
    if (!currentTenant) return;
    const confirmed = window.confirm(
      `Confermi il caricamento dei dati di esempio nel tenant «${currentTenant.nome_display}»? Potrebbe creare righe duplicate se eseguito più volte.`
    );
    if (!confirmed) {
      return;
    }
    try {
      const token = localStorage.getItem('access_token');
      await axios.post(
        `${API_BASE_URL}/tenants/${currentTenant.id}/modules/${moduleId}/reseed`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert('Dati di esempio caricati.');
    } catch (err) {
      alert(`Errore caricamento dati di esempio: ${err.response?.data?.detail || 'Operazione fallita'}`);
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
        <div className="tenant-modules-groups">
          {Object.entries(
            modules.reduce((acc, module) => {
              const local = localManifests[module.module_id]
              const category = (local?.category || module.category || 'other').toLowerCase()
              if (!acc[category]) acc[category] = []
              acc[category].push(module)
              return acc
            }, {})
          )
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([category, groupModules]) => (
              <section key={category} className="tenant-modules-group">
                <div className="tenant-modules-group-header">
                  <h2>{category}</h2>
                  <span className="tenant-modules-group-count">{groupModules.length} moduli</span>
                </div>
                <div className="tenant-modules-grid">
                  {[...groupModules]
                    .sort((a, b) => (a.name || '').toLowerCase().localeCompare((b.name || '').toLowerCase()))
                    .map(module => {
                      const local = localManifests[module.module_id]
                      const displayName = local?.displayName || module.name
                      const displayDescription = local?.description || module.description
                      const displayIcon = local?.icon || module.icon
                      return (
                    <div key={module.module_id} className="tenant-module-card">
                      <div className="tenant-module-header">
                        <div className="tenant-module-info">
                          <div className="tenant-module-title">
                            <span className="tenant-module-title-icon" aria-hidden="true">
                              {renderIcon(displayIcon || 'package', { size: 18, fallbackClassName: 'tenant-module-icon-emoji' })}
                            </span>
                            <h3>{displayName}</h3>
                          </div>
                          {module.version && <span className="tenant-module-version">v{module.version}</span>}
                        </div>
                        <div className="tenant-module-status">
                          <span className={`status-badge ${module.enabled ? 'active' : 'inactive'}`}>
                            {module.enabled ? 'Attivo' : 'Disattivo'}
                          </span>
                          {module.needs_update && (
                            <span className="status-badge needs-update">
                              Aggiornamento richiesto
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="tenant-module-body">
                        <p className="tenant-module-description">
                          {displayDescription || 'Nessuna descrizione disponibile'}
                        </p>

                        {module.author && (
                          <p className="tenant-module-author">
                            <strong>Autore:</strong> {module.author}
                          </p>
                        )}

                        <p className="tenant-module-technical-name">
                          <strong>Nome tecnico:</strong> <code>{module.module_id}</code>
                        </p>

                        <div className="tenant-module-tables">
                          <strong>Tabelle presenti ({module.tenant_tables?.length ?? 0}):</strong>
                          {module.tenant_tables && module.tenant_tables.length > 0 ? (
                            <div className="tenant-module-tables-list">
                              {module.tenant_tables.map(table => (
                                <span key={table} className="tenant-module-table-pill">
                                  {table}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="tenant-module-tables-empty">Nessuna</span>
                          )}
                        </div>

                        <div className="tenant-module-dependencies">
                          <strong>Dipendenze:</strong>
                          {module.dependencies && module.dependencies.length > 0 ? (
                            <ul>
                              {module.dependencies.map(dep => (
                                <li key={dep}><code>{dep}</code></li>
                              ))}
                            </ul>
                          ) : (
                            <span className="tenant-module-dependencies-empty">Nessuna</span>
                          )}
                        </div>

                        <div className="tenant-module-actions">
                          {module.needs_update && module.enabled ? (
                            <>
                              <p className="tenant-module-update-notice">
                                Le tabelle di questo tenant non sono allineate alla versione
                                corrente del modulo ({module.installed_version} → {module.version}).
                                Disabilita il modulo oppure forza l'aggiornamento delle tabelle.
                              </p>
                              <button
                                className="btn btn-sm btn-outline"
                                onClick={() => toggleTenantModule(module.module_id, true, false, false)}
                              >
                                Disabilita
                              </button>
                              <button
                                className="btn btn-sm btn-primary"
                                onClick={() => forceUpdateModule(module.module_id)}
                              >
                                Forza aggiornamento
                              </button>
                            </>
                          ) : (
                            <>
                              {!module.enabled && (
                                <label className="tenant-module-testdata-toggle">
                                  <input
                                    type="checkbox"
                                    checked={!!seedTestDataByModule[module.module_id]}
                                    onChange={(event) =>
                                      setSeedTestDataByModule((prev) => ({
                                        ...prev,
                                        [module.module_id]: event.target.checked,
                                      }))
                                    }
                                  />
                                  Carica dati di test
                                </label>
                              )}
                              {module.enabled && (
                                <label className="tenant-module-drop-toggle">
                                  <input
                                    type="checkbox"
                                    checked={!!dropTablesByModule[module.module_id]}
                                    onChange={(event) =>
                                      setDropTablesByModule((prev) => ({
                                        ...prev,
                                        [module.module_id]: event.target.checked,
                                      }))
                                    }
                                  />
                                  Cancella tabelle tenant
                                </label>
                              )}
                              <button
                                className={`btn btn-sm ${module.enabled ? 'btn-outline' : 'btn-primary'}`}
                                onClick={() => toggleTenantModule(
                                  module.module_id,
                                  module.enabled,
                                  !!dropTablesByModule[module.module_id],
                                  !!seedTestDataByModule[module.module_id]
                                )}
                              >
                                {module.enabled ? 'Disabilita' : 'Abilita'}
                              </button>
                              <button
                                className="btn btn-sm btn-secondary"
                                onClick={() => openConfigEditor(module)}
                              >
                                Config
                              </button>
                              {module.enabled && (
                                <button
                                  className="btn btn-sm btn-secondary"
                                  onClick={() => reseedModule(module.module_id)}
                                >
                                  Carica dati di esempio
                                </button>
                              )}
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                      )
                    })}
                </div>
              </section>
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
