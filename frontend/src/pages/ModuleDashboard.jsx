import { useParams } from 'react-router-dom';
import ModuleDashboardComponent from '../components/Platform/ModuleDashboard';

/**
 * ModuleDashboard Page - Dashboard specifica per modulo
 *
 * Wrapper per la route /modules/:moduleName/dashboard
 * Usa il componente Platform/ModuleDashboard per mostrare widget modulari
 */
function ModuleDashboard() {
  const { moduleName } = useParams();

  // Map module technical names to display labels
  const moduleLabels = {
    'immobili': 'Immobili',
    'anagrafica_italiana': 'Anagrafica Italiana',
    'affitti_lungo': 'Affitti Lungo Termine',
    'hello_module': 'Hello Module',
  };

  const moduleLabel = moduleLabels[moduleName] || moduleName;

  return (
    <ModuleDashboardComponent
      moduleId={moduleName}
      moduleLabel={moduleLabel}
    />
  );
}

export default ModuleDashboard;
