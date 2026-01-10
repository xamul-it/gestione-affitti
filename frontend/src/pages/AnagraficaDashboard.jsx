import React from 'react'
import ModuleDashboard from '../components/Platform/ModuleDashboard'

/**
 * Dashboard specifica per il modulo Anagrafica Italiana
 *
 * Mostra solo i widget relativi alle anagrafiche (persone fisiche e giuridiche)
 */
function AnagraficaDashboard() {
  return (
    <ModuleDashboard
      moduleId="anagrafica_italiana"
      moduleLabel="Anagrafiche"
    />
  )
}

export default AnagraficaDashboard
