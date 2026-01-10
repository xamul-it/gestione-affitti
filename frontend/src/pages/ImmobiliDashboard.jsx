import React from 'react'
import ModuleDashboard from '../components/Platform/ModuleDashboard'

/**
 * Dashboard specifica per il modulo Immobili
 *
 * Mostra solo i widget relativi a immobili, condomini, certificati energetici, etc.
 */
function ImmobiliDashboard() {
  return (
    <ModuleDashboard
      moduleId="immobili"
      moduleLabel="Immobili"
    />
  )
}

export default ImmobiliDashboard
