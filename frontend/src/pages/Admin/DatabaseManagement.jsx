import { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigation } from '../../contexts/NavigationContext';
import './DatabaseManagement.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export default function DatabaseManagement() {
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showRestoreForm, setShowRestoreForm] = useState(null);
  const [showModulesForTenant, setShowModulesForTenant] = useState(null);
  const [tenantModules, setTenantModules] = useState([]);
  const [modulesLoading, setModulesLoading] = useState(false);
  const [modulesError, setModulesError] = useState(null);
  const [moduleSeedTestFlags, setModuleSeedTestFlags] = useState({});
  const [configEditor, setConfigEditor] = useState(null);
  const [configValue, setConfigValue] = useState('');
  const [configSaving, setConfigSaving] = useState(false);
  const { loadMenu } = useNavigation();

  // Form states
  const [newTenant, setNewTenant] = useState({
    schema_name: '',
    nome_display: '',
    descrizione: ''
  });
  const [restoreFile, setRestoreFile] = useState(null);

  useEffect(() => {
    loadTenants();
  }, []);

  const loadTenants = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${API_BASE_URL}/tenants/my-tenants`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTenants(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore nel caricamento database');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTenant = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        alert('Sessione scaduta. Effettua di nuovo il login.');
        return;
      }
      const normalizedTenant = {
        schema_name: newTenant.schema_name.trim().toLowerCase(),
        nome_display: newTenant.nome_display.trim(),
        descrizione: newTenant.descrizione.trim() || null
      };
      if (!normalizedTenant.schema_name || !normalizedTenant.nome_display) {
        alert('Compila i campi obbligatori.');
        return;
      }
      await axios.post(`${API_BASE_URL}/tenants/`, normalizedTenant, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert('Database creato con successo!');
      setShowCreateForm(false);
      setNewTenant({ schema_name: '', nome_display: '', descrizione: '' });
      loadTenants();
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      if (status === 401) {
        alert('Sessione scaduta. Effettua di nuovo il login.');
        return;
      }
      alert(`Errore: ${detail || 'Creazione fallita'}`);
    }
  };

  const handleBackup = async (tenantId, schemaName) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.post(
        `${API_BASE_URL}/tenants/${tenantId}/backup`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `backup_${schemaName}_${new Date().toISOString().split('T')[0]}.sql`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      alert('Backup scaricato con successo!');
    } catch (err) {
      alert(`Errore backup: ${err.response?.data?.detail || 'Backup fallito'}`);
    }
  };

  const handleRestore = async (e) => {
    e.preventDefault();
    if (!restoreFile) {
      alert('Seleziona un file di backup');
      return;
    }

    if (!window.confirm('ATTENZIONE: Il ripristino sovrascriverà tutti i dati esistenti. Continuare?')) {
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const formData = new FormData();
      formData.append('backup_file', restoreFile);

      await axios.post(
        `${API_BASE_URL}/tenants/${showRestoreForm}/restore`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      alert('Ripristino completato con successo!');
      setShowRestoreForm(null);
      setRestoreFile(null);
    } catch (err) {
      alert(`Errore ripristino: ${err.response?.data?.detail || 'Ripristino fallito'}`);
    }
  };

  const handleDelete = async (tenantId, schemaName) => {
    if (!window.confirm(`ATTENZIONE: Eliminare il database "${schemaName}"?\n\nQuesta operazione è IRREVERSIBILE!`)) {
      return;
    }

    const dropSchema = window.confirm(
      'Vuoi anche eliminare permanentemente lo schema e tutti i dati?\n\n' +
      'SI = Elimina tutto (irreversibile)\n' +
      'NO = Elimina solo il record (lo schema rimane nel database)'
    );

    try {
      const token = localStorage.getItem('access_token');
      await axios.delete(`${API_BASE_URL}/tenants/${tenantId}`, {
        params: { drop_schema: dropSchema },
        headers: { Authorization: `Bearer ${token}` }
      });

      alert('Database eliminato con successo!');
      loadTenants();
    } catch (err) {
      alert(`Errore eliminazione: ${err.response?.data?.detail || 'Eliminazione fallita'}`);
    }
  };

  const loadTenantModules = async (tenantId) => {
    try {
      setModulesLoading(true);
      setModulesError(null);
      const token = localStorage.getItem('access_token');
      if (!token) {
        setModulesError('Sessione scaduta. Effettua di nuovo il login.');
        return;
      }
      const response = await axios.get(`${API_BASE_URL}/tenants/${tenantId}/modules`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTenantModules(response.data);
    } catch (err) {
      setModulesError(err.response?.data?.detail || 'Errore nel caricamento moduli');
    } finally {
      setModulesLoading(false);
    }
  };

  const openModulesModal = async (tenant) => {
    setShowModulesForTenant(tenant);
    setTenantModules([]);
    setModulesError(null);
    setConfigEditor(null);
    setConfigValue('');
    setModuleSeedTestFlags({});
    await loadTenantModules(tenant.id);
  };

  const toggleTenantModule = async (tenantId, moduleId, enabled, seedTestData = false) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        alert('Sessione scaduta. Effettua di nuovo il login.');
        return;
      }
      if (enabled) {
        await axios.post(
          `${API_BASE_URL}/tenants/${tenantId}/modules/${moduleId}/disable`,
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        );
      } else {
        await axios.post(
          `${API_BASE_URL}/tenants/${tenantId}/modules/install`,
          { module_id: moduleId, seed_test_data: seedTestData },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setModuleSeedTestFlags(prev => ({ ...prev, [moduleId]: false }));
      }
      await loadTenantModules(tenantId);
      await loadMenu();
    } catch (err) {
      alert(`Errore moduli: ${err.response?.data?.detail || 'Operazione fallita'}`);
    }
  };

  const openConfigEditor = (tenantId, module) => {
    setConfigEditor({ tenantId, moduleId: module.module_id });
    setConfigValue(JSON.stringify(module.config || {}, null, 2));
  };

  const saveModuleConfig = async () => {
    if (!configEditor) return;
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
        `${API_BASE_URL}/tenants/${configEditor.tenantId}/modules/${configEditor.moduleId}/config`,
        { config: parsedConfig },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      await loadTenantModules(configEditor.tenantId);
      setConfigEditor(null);
      setConfigValue('');
    } catch (err) {
      alert(`Errore configurazione: ${err.response?.data?.detail || 'Salvataggio fallito'}`);
    } finally {
      setConfigSaving(false);
    }
  };

  if (loading) return <div className="loading">Caricamento database...</div>;

  return (
    <div className="database-management">
      <div className="page-header">
        <h1>Gestione Database</h1>
        <button
          className="btn btn-primary"
          onClick={() => setShowCreateForm(!showCreateForm)}
        >
          {showCreateForm ? 'Annulla' : '+ Nuovo Database'}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Create Form */}
      {showCreateForm && (
        <div className="card create-form">
          <h2>Crea Nuovo Database</h2>
          <form onSubmit={handleCreateTenant}>
            <div className="form-group">
              <label>Schema Name (tecnico)*</label>
              <input
                type="text"
                placeholder="tenant_nome"
                value={newTenant.schema_name}
                onChange={(e) => setNewTenant({ ...newTenant, schema_name: e.target.value })}
                pattern="[a-z0-9_-]+"
                title="Solo lettere minuscole, numeri, trattini e underscore"
                required
              />
              <small>Formato: tenant_nome (solo minuscole, numeri, _ e -)</small>
            </div>

            <div className="form-group">
              <label>Nome Visualizzato*</label>
              <input
                type="text"
                placeholder="Database Produzione"
                value={newTenant.nome_display}
                onChange={(e) => setNewTenant({ ...newTenant, nome_display: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label>Descrizione</label>
              <textarea
                placeholder="Descrizione del database..."
                value={newTenant.descrizione}
                onChange={(e) => setNewTenant({ ...newTenant, descrizione: e.target.value })}
                rows={3}
              />
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn-primary">Crea Database</button>
              <button type="button" className="btn btn-secondary" onClick={() => setShowCreateForm(false)}>
                Annulla
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tenants Table */}
      <div className="card">
        <h2>Database Esistenti ({tenants.length})</h2>
        <div className="table-responsive">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Schema</th>
                <th>Nome</th>
                <th>Descrizione</th>
                <th>Stato</th>
                <th>Azioni</th>
              </tr>
            </thead>
            <tbody>
              {tenants.map((tenant) => (
                <tr key={tenant.id}>
                  <td>{tenant.id}</td>
                  <td><code>{tenant.schema_name}</code></td>
                  <td><strong>{tenant.nome_display}</strong></td>
                  <td>{tenant.descrizione}</td>
                  <td>
                    <span className={`badge ${tenant.active ? 'badge-success' : 'badge-secondary'}`}>
                      {tenant.active ? 'Attivo' : 'Disattivato'}
                    </span>
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button
                        className="btn btn-sm btn-info"
                        onClick={() => handleBackup(tenant.id, tenant.schema_name)}
                        title="Scarica backup"
                      >
                        📥 Backup
                      </button>
                      <button
                        className="btn btn-sm btn-warning"
                        onClick={() => setShowRestoreForm(tenant.id)}
                        title="Ripristina da backup"
                      >
                        📤 Ripristina
                      </button>
                      <button
                        className="btn btn-sm btn-danger"
                        onClick={() => handleDelete(tenant.id, tenant.schema_name)}
                        title="Elimina database"
                      >
                        🗑️ Elimina
                      </button>
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => openModulesModal(tenant)}
                        title="Gestisci funzionalità"
                      >
                        🧩 Funzionalità
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Restore Modal */}
      {showRestoreForm && (
        <div className="modal-overlay" onClick={() => setShowRestoreForm(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Ripristina Database</h2>
            <p className="warning-text">
              ⚠️ ATTENZIONE: Questa operazione sovrascriverà tutti i dati esistenti!
            </p>
            <form onSubmit={handleRestore}>
              <div className="form-group">
                <label>File di Backup (.sql)*</label>
                <input
                  type="file"
                  accept=".sql"
                  onChange={(e) => setRestoreFile(e.target.files[0])}
                  required
                />
                {restoreFile && (
                  <small>File selezionato: {restoreFile.name}</small>
                )}
              </div>

              <div className="form-actions">
                <button type="submit" className="btn btn-warning">
                  Ripristina
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowRestoreForm(null);
                    setRestoreFile(null);
                  }}
                >
                  Annulla
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modules Modal */}
      {showModulesForTenant && (
        <div className="modal-overlay" onClick={() => setShowModulesForTenant(null)}>
          <div className="modal-content modal-wide" onClick={(e) => e.stopPropagation()}>
            <h2>Funzionalità Database - {showModulesForTenant.nome_display}</h2>
            {modulesError && <div className="alert alert-error">{modulesError}</div>}
            {modulesLoading ? (
              <div className="loading">Caricamento moduli...</div>
            ) : (
              <div className="modules-table">
                {tenantModules.map(module => (
                  <div key={module.module_id} className="module-row">
                    <div className="module-main">
                      <div className="module-title">
                        <strong>{module.name}</strong>
                        <span className={`badge ${module.enabled ? 'badge-success' : 'badge-secondary'}`}>
                          {module.enabled ? 'Attivo' : 'Disattivo'}
                        </span>
                      </div>
                      <div className="module-meta">
                        <code>{module.module_id}</code>
                      </div>
                    </div>
                    <div className="module-actions">
                      {!module.enabled && (
                        <label className="module-testdata-flag">
                          <input
                            type="checkbox"
                            checked={!!moduleSeedTestFlags[module.module_id]}
                            onChange={(e) => setModuleSeedTestFlags(prev => ({
                              ...prev,
                              [module.module_id]: e.target.checked,
                            }))}
                          />
                          Dati di test
                        </label>
                      )}
                      <button
                        className={`btn btn-sm ${module.enabled ? 'btn-warning' : 'btn-primary'}`}
                        onClick={() => toggleTenantModule(
                          showModulesForTenant.id,
                          module.module_id,
                          module.enabled,
                          moduleSeedTestFlags[module.module_id]
                        )}
                      >
                        {module.enabled ? 'Disattiva' : 'Attiva'}
                      </button>
                      <button
                        className="btn btn-sm btn-info"
                        onClick={() => openConfigEditor(showModulesForTenant.id, module)}
                      >
                        Config
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {configEditor && (
              <div className="config-editor">
                <h3>Config modulo: {configEditor.moduleId}</h3>
                <textarea
                  value={configValue}
                  onChange={(e) => setConfigValue(e.target.value)}
                  rows={8}
                />
                <div className="form-actions">
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={saveModuleConfig}
                    disabled={configSaving}
                  >
                    {configSaving ? 'Salvataggio...' : 'Salva Config'}
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => {
                      setConfigEditor(null);
                      setConfigValue('');
                    }}
                  >
                    Chiudi
                  </button>
                </div>
              </div>
            )}

            <div className="form-actions">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowModulesForTenant(null)}
              >
                Chiudi
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
