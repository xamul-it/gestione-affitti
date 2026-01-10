import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './Dashboard.css'
import { LazyWidgetLoader } from '../core/widgets'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

function Dashboard() {
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showWidgetManager, setShowWidgetManager] = useState(false)
  const [availableWidgets, setAvailableWidgets] = useState([])
  const [loadingWidgets, setLoadingWidgets] = useState(false)
  const [selectedWidgetIds, setSelectedWidgetIds] = useState([])
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    loadDashboard()
  }, [])

  async function loadDashboard() {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(
        `${API_BASE_URL}/platform/dashboard/my-dashboard`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )
      setDashboard(response.data)
      setError(null)
      console.log('✅ Dashboard loaded:', response.data)
    } catch (err) {
      console.error('❌ Error loading dashboard:', err)
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  async function loadAvailableWidgets() {
    try {
      setLoadingWidgets(true)
      const token = localStorage.getItem('access_token')
      const response = await axios.get(
        `${API_BASE_URL}/platform/dashboard/available-widgets`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )
      setAvailableWidgets(response.data)
    } catch (err) {
      console.error('❌ Error loading available widgets:', err)
    } finally {
      setLoadingWidgets(false)
    }
  }

  function toggleWidget(widgetId) {
    setSelectedWidgetIds(prev => {
      const isCurrentlySelected = prev.includes(widgetId)
      const newSelection = isCurrentlySelected
        ? prev.filter(id => id !== widgetId)
        : [...prev, widgetId]

      console.log('🔄 Toggle widget:', {
        widgetId,
        action: isCurrentlySelected ? 'REMOVE' : 'ADD',
        before: prev,
        after: newSelection
      })

      return newSelection
    })
  }

  async function saveWidgetSelection() {
    try {
      setIsSaving(true)
      const token = localStorage.getItem('access_token')

      // Get current widget IDs in dashboard
      const currentWidgetIds = dashboard.layout.map(item => item.i)

      console.log('📊 Current state:', {
        selectedWidgetIds,
        currentWidgetIds,
        selectedCount: selectedWidgetIds.length
      })

      // Calculate widgets to add and remove
      const widgetsToAdd = selectedWidgetIds.filter(id => !currentWidgetIds.includes(id))
      const widgetsToRemove = currentWidgetIds.filter(id => !selectedWidgetIds.includes(id))

      console.log('📋 Changes to apply:', {
        toAdd: widgetsToAdd,
        toRemove: widgetsToRemove
      })

      // Add new widgets
      let addedCount = 0
      for (const widgetId of widgetsToAdd) {
        try {
          console.log(`➕ Adding widget: ${widgetId}`)
          await axios.post(
            `${API_BASE_URL}/platform/dashboard/add-widget`,
            { widget_id: widgetId },
            { headers: { 'Authorization': `Bearer ${token}` } }
          )
          addedCount++
          console.log(`✅ Widget ${widgetId} added successfully`)
        } catch (addErr) {
          console.error(`❌ Failed to add widget ${widgetId}:`, addErr.response?.data || addErr.message)
          throw new Error(`Errore aggiungendo widget ${widgetId}: ${addErr.response?.data?.detail || addErr.message}`)
        }
      }

      // Remove widgets
      let removedCount = 0
      for (const widgetId of widgetsToRemove) {
        try {
          console.log(`➖ Removing widget: ${widgetId}`)
          await axios.delete(
            `${API_BASE_URL}/platform/dashboard/remove-widget/${widgetId}`,
            { headers: { 'Authorization': `Bearer ${token}` } }
          )
          removedCount++
          console.log(`✅ Widget ${widgetId} removed successfully`)
        } catch (removeErr) {
          console.error(`❌ Failed to remove widget ${widgetId}:`, removeErr.response?.data || removeErr.message)
          throw new Error(`Errore rimuovendo widget ${widgetId}: ${removeErr.response?.data?.detail || removeErr.message}`)
        }
      }

      console.log(`✅ Widget selection saved: ${addedCount} added, ${removedCount} removed`)

      // Close modal and reload dashboard
      setShowWidgetManager(false)
      await loadDashboard()
    } catch (err) {
      console.error('❌ Error saving widget selection:', err)
      alert(err.message || err.response?.data?.detail || 'Errore durante il salvataggio')
    } finally {
      setIsSaving(false)
    }
  }

  function openWidgetManager() {
    // Initialize selection with current dashboard widgets
    const currentWidgetIds = dashboard?.layout.map(item => item.i) || []
    console.log('🎯 Opening widget manager:', {
      currentDashboardWidgets: currentWidgetIds
    })
    setSelectedWidgetIds(currentWidgetIds)
    setShowWidgetManager(true)
    loadAvailableWidgets()
  }

  function closeWidgetManager() {
    setShowWidgetManager(false)
    setSelectedWidgetIds([])
  }

  async function removeWidget(widgetId) {
    if (!confirm('Sei sicuro di voler rimuovere questo widget?')) {
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      await axios.delete(
        `${API_BASE_URL}/platform/dashboard/remove-widget/${widgetId}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      )
      console.log('✅ Widget removed:', widgetId)
      await loadDashboard()
    } catch (err) {
      console.error('❌ Error removing widget:', err)
      alert(err.response?.data?.detail || 'Errore durante la rimozione del widget')
    }
  }

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="spinner"></div>
          <span>Caricamento dashboard...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-error">
          <i className="fas fa-exclamation-triangle"></i>
          <h2>Errore caricamento dashboard</h2>
          <p>{error}</p>
          <button onClick={loadDashboard} className="retry-btn">
            <i className="fas fa-redo"></i> Riprova
          </button>
        </div>
      </div>
    )
  }

  if (!dashboard || dashboard.widgets.length === 0) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-empty">
          <i className="fas fa-chart-line"></i>
          <h2>Nessun Widget Disponibile</h2>
          <p>Non ci sono widget configurati per la tua dashboard.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1>
          <i className="fas fa-tachometer-alt"></i>
        </h1>
        <div className="dashboard-actions">
          <button className="btn-add-widget" onClick={openWidgetManager} title="Aggiungi Widget">
            <i className="fas fa-plus"></i> Widget
          </button>
          <button className="btn-refresh" onClick={loadDashboard} title="Aggiorna">
            <i className="fas fa-sync-alt"></i> Aggiorna
          </button>
        </div>
      </div>

      <div className="dashboard-grid">
        {dashboard.layout.map(item => {
          const widget = dashboard.widgets.find(w => w.id === item.i)
          if (!widget) return null

          return (
            <div
              key={item.i}
              className="widget-container"
              style={{
                gridColumn: `span ${item.w}`,
                gridRow: `span ${item.h}`
              }}
            >
              <button
                className="widget-remove-btn"
                onClick={() => removeWidget(item.i)}
                title="Rimuovi widget"
              >
                ×
              </button>
              <div className="widget-body">
                <LazyWidgetLoader
                  componentName={widget.component}
                  onError={(err) => console.error(`Failed to load widget ${widget.component}:`, err)}
                />
              </div>
            </div>
          )
        })}
      </div>

      <div className="dashboard-info">
        <p>
          <i className="fas fa-info-circle"></i>
          Visualizzati {dashboard.layout.length} widget di {dashboard.widgets.length} disponibili
        </p>
      </div>

      {/* Widget Manager Modal */}
      {showWidgetManager && (
        <div className="widget-manager-modal" onClick={closeWidgetManager}>
          <div className="modal-overlay"></div>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>
                <i className="fas fa-puzzle-piece"></i> Gestione Widget
              </h2>
              <button
                className="modal-close-btn"
                onClick={closeWidgetManager}
              >
                <i className="fas fa-times"></i>
              </button>
            </div>

            <div className="modal-body">
              {loadingWidgets ? (
                <div className="modal-loading">
                  <div className="spinner"></div>
                  <span>Caricamento widget...</span>
                </div>
              ) : (
                <>
                  <p className="modal-description">
                    Seleziona i widget da visualizzare nella tua dashboard. Clicca su "Salva" per applicare le modifiche.
                  </p>
                  <div className="available-widgets-grid">
                    {availableWidgets.map(widget => {
                      const isSelected = selectedWidgetIds.includes(widget.id)

                      return (
                        <label
                          key={widget.id}
                          className={`available-widget-card ${isSelected ? 'selected' : ''}`}
                          htmlFor={`widget-${widget.id}`}
                        >
                          <div className="widget-card-checkbox">
                            <input
                              type="checkbox"
                              id={`widget-${widget.id}`}
                              checked={isSelected}
                              onChange={() => toggleWidget(widget.id)}
                            />
                            <div className="checkbox-custom">
                              <i className="fas fa-check"></i>
                            </div>
                          </div>
                          <div className="widget-card-content">
                            <div className="widget-card-header">
                              <h3>{widget.title}</h3>
                            </div>
                            {widget.description && (
                              <p className="widget-card-description">{widget.description}</p>
                            )}
                            <div className="widget-card-meta">
                              <span className="widget-module-badge">{widget.module_id}</span>
                              {widget.category && (
                                <span className="widget-category-badge">{widget.category}</span>
                              )}
                            </div>
                          </div>
                        </label>
                      )
                    })}
                  </div>
                  {availableWidgets.length === 0 && (
                    <div className="no-widgets-message">
                      <i className="fas fa-inbox"></i>
                      <p>Nessun widget disponibile</p>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Modal Footer */}
            {!loadingWidgets && availableWidgets.length > 0 && (
              <div className="modal-footer">
                <div className="modal-footer-info">
                  <span>
                    <i className="fas fa-check-circle"></i> {selectedWidgetIds.length} widget selezionati
                  </span>
                </div>
                <div className="modal-footer-actions">
                  <button
                    className="btn-modal-cancel"
                    onClick={closeWidgetManager}
                    disabled={isSaving}
                  >
                    Annulla
                  </button>
                  <button
                    className="btn-modal-save"
                    onClick={saveWidgetSelection}
                    disabled={isSaving}
                  >
                    {isSaving ? (
                      <>
                        <div className="spinner-small"></div>
                        Salvataggio...
                      </>
                    ) : (
                      <>
                        <i className="fas fa-save"></i> Salva
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
