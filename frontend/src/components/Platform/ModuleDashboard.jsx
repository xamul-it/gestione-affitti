import React, { useState, useEffect, Suspense } from 'react'
import axios from 'axios'
import {
  AlertTriangle, BarChart3, Check, CheckCircle, ChartLine, Inbox, Plus, Puzzle, RefreshCw, RotateCcw, Save, X,
} from 'lucide-react'
import { LazyWidgetLoader } from '../../core/widgets'
import { Button } from '../UI'
import './ModuleDashboard.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

/**
 * ModuleDashboard - Dashboard specifica per modulo
 *
 * Mostra solo i widget del modulo specificato, con possibilità di aggiungerli/rimuoverli
 *
 * @param {string} moduleId - ID del modulo (es: "immobili", "anagrafica_italiana")
 * @param {string} moduleLabel - Nome visualizzato del modulo (es: "Immobili", "Anagrafiche")
 */
function ModuleDashboard({ moduleId, moduleLabel }) {
  const [widgets, setWidgets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showWidgetSelector, setShowWidgetSelector] = useState(false)
  const [availableWidgets, setAvailableWidgets] = useState([])
  const [selectedWidgetIds, setSelectedWidgetIds] = useState([])

  useEffect(() => {
    loadModuleWidgets()
  }, [moduleId])

  async function loadModuleWidgets() {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')

      // Get all available widgets
      const response = await axios.get(
        `${API_BASE_URL}/platform/dashboard/available-widgets`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      )

      // Filter only widgets from this module
      const moduleWidgets = response.data.filter(w => w.module_id === moduleId)
      setAvailableWidgets(moduleWidgets)

      // Get user's dashboard to see which widgets are active
      const dashboardResponse = await axios.get(
        `${API_BASE_URL}/platform/dashboard/my-dashboard`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      )

      // Filter layout using the widgets registered for this module.
      // Widget ids are not guaranteed to be prefixed with the module id.
      const moduleWidgetIds = new Set(moduleWidgets.map(widget => widget.id))
      const activeModuleWidgetIds = dashboardResponse.data.layout
        .map(item => item.i)
        .filter(id => moduleWidgetIds.has(id))

      // Build widget list with layout info
      const widgetsWithLayout = activeModuleWidgetIds
        .map(widgetId => {
          const widget = moduleWidgets.find(w => w.id === widgetId)
          const layoutItem = dashboardResponse.data.layout.find(l => l.i === widgetId)
          return widget && layoutItem ? { ...widget, layout: layoutItem } : null
        })
        .filter(Boolean)

      setWidgets(widgetsWithLayout)
      setSelectedWidgetIds(activeModuleWidgetIds)
      setError(null)
    } catch (err) {
      console.error('Error loading module widgets:', err)
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  function toggleWidget(widgetId) {
    setSelectedWidgetIds(prev => {
      const isCurrentlySelected = prev.includes(widgetId)
      return isCurrentlySelected
        ? prev.filter(id => id !== widgetId)
        : [...prev, widgetId]
    })
  }

  async function saveWidgetSelection() {
    try {
      const token = localStorage.getItem('access_token')
      const currentWidgetIds = widgets.map(w => w.id)

      // Calculate changes
      const widgetsToAdd = selectedWidgetIds.filter(id => !currentWidgetIds.includes(id))
      const widgetsToRemove = currentWidgetIds.filter(id => !selectedWidgetIds.includes(id))

      // Add new widgets
      for (const widgetId of widgetsToAdd) {
        await axios.post(
          `${API_BASE_URL}/platform/dashboard/add-widget`,
          { widget_id: widgetId },
          { headers: { 'Authorization': `Bearer ${token}` } }
        )
      }

      // Remove widgets
      for (const widgetId of widgetsToRemove) {
        await axios.delete(
          `${API_BASE_URL}/platform/dashboard/remove-widget/${widgetId}`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        )
      }

      // Reload
      setShowWidgetSelector(false)
      await loadModuleWidgets()
    } catch (err) {
      console.error('Error saving widget selection:', err)
      alert(err.message || 'Errore durante il salvataggio')
    }
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
      await loadModuleWidgets()
    } catch (err) {
      console.error('Error removing widget:', err)
      alert(err.response?.data?.detail || 'Errore durante la rimozione')
    }
  }

  useEffect(() => {
    if (!showWidgetSelector) return undefined
    const onKeyDown = (e) => {
      if (e.key === 'Escape') setShowWidgetSelector(false)
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [showWidgetSelector])

  function openWidgetSelector() {
    const currentWidgetIds = widgets.map(w => w.id)
    setSelectedWidgetIds(currentWidgetIds)
    setShowWidgetSelector(true)
  }

  if (loading) {
    return (
      <div className="module-dashboard">
        <div className="dashboard-loading">
          <div className="spinner"></div>
          <span>Caricamento widget...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="module-dashboard">
        <div className="dashboard-error">
          <AlertTriangle size={48} strokeWidth={1.7} className="dashboard-error-icon" aria-hidden="true" />
          <p>{error}</p>
          <Button variant="primary" onClick={loadModuleWidgets}>
            <RotateCcw size={16} strokeWidth={1.7} aria-hidden="true" /> Riprova
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="module-dashboard">
      <div className="module-dashboard-header">
        <h2>
          <ChartLine size={22} strokeWidth={1.7} className="module-dashboard-title-icon" aria-hidden="true" />
          Dashboard {moduleLabel}
        </h2>
        <div className="dashboard-actions">
          <Button variant="secondary" onClick={openWidgetSelector}>
            <Plus size={16} strokeWidth={1.7} aria-hidden="true" /> Widget
          </Button>
          <Button variant="ghost" onClick={loadModuleWidgets}>
            <RefreshCw size={16} strokeWidth={1.7} aria-hidden="true" /> Aggiorna
          </Button>
        </div>
      </div>

      {widgets.length === 0 ? (
        <div className="dashboard-empty">
          <BarChart3 size={48} strokeWidth={1.7} className="dashboard-empty-icon" aria-hidden="true" />
          <h3>Nessun Widget Attivo</h3>
          <p>Clicca su "Widget" per aggiungere widget alla tua dashboard {moduleLabel}</p>
          <Button variant="primary" onClick={openWidgetSelector}>
            <Plus size={16} strokeWidth={1.7} aria-hidden="true" /> Aggiungi Widget
          </Button>
        </div>
      ) : (
        <div className="module-dashboard-grid">
          {widgets.map(widget => (
            <div
              key={widget.id}
              className="widget-container"
              style={{
                gridColumn: `span ${widget.layout.w}`,
                gridRow: `span ${widget.layout.h}`
              }}
            >
              <button
                className="widget-remove-btn"
                onClick={() => removeWidget(widget.id)}
                title="Rimuovi widget"
                aria-label="Rimuovi widget"
              >
                <X size={16} strokeWidth={2} aria-hidden="true" />
              </button>
              <div className="widget-body">
                <Suspense fallback={
                  <div className="widget-loading">
                    <div className="spinner"></div>
                    <span>Caricamento...</span>
                  </div>
                }>
                  <LazyWidgetLoader
                    componentName={widget.component}
                    onError={(err) => console.error(`Widget ${widget.id} error:`, err)}
                  />
                </Suspense>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Widget Selector Modal */}
      {showWidgetSelector && (
        <div className="widget-manager-modal" onClick={() => setShowWidgetSelector(false)}>
          <div
            className="modal-content"
            role="dialog"
            aria-modal="true"
            aria-labelledby="module-dashboard-widget-dialog-title"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h2 id="module-dashboard-widget-dialog-title">
                <Puzzle size={20} strokeWidth={1.7} className="modal-title-icon" aria-hidden="true" /> Widget {moduleLabel}
              </h2>
              <button
                className="modal-close-btn"
                onClick={() => setShowWidgetSelector(false)}
                aria-label="Chiudi"
              >
                <X size={18} strokeWidth={1.7} aria-hidden="true" />
              </button>
            </div>

            <div className="modal-body">
              <p className="modal-description">
                Seleziona i widget da visualizzare nella dashboard {moduleLabel}.
              </p>

              {availableWidgets.length === 0 ? (
                <div className="no-widgets-message">
                  <Inbox size={40} strokeWidth={1.7} aria-hidden="true" />
                  <p>Nessun widget disponibile per questo modulo</p>
                </div>
              ) : (
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
                            <Check size={14} strokeWidth={2.5} aria-hidden="true" />
                          </div>
                        </div>
                        <div className="widget-card-content">
                          <div className="widget-card-header">
                            <h3>{widget.title}</h3>
                          </div>
                          {widget.description && (
                            <p className="widget-card-description">{widget.description}</p>
                          )}
                          {widget.category && (
                            <div className="widget-card-meta">
                              <span className="widget-category-badge">{widget.category}</span>
                            </div>
                          )}
                        </div>
                      </label>
                    )
                  })}
                </div>
              )}
            </div>

            {availableWidgets.length > 0 && (
              <div className="modal-footer">
                <div className="modal-footer-info">
                  <span>
                    <CheckCircle size={16} strokeWidth={1.7} aria-hidden="true" /> {selectedWidgetIds.length} widget selezionati
                  </span>
                </div>
                <div className="modal-footer-actions">
                  <Button variant="secondary" onClick={() => setShowWidgetSelector(false)}>
                    Annulla
                  </Button>
                  <Button variant="primary" onClick={saveWidgetSelection}>
                    <Save size={16} strokeWidth={1.7} aria-hidden="true" /> Salva
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default ModuleDashboard
