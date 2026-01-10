import React, { useState, useEffect } from 'react'
import widgetRegistry from './WidgetComponentRegistry'

/**
 * LazyWidgetLoader
 *
 * Dynamically loads widget components from the registry.
 * Handles loading states, errors, and lazy component resolution.
 *
 * @param {string} componentName - Name of widget component to load
 * @param {Function} onError - Optional error callback
 * @param {Object} props - Props to pass to the loaded widget component
 */
function LazyWidgetLoader({ componentName, onError, ...props }) {
  const [WidgetComponent, setWidgetComponent] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let mounted = true

    async function loadWidget() {
      try {
        setLoading(true)
        setError(null)

        const Component = await widgetRegistry.getComponent(componentName)

        if (mounted) {
          setWidgetComponent(() => Component)
          setLoading(false)
        }
      } catch (err) {
        console.error(`[LazyWidgetLoader] Error loading ${componentName}:`, err)

        if (mounted) {
          setError(err.message)
          setLoading(false)
          onError?.(err)
        }
      }
    }

    loadWidget()

    return () => {
      mounted = false
    }
  }, [componentName, onError])

  // Loading state
  if (loading) {
    return (
      <div className="widget-loading">
        <div className="spinner"></div>
        <span>Caricamento widget...</span>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="widget-placeholder">
        <i className="fas fa-exclamation-triangle"></i>
        <p><strong>{componentName}</strong></p>
        <p className="widget-error">Errore: {error}</p>
      </div>
    )
  }

  // Success - render the loaded component
  if (WidgetComponent) {
    return <WidgetComponent {...props} />
  }

  // Should not reach here
  return null
}

export default LazyWidgetLoader
