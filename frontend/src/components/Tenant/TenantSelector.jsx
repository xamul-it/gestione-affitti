import { useState, useEffect, useRef } from 'react';
import { useTenant } from '../../contexts/TenantContext';
import axios from 'axios';
import './TenantSelector.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export function TenantSelector({ onTenantSelected }) {
  const { availableTenants, switchTenant, loading, error, refreshTenants, fetchUserTenants } = useTenant();
  const [selectedTenantId, setSelectedTenantId] = useState(null);
  const [switching, setSwitching] = useState(false);
  const [settingDefault, setSettingDefault] = useState(null);
  const fetchedRef = useRef(false);

  // Fetch tenants on mount — un'unica chiamata grazie al ref
  useEffect(() => {
    if (fetchedRef.current || availableTenants.length > 0) return;
    fetchedRef.current = true;
    fetchUserTenants().catch(err => {
      console.error('Failed to fetch tenants:', err);
      fetchedRef.current = false; // consenti retry se fallisce
    });
  }, []);

  useEffect(() => {
    // Auto-select if only one tenant (but only if not coming from a page reload after switch)
    const hasJustSwitched = sessionStorage.getItem('tenant_just_switched');

    if (availableTenants.length === 1 && !hasJustSwitched) {
      handleTenantSwitch(availableTenants[0].id);
    } else if (availableTenants.length > 0) {
      // Clear the flag after page reload
      sessionStorage.removeItem('tenant_just_switched');

      // Pre-select default tenant
      const defaultTenant = availableTenants.find(t => t.is_default);
      if (defaultTenant) {
        setSelectedTenantId(defaultTenant.id);
      }
    }
  }, [availableTenants]);

  const handleTenantSwitch = async (tenantId) => {
    try {
      setSwitching(true);
      // Set flag before switching to prevent auto-switch loop
      sessionStorage.setItem('tenant_just_switched', 'true');
      await switchTenant(tenantId);
      if (onTenantSelected) {
        onTenantSelected();
      }
    } catch (err) {
      console.error('Failed to switch tenant:', err);
      sessionStorage.removeItem('tenant_just_switched');
      setSwitching(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (selectedTenantId) {
      handleTenantSwitch(selectedTenantId);
    }
  };

  const handleSetDefault = async (tenantId, e) => {
    e.stopPropagation(); // Prevent selecting the tenant
    try {
      setSettingDefault(tenantId);
      const token = localStorage.getItem('access_token');
      await axios.post(
        `${API_BASE_URL}/tenants/set-default/${tenantId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Refresh tenant list to update default flag
      if (refreshTenants) {
        await refreshTenants();
      }
    } catch (err) {
      console.error('Failed to set default tenant:', err);
      alert('Errore nell\'impostazione del database predefinito');
    } finally {
      setSettingDefault(null);
    }
  };

  if (loading) {
    return (
      <div className="tenant-selector-container">
        <div className="tenant-selector-card">
          <div className="tenant-selector-loading">
            <div className="spinner"></div>
            <p>Caricamento tenant...</p>
          </div>
        </div>
      </div>
    );
  }

  if (availableTenants.length === 0) {
    return (
      <div className="tenant-selector-container">
        <div className="tenant-selector-card">
          <div className="tenant-selector-error">
            <h2>Nessun Tenant Disponibile</h2>
            <p>Non hai accesso ad alcun tenant. Contatta l'amministratore di sistema.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="tenant-selector-container">
      <div className="tenant-selector-card">
        <div className="tenant-selector-header">
          <h2>Seleziona Database</h2>
          <p>Scegli il database con cui vuoi lavorare</p>
        </div>

        {error && (
          <div className="tenant-selector-alert error">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="tenant-selector-form">
          <div className="tenant-list">
            {availableTenants.map(tenant => (
              <div
                key={tenant.id}
                className={`tenant-option ${selectedTenantId === tenant.id ? 'selected' : ''}`}
                onClick={() => setSelectedTenantId(tenant.id)}
              >
                <div className="tenant-option-radio">
                  <input
                    type="radio"
                    id={`tenant-${tenant.id}`}
                    name="tenant"
                    value={tenant.id}
                    checked={selectedTenantId === tenant.id}
                    onChange={() => setSelectedTenantId(tenant.id)}
                  />
                </div>
                <div className="tenant-option-content">
                  <label htmlFor={`tenant-${tenant.id}`} className="tenant-option-label">
                    <div className="tenant-name">{tenant.nome_display}</div>
                    {tenant.descrizione && (
                      <div className="tenant-description">{tenant.descrizione}</div>
                    )}
                    {tenant.is_default && (
                      <div className="tenant-badge">Predefinito</div>
                    )}
                  </label>
                  {!tenant.is_default && (
                    <button
                      type="button"
                      className="set-default-button"
                      onClick={(e) => handleSetDefault(tenant.id, e)}
                      disabled={settingDefault === tenant.id}
                      title="Imposta come database predefinito"
                    >
                      {settingDefault === tenant.id ? '...' : '⭐'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          <button
            type="submit"
            className="tenant-selector-button"
            disabled={!selectedTenantId || switching}
          >
            {switching ? (
              <>
                <div className="button-spinner"></div>
                Connessione in corso...
              </>
            ) : (
              'Continua'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
