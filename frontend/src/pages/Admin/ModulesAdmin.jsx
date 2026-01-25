import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { renderIcon } from '../../components/Navigation/iconRegistry.jsx'
import { useNavigation } from '../../contexts/NavigationContext'
import { loadLocalModuleManifests } from '../../core/modules/localManifests.js'
import './ModulesAdmin.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

function ModulesAdmin() {
  const [modules, setModules] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [toggling, setToggling] = useState({})
  const [registering, setRegistering] = useState({})
  const [reloading, setReloading] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  const [localManifests, setLocalManifests] = useState({})
  const { loadMenu } = useNavigation()

  useEffect(() => {
    loadModules()
    loadLocalModuleManifests().then(setLocalManifests)
  }, [])

  async function withAuthRetry(requestFn) {
    try {
      return await requestFn()
    } catch (err) {
      const status = err.response?.status
      if (status !== 401 && status !== 403) {
        throw err
      }

      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        throw err
      }

      const refreshResponse = await axios.post(
        `${API_BASE_URL}/auth/refresh`,
        { refresh_token: refreshToken }
      )
      const newAccessToken = refreshResponse.data?.access_token
      const newRefreshToken = refreshResponse.data?.refresh_token
      if (newAccessToken) {
        localStorage.setItem('access_token', newAccessToken)
      }
      if (newRefreshToken) {
        localStorage.setItem('refresh_token', newRefreshToken)
      }

      return await requestFn()
    }
  }

  async function loadModules() {
    try {
      const response = await withAuthRetry(() => {
        const token = localStorage.getItem('access_token')
        return axios.get(
          `${API_BASE_URL}/modules/all`,
          {
            headers: { 'Authorization': `Bearer ${token}` }
          }
        )
      })
      setModules(response.data)
      setError(null)
      console.log('✅ Modules loaded:', response.data)
    } catch (err) {
      console.error('❌ Error loading modules:', err)
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  async function toggleModule(technicalName, currentlyEnabled) {
    setToggling(prev => ({ ...prev, [technicalName]: true }))

    try {
      const response = await withAuthRetry(() => {
        const token = localStorage.getItem('access_token')
        return axios.post(
          `${API_BASE_URL}/modules/${technicalName}/toggle`,
          { enabled: !currentlyEnabled },
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        )
      })

      console.log('✅ Module toggled:', response.data)

      // Update local state
      setModules(prevModules =>
        prevModules.map(mod =>
          mod.technical_name === technicalName
            ? { ...mod, enabled: !currentlyEnabled }
            : mod
        )
      )

      // Mark that there are changes to apply
      setHasChanges(true)

    } catch (err) {
      console.error('❌ Error toggling module:', err)
      alert('Errore: ' + (err.response?.data?.detail || err.message))
    } finally {
      setToggling(prev => ({ ...prev, [technicalName]: false }))
    }
  }

  async function applyChanges() {
    setReloading(true)

    try {
      const response = await withAuthRetry(() => {
        const token = localStorage.getItem('access_token')
        return axios.post(
          `${API_BASE_URL}/modules/reload`,
          {},
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        )
      })

      console.log('✅ Server reload initiated:', response.data)
      alert('Ricaricamento server in corso...\n\nLe modifiche saranno applicate tra pochi secondi.')

      // Wait a bit for server to reload, then refresh the page
      setTimeout(() => {
        window.location.reload()
      }, 3000)

    } catch (err) {
      console.error('❌ Error reloading server:', err)
      alert('Errore nel riavvio: ' + (err.response?.data?.detail || err.message))
      setReloading(false)
    }
  }

  async function registerResources(technicalName) {
    setRegistering(prev => ({ ...prev, [technicalName]: true }))

    try {
      const response = await withAuthRetry(() => {
        const token = localStorage.getItem('access_token')
        return axios.post(
          `${API_BASE_URL}/modules/${technicalName}/register-resources`,
          {},
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        )
      })

      const data = response.data || {}
      alert(
        `Registrazione completata per ${technicalName}\n` +
        `Menu: ${data.menu_items_registered ?? 0}\n` +
        `Widget: ${data.widgets_registered ?? 0}\n` +
        `Tenant: ${data.tenants_processed ?? 0}\n` +
        `Tabelle OK: ${data.tables_ok ?? 0}\n` +
        `Errori: ${Array.isArray(data.tables_failed) ? data.tables_failed.length : 0}`
      )
      await loadModules()
      await loadMenu()
    } catch (err) {
      console.error('❌ Error registering module resources:', err)
      alert('Errore registrazione: ' + (err.response?.data?.detail || err.message))
    } finally {
      setRegistering(prev => ({ ...prev, [technicalName]: false }))
    }
  }

  if (loading) {
    return (
      <div className="modules-admin">
        <div className="loading">
          <div className="spinner"></div>
          <p>Caricamento moduli...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="modules-admin">
        <div className="error-container">
          <h2>Errore</h2>
          <p>{error}</p>
          <button onClick={loadModules} className="btn btn-primary">
            Riprova
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="modules-admin">
      <div className="page-header">
        <h1>Gestione Moduli (Piattaforma)</h1>
        <p className="subtitle">
          Visualizzazione moduli installati. Implementazioni future.
        </p>
        <div className="changes-banner">
          <span>Implementazioni future: installazione/rimozione moduli.</span>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button className="btn btn-secondary" disabled>+ Aggiungi Modulo</button>
            <button className="btn btn-secondary" disabled>Rimuovi Modulo</button>
            <button
              className="btn btn-primary"
              onClick={applyChanges}
              disabled={reloading}
            >
              {reloading ? 'Ricaricamento...' : 'Ricarica moduli'}
            </button>
          </div>
        </div>
      </div>

      {modules.length === 0 ? (
        <div className="empty-state">
          <p>Nessun modulo disponibile</p>
        </div>
      ) : (
        <div className="modules-groups">
          {Object.entries(
            [...modules].reduce((acc, module) => {
              const local = localManifests[module.technical_name]
              const category = (local?.category || module.category || 'other').toLowerCase()
              if (!acc[category]) acc[category] = []
              acc[category].push(module)
              return acc
            }, {})
          )
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([category, groupModules]) => (
              <section key={category} className="modules-group">
                <div className="modules-group-header">
                  <h2>{category}</h2>
                  <span className="modules-group-count">{groupModules.length} moduli</span>
                </div>
                <div className="modules-grid">
                  {[...groupModules]
                    .sort((a, b) => (a.name || '').toLowerCase().localeCompare((b.name || '').toLowerCase()))
                    .map(module => {
                      const local = localManifests[module.technical_name]
                      const displayName = local?.displayName || module.name
                      const displayDescription = local?.description || module.description
                      const displayIcon = local?.icon || module.icon
                      return (
                    <div key={module.technical_name} className="module-card">
                      <div className="module-header">
                        <div className="module-info">
                          <div className="module-title">
                            <span className="module-title-icon" aria-hidden="true">
                              {renderIcon(displayIcon || 'package', { size: 20, fallbackClassName: 'module-icon-emoji' })}
                            </span>
                            <h3>{displayName}</h3>
                          </div>
                          <span className="module-version">v{module.version}</span>
                        </div>
                        <div className="module-status">
                          <span className={`status-badge ${module.registered ? 'registered' : 'unregistered'}`}>
                            {module.registered ? 'Registrato' : 'Non registrato'}
                          </span>
                        </div>
                      </div>

                      <div className="module-body">
                        <p className="module-description">
                          {displayDescription || 'Nessuna descrizione disponibile'}
                        </p>

                        {module.author && (
                          <p className="module-author">
                            <strong>Autore:</strong> {module.author}
                          </p>
                        )}

                        <p className="module-tenant-count">
                          <strong>Installato su:</strong> {module.tenant_enabled_count ?? 0} tenant
                        </p>

                        <p className="module-technical-name">
                          <strong>Nome tecnico:</strong> <code>{module.technical_name}</code>
                        </p>

                        <div className="module-dependencies">
                          <strong>Dipendenze:</strong>
                          {module.dependencies && module.dependencies.length > 0 ? (
                            <ul>
                              {module.dependencies.map(dep => (
                                <li key={dep}><code>{dep}</code></li>
                              ))}
                            </ul>
                          ) : (
                            <span className="module-dependencies-empty">Nessuna</span>
                          )}
                        </div>

                        <div className="module-actions">
                          <button
                            className="btn btn-secondary"
                            onClick={() => registerResources(module.technical_name)}
                            disabled={!!registering[module.technical_name]}
                          >
                            {registering[module.technical_name] ? 'Registrazione...' : 'Forza registrazione'}
                          </button>
                        </div>
                      </div>

                      {toggling[module.technical_name] && (
                        <div className="module-loading-overlay">
                          <div className="spinner-small"></div>
                        </div>
                      )}
                    </div>
                      )
                    })}
                </div>
              </section>
            ))}
        </div>
      )}
    </div>
  )
}

export default ModulesAdmin
