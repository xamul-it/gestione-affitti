import { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigation } from '../../contexts/NavigationContext';
import { Download, Puzzle, Trash2, Upload, AlertTriangle, Plus } from 'lucide-react';
import { Button, Badge, Card, FormField } from '../../components/UI';
import { ConfirmDialog, EmptyState, ErrorMessage, LoadingSpinner } from '../../core/components/common';
import { FormModal } from '../../core/components';
import { useToast } from '../../core/hooks';
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
  const toast = useToast();

  // Dialoghi di conferma (sostituiscono window.confirm)
  const [restoreConfirmOpen, setRestoreConfirmOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteDropSchema, setDeleteDropSchema] = useState(false);
  const [deleting, setDeleting] = useState(false);

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
        toast.error('Sessione scaduta. Effettua di nuovo il login.');
        return;
      }
      const normalizedTenant = {
        schema_name: newTenant.schema_name.trim().toLowerCase(),
        nome_display: newTenant.nome_display.trim(),
        descrizione: newTenant.descrizione.trim() || null
      };
      if (!normalizedTenant.schema_name || !normalizedTenant.nome_display) {
        toast.warning('Compila i campi obbligatori.');
        return;
      }
      await axios.post(`${API_BASE_URL}/tenants/`, normalizedTenant, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Database creato con successo');
      setShowCreateForm(false);
      setNewTenant({ schema_name: '', nome_display: '', descrizione: '' });
      loadTenants();
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      if (status === 401) {
        toast.error('Sessione scaduta. Effettua di nuovo il login.');
        return;
      }
      toast.error(`Errore: ${detail || 'Creazione fallita'}`);
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

      toast.success('Backup scaricato con successo');
    } catch (err) {
      toast.error(`Errore backup: ${err.response?.data?.detail || 'Backup fallito'}`);
    }
  };

  const handleRestore = async (e) => {
    e.preventDefault();
    if (!restoreFile) {
      toast.warning('Seleziona un file di backup');
      return;
    }

    setRestoreConfirmOpen(true);
  };

  const executeRestore = async () => {
    setRestoreConfirmOpen(false);
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

      toast.success('Ripristino completato con successo');
      setShowRestoreForm(null);
      setRestoreFile(null);
      setRestoreConfirmOpen(false);
    } catch (err) {
      toast.error(`Errore ripristino: ${err.response?.data?.detail || 'Ripristino fallito'}`);
    }
  };

  const handleDelete = (tenantId, schemaName) => {
    setDeleteDropSchema(false);
    setDeleteTarget({ id: tenantId, schemaName });
  };

  const executeDelete = async () => {
    if (!deleteTarget) return;
    const dropSchema = deleteDropSchema;
    try {
      setDeleting(true);
      const token = localStorage.getItem('access_token');
      await axios.delete(`${API_BASE_URL}/tenants/${deleteTarget.id}`, {
        params: { drop_schema: dropSchema },
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Database eliminato con successo');
      loadTenants();
    } catch (err) {
      toast.error(`Errore eliminazione: ${err.response?.data?.detail || 'Eliminazione fallita'}`);
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
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
        toast.error('Sessione scaduta. Effettua di nuovo il login.');
        return;
      }
      if (enabled) {
        const response = await axios.post(
          `${API_BASE_URL}/tenants/${tenantId}/modules/${moduleId}/disable`,
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        );
        const failed = response.data?.tables_failed || [];
        if (failed.length > 0) {
          toast.warning(
            `Disabilitazione completata, ma non tutte le tabelle sono state rimosse.\n` +
            `Tabelle rimaste: ${failed.map((item) => item.table).join(', ')}`
          );
        }
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
      toast.error(`Errore moduli: ${err.response?.data?.detail || 'Operazione fallita'}`);
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
      toast.warning('Config non valida: inserisci JSON valido.');
      return;
    }

    try {
      setConfigSaving(true);
      const token = localStorage.getItem('access_token');
      if (!token) {
        toast.error('Sessione scaduta. Effettua di nuovo il login.');
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
      toast.error(`Errore configurazione: ${err.response?.data?.detail || 'Salvataggio fallito'}`);
    } finally {
      setConfigSaving(false);
    }
  };

  if (loading) return <LoadingSpinner message="Caricamento database..." />;

  const closeRestoreModal = () => {
    setShowRestoreForm(null);
    setRestoreFile(null);
  };

  const closeConfigEditor = () => {
    setConfigEditor(null);
    setConfigValue('');
  };

  return (
    <div className="database-management">
      <div className="page-header">
        <h1>Gestione Database</h1>
        <Button
          type="button"
          variant={showCreateForm ? 'secondary' : 'primary'}
          onClick={() => setShowCreateForm(!showCreateForm)}
        >
          {showCreateForm ? 'Annulla' : (<><Plus size={18} strokeWidth={1.7} aria-hidden="true" /> Nuovo Database</>)}
        </Button>
      </div>

      <ErrorMessage message={error} onRetry={loadTenants} onDismiss={() => setError(null)} />

      {/* Create Form */}
      {showCreateForm && (
        <Card className="create-form">
          <h2>Crea Nuovo Database</h2>
          <form onSubmit={handleCreateTenant}>
            <FormField label="Schema Name (tecnico) *" htmlFor="db-schema-name">
              <input
                id="db-schema-name"
                type="text"
                placeholder="tenant_nome"
                value={newTenant.schema_name}
                onChange={(e) => setNewTenant({ ...newTenant, schema_name: e.target.value })}
                pattern="[a-z0-9_-]+"
                title="Solo lettere minuscole, numeri, trattini e underscore"
                required
              />
              <small>Formato: tenant_nome (solo minuscole, numeri, _ e -)</small>
            </FormField>

            <FormField label="Nome Visualizzato *" htmlFor="db-nome-display">
              <input
                id="db-nome-display"
                type="text"
                placeholder="Database Produzione"
                value={newTenant.nome_display}
                onChange={(e) => setNewTenant({ ...newTenant, nome_display: e.target.value })}
                required
              />
            </FormField>

            <FormField label="Descrizione" htmlFor="db-descrizione">
              <textarea
                id="db-descrizione"
                placeholder="Descrizione del database..."
                value={newTenant.descrizione}
                onChange={(e) => setNewTenant({ ...newTenant, descrizione: e.target.value })}
                rows={3}
              />
            </FormField>

            <div className="form-actions">
              <Button type="submit" variant="primary">Crea Database</Button>
              <Button type="button" variant="secondary" onClick={() => setShowCreateForm(false)}>
                Annulla
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Tenants Table */}
      <Card>
        <h2>Database Esistenti ({tenants.length})</h2>
        {tenants.length === 0 ? (
          <EmptyState
            title="Nessun database trovato"
            message='Non ci sono database registrati. Clicca su "Nuovo Database" per iniziare.'
          />
        ) : (
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
                    <Badge variant={tenant.active ? 'success' : 'neutral'}>
                      {tenant.active ? 'Attivo' : 'Disattivato'}
                    </Badge>
                  </td>
                  <td>
                    <div className="action-buttons">
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={() => handleBackup(tenant.id, tenant.schema_name)}
                        title="Scarica backup"
                      >
                        <Download size={16} strokeWidth={1.7} aria-hidden="true" /> Backup
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={() => setShowRestoreForm(tenant.id)}
                        title="Ripristina da backup"
                      >
                        <Upload size={16} strokeWidth={1.7} aria-hidden="true" /> Ripristina
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={() => openModulesModal(tenant)}
                        title="Gestisci funzionalità"
                      >
                        <Puzzle size={16} strokeWidth={1.7} aria-hidden="true" /> Funzionalità
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="danger"
                        onClick={() => handleDelete(tenant.id, tenant.schema_name)}
                        title="Elimina database"
                      >
                        <Trash2 size={16} strokeWidth={1.7} aria-hidden="true" /> Elimina
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        )}
      </Card>

      {/* Restore Modal */}
      {showRestoreForm && (
        <FormModal title="Ripristina Database" size="small" onClose={closeRestoreModal}>
          <p className="warning-text" role="alert">
            <AlertTriangle size={18} strokeWidth={1.7} aria-hidden="true" />
            <span>ATTENZIONE: questa operazione sovrascriverà tutti i dati esistenti!</span>
          </p>
          <form onSubmit={handleRestore}>
            <FormField label="File di Backup (.sql) *" htmlFor="db-restore-file">
              <input
                id="db-restore-file"
                type="file"
                accept=".sql"
                onChange={(e) => setRestoreFile(e.target.files[0])}
                required
              />
              {restoreFile && (
                <small>File selezionato: {restoreFile.name}</small>
              )}
            </FormField>

            <div className="form-actions">
              <Button type="submit" variant="danger">Ripristina</Button>
              <Button type="button" variant="secondary" onClick={closeRestoreModal}>
                Annulla
              </Button>
            </div>
          </form>
        </FormModal>
      )}

      {/* Modules Modal */}
      {showModulesForTenant && (
        <FormModal
          title={`Funzionalità Database - ${showModulesForTenant.nome_display}`}
          size="large"
          onClose={() => setShowModulesForTenant(null)}
        >
          <ErrorMessage message={modulesError} onDismiss={() => setModulesError(null)} />
          {modulesLoading ? (
            <LoadingSpinner message="Caricamento moduli..." />
          ) : (
            <div className="modules-table">
              {tenantModules.map(module => (
                <div key={module.module_id} className="module-row">
                  <div className="module-main">
                    <div className="module-title">
                      <strong>{module.name}</strong>
                      <Badge variant={module.enabled ? 'success' : 'neutral'}>
                        {module.enabled ? 'Attivo' : 'Disattivo'}
                      </Badge>
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
                    <Button
                      type="button"
                      size="sm"
                      variant={module.enabled ? 'secondary' : 'primary'}
                      onClick={() => toggleTenantModule(
                        showModulesForTenant.id,
                        module.module_id,
                        module.enabled,
                        moduleSeedTestFlags[module.module_id]
                      )}
                    >
                      {module.enabled ? 'Disattiva' : 'Attiva'}
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="secondary"
                      onClick={() => openConfigEditor(showModulesForTenant.id, module)}
                    >
                      Config
                    </Button>
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
                aria-label={`Configurazione JSON del modulo ${configEditor.moduleId}`}
              />
              <div className="form-actions">
                <Button
                  type="button"
                  variant="primary"
                  onClick={saveModuleConfig}
                  loading={configSaving}
                >
                  {configSaving ? 'Salvataggio...' : 'Salva Config'}
                </Button>
                <Button type="button" variant="secondary" onClick={closeConfigEditor}>
                  Chiudi
                </Button>
              </div>
            </div>
          )}

          <div className="form-actions">
            <Button type="button" variant="secondary" onClick={() => setShowModulesForTenant(null)}>
              Chiudi
            </Button>
          </div>
        </FormModal>
      )}

      {/* Conferma eliminazione */}
      {deleteTarget && (
        <FormModal
          title="Elimina database"
          size="small"
          onClose={() => !deleting && setDeleteTarget(null)}
        >
          <p className="warning-text" role="alert">
            <AlertTriangle size={18} strokeWidth={1.7} aria-hidden="true" />
            <span>
              Eliminare il database <strong>{deleteTarget.schemaName}</strong>? Questa operazione è IRREVERSIBILE.
            </span>
          </p>
          <label className="module-testdata-flag delete-drop-flag">
            <input
              type="checkbox"
              checked={deleteDropSchema}
              onChange={(e) => setDeleteDropSchema(e.target.checked)}
              disabled={deleting}
            />
            Elimina anche lo schema e tutti i dati (irreversibile). Se non selezionato, viene eliminato solo il record e lo schema rimane nel database.
          </label>
          <div className="form-actions">
            <Button type="button" variant="danger" onClick={executeDelete} loading={deleting}>
              {deleting ? 'Eliminazione...' : 'Elimina'}
            </Button>
            <Button type="button" variant="secondary" onClick={() => setDeleteTarget(null)} disabled={deleting}>
              Annulla
            </Button>
          </div>
        </FormModal>
      )}

      {/* Conferma ripristino */}
      <ConfirmDialog
        isOpen={restoreConfirmOpen}
        title="Conferma ripristino"
        message="ATTENZIONE: il ripristino sovrascriverà tutti i dati esistenti. Continuare?"
        confirmLabel="Ripristina"
        variant="danger"
        onConfirm={executeRestore}
        onCancel={() => setRestoreConfirmOpen(false)}
      />
    </div>
  );
}
