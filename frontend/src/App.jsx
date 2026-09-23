import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import TopBar from './components/Layout/TopBar';
import Sidebar from './components/Navigation/Sidebar';
import Drawer from './components/Navigation/Drawer';
import ModuleSelector from './pages/ModuleSelector';
import ModuleDashboard from './pages/ModuleDashboard';
import Home from './pages/Home';  // Old home - keeping for now
import Dashboard from './pages/Dashboard';
import ImmobiliDashboard from './pages/ImmobiliDashboard';
import AnagraficaDashboard from './pages/AnagraficaDashboard';
import LoginPage from './pages/LoginPage';
import UsersManagement from './pages/UsersManagement';
import Settings from './pages/Settings';
import ScadenzeTestPage from './pages/ScadenzeTestPage';
import ScadenzaResolve from './pages/ScadenzaResolve';
import AnagraficaScadenzaResolve from './pages/AnagraficaScadenzaResolve';
import ImmobiliHome from './pages/ImmobiliHome';
// Immobili module components
import {
  UnitaImmobiliariList,
  TerreniList,
  CertificatiEnergeticiList,
  ProprietariList,
  CondominList,
  ConduttoriList,
  TabelleMillesimaliList,
  MillesimiImmobileList,
  CategorieCatastaliList,
  TipologieTerrenoList
} from './modules/immobili';

import ImmobileDetail from './pages/ImmobileDetail';
import { TenantSelector } from './components/Tenant/TenantSelector';

// Affitti Lungo module components
import {
  AffittuariList,
  ContrattiList,
  SpeseList,
  IncassiList,
  TecniciList
} from './modules/affitti_lungo';

// Anagrafica Italiana module components
import {
  SoggettiAnagraficiList,
  SoggettoDetail,
  SoggettoNew,
  PersoneFisicheList,
  PersonaFisicaForm,
  PersonaFisicaDetail,
  PersoneGiuridicheList,
  PersonaGiuridicaForm,
  PersonaGiuridicaDetail,
  ComuniList,
  TipiDocumentoList,
  StatiDocumentoList,
  RuoliAziendaTipiList,
  RuoliAziendaList
} from './modules/anagrafica_italiana';

import AffittuarioDetail from './pages/AffittuarioDetail';
import ContrattoDetail from './pages/ContrattoDetail';
import ModulesAdmin from './pages/Admin/ModulesAdmin';
import DataAdmin from './pages/Admin/DataAdmin';
import DatabaseManagement from './pages/Admin/DatabaseManagement';
import TenantModules from './pages/Tenant/TenantModules';
import RolesPermissionsDebug from './pages/Admin/RolesPermissionsDebug';
import DocumentParsingDebug from './pages/Admin/DocumentParsingDebug';
import ParsingServices from './pages/Admin/ParsingServices';
import TenantMaintenance from './pages/Admin/TenantMaintenance';
import CoreCleanup from './pages/Admin/CoreCleanup';
import StyleGuide from './pages/Admin/StyleGuide';

// Auth
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ProtectedRoute from './components/Auth/ProtectedRoute';

// Tenant
import { TenantProvider } from './contexts/TenantContext';

// Navigation
import { NavigationProvider } from './contexts/NavigationContext';

// Module system imports
import { useModuleLoader } from './core/modules/useModuleLoader';
import { getDynamicRouteComponents, registerModuleComponent } from './core/modules/DynamicRoutes';

// Register module components
import HelloPage from './modules/hello_module/HelloPage';
registerModuleComponent('@modules/hello_module/HelloPage', HelloPage);

// Gestione PEC module
import {
  PecInboxPage,
  PecAdminPage,
  PecSummaryWidget,
} from './modules/gestione_pec';
registerModuleComponent('PecSummaryWidget', PecSummaryWidget);

// Affitti Brevi module components (dynamic routes)
import {
  CalendarioMultiPiattaforma,
  PrenotazioniList,
  CalendariList,
  TassaConfigList
} from './modules/affitti_brevi';
registerModuleComponent('CalendarioMultiPiattaforma', CalendarioMultiPiattaforma);
registerModuleComponent('PrenotazioniList', PrenotazioniList);
registerModuleComponent('CalendariList', CalendariList);
registerModuleComponent('TassaConfigList', TassaConfigList);

registerModuleComponent('TipologieTerrenoList', TipologieTerrenoList);

// Esempio Componenti module components
import { ElementiEsempioList } from './modules/esempio_componenti';
registerModuleComponent('ElementiEsempioList', ElementiEsempioList);

// Layout wrapper component with new navigation system
function AppLayout({ children }) {
  const { isAuthenticated } = useAuth();

  return (
    <div className="app-layout">
      {/* TopBar is always visible */}
      <TopBar />

      {/* Sidebar (desktop ≥768px) - only when authenticated */}
      {isAuthenticated && <Sidebar />}

      {/* Drawer (mobile <768px) - only when authenticated */}
      {isAuthenticated && <Drawer />}

      {/* Main content area */}
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}

function App() {
  const { loading: modulesLoading, error: modulesError, modules } = useModuleLoader();

  // Auth system v2.0 - Fixed AuthProvider wrapper
  return (
    <Router>
      <div className="app">
        {/* UX Quick Fix #2: Skip to content link for keyboard navigation */}
        <a href="#main-content" className="skip-link">
          Vai al contenuto principale
        </a>

        <AuthProvider>
          <TenantProvider>
            <NavigationProvider>
              <AppLayout>
            <div className="container" id="main-content">
              {modulesLoading && (
                <div style={{ padding: '20px', textAlign: 'center', backgroundColor: '#f0f0f0' }}>
                  <p>Caricamento moduli in corso...</p>
                </div>
              )}

              {modulesError && (
                <div style={{ padding: '20px', color: 'red', backgroundColor: '#ffe0e0', textAlign: 'center' }}>
                  <p>⚠️ Errore caricamento moduli: {modulesError}</p>
                  <p style={{ fontSize: '12px' }}>L'applicazione continuerà a funzionare senza moduli dinamici.</p>
                </div>
              )}

              <Routes>
                {/* Public routes */}
                <Route path="/login" element={<LoginPage />} />

                {/* Tenant selection - requires auth but not tenant */}
                <Route path="/tenant-select" element={<ProtectedRoute requireTenant={false}><TenantSelector /></ProtectedRoute>} />

                {/* Protected routes */}
                <Route path="/" element={<ProtectedRoute><ModuleSelector /></ProtectedRoute>} />
                <Route path="/modules/:moduleName/dashboard" element={<ProtectedRoute><ModuleDashboard /></ProtectedRoute>} />
                <Route path="/old-home" element={<ProtectedRoute><Home /></ProtectedRoute>} />
                <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                <Route path="/admin/users" element={<ProtectedRoute requiredRole="Admin"><UsersManagement /></ProtectedRoute>} />
                <Route path="/admin/roles-debug" element={<ProtectedRoute requiredRole="Admin"><RolesPermissionsDebug /></ProtectedRoute>} />
                <Route path="/admin/document-parsing-debug" element={<ProtectedRoute requiredRole="Admin"><DocumentParsingDebug /></ProtectedRoute>} />
                <Route path="/admin/parsing-services" element={<ProtectedRoute requiredRole="Admin"><ParsingServices /></ProtectedRoute>} />
                <Route path="/admin/tenant-maintenance" element={<ProtectedRoute requiredRole="Admin"><TenantMaintenance /></ProtectedRoute>} />
                <Route path="/admin/core-cleanup" element={<ProtectedRoute requiredRole="Admin"><CoreCleanup /></ProtectedRoute>} />
                <Route path="/admin/style-guide" element={<ProtectedRoute requiredRole="Admin"><StyleGuide /></ProtectedRoute>} />
                <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />

                {/* Scadenze Test Page */}
                <Route path="/test/scadenze" element={<ProtectedRoute><ScadenzeTestPage /></ProtectedRoute>} />
                <Route path="/scadenze/resolve" element={<ProtectedRoute><ScadenzaResolve /></ProtectedRoute>} />
                <Route path="/anagrafiche/scadenze/resolve" element={<ProtectedRoute><AnagraficaScadenzaResolve /></ProtectedRoute>} />

                {/* Anagrafica routes */}
                <Route path="/anagrafiche" element={<ProtectedRoute><AnagraficaDashboard /></ProtectedRoute>} />
                <Route path="/anagrafiche/lista" element={<ProtectedRoute><SoggettiAnagraficiList /></ProtectedRoute>} />
                <Route path="/anagrafiche/nuovo" element={<ProtectedRoute><SoggettoNew /></ProtectedRoute>} />

                {/* Persone Fisiche routes - SPECIFICHE PRIMA */}
                <Route path="/anagrafiche/persone-fisiche" element={<ProtectedRoute><PersoneFisicheList /></ProtectedRoute>} />
                <Route path="/anagrafiche/persone-fisiche/nuovo" element={<ProtectedRoute><PersonaFisicaForm /></ProtectedRoute>} />
                <Route path="/anagrafiche/persone-fisiche/:id/modifica" element={<ProtectedRoute><PersonaFisicaForm /></ProtectedRoute>} />
                <Route path="/anagrafiche/persone-fisiche/:id" element={<ProtectedRoute><PersonaFisicaDetail /></ProtectedRoute>} />

                {/* Persone Giuridiche routes - SPECIFICHE PRIMA */}
                <Route path="/anagrafiche/persone-giuridiche" element={<ProtectedRoute><PersoneGiuridicheList /></ProtectedRoute>} />
                <Route path="/anagrafiche/persone-giuridiche/nuovo" element={<ProtectedRoute><PersonaGiuridicaForm /></ProtectedRoute>} />
                <Route path="/anagrafiche/persone-giuridiche/:id/modifica" element={<ProtectedRoute><PersonaGiuridicaForm /></ProtectedRoute>} />
                <Route path="/anagrafiche/persone-giuridiche/:id" element={<ProtectedRoute><PersonaGiuridicaDetail /></ProtectedRoute>} />

                {/* Comuni route - Dati di riferimento */}
                <Route path="/anagrafiche/comuni" element={<ProtectedRoute><ComuniList /></ProtectedRoute>} />

                {/* Tipi Documento - Dati di dominio */}
                <Route path="/anagrafiche/domini/tipi-documento" element={<ProtectedRoute><TipiDocumentoList /></ProtectedRoute>} />

                {/* Stati Documento - Dati di dominio */}
                <Route path="/anagrafiche/domini/stati-documento" element={<ProtectedRoute><StatiDocumentoList /></ProtectedRoute>} />

                {/* Ruoli Azienda - Dati di dominio */}
                <Route path="/anagrafiche/domini/ruoli-azienda" element={<ProtectedRoute><RuoliAziendaTipiList /></ProtectedRoute>} />

                {/* Ruoli Azienda - Associazioni */}
                <Route path="/anagrafiche/ruoli-azienda" element={<ProtectedRoute><RuoliAziendaList /></ProtectedRoute>} />

                {/* Fallback generico per anagrafiche */}
                <Route path="/anagrafiche/:id" element={<ProtectedRoute><SoggettoDetail /></ProtectedRoute>} />

                {/* Immobili routes */}
                <Route path="/immobili" element={<ProtectedRoute><ImmobiliDashboard /></ProtectedRoute>} />
                <Route path="/immobili/home" element={<ProtectedRoute><ImmobiliHome /></ProtectedRoute>} />
                <Route path="/unita-immobiliari" element={<ProtectedRoute><UnitaImmobiliariList /></ProtectedRoute>} />
                <Route path="/unita-immobiliari/:id" element={<ProtectedRoute><ImmobileDetail /></ProtectedRoute>} />
                <Route path="/terreni" element={<ProtectedRoute><TerreniList /></ProtectedRoute>} />
                <Route path="/affittuari" element={<ProtectedRoute><AffittuariList /></ProtectedRoute>} />
                <Route path="/affittuari/:id" element={<ProtectedRoute><AffittuarioDetail /></ProtectedRoute>} />
                <Route path="/contratti" element={<ProtectedRoute><ContrattiList /></ProtectedRoute>} />
                <Route path="/contratti/:id" element={<ProtectedRoute><ContrattoDetail /></ProtectedRoute>} />
                <Route path="/spese" element={<ProtectedRoute><SpeseList /></ProtectedRoute>} />
                <Route path="/incassi" element={<ProtectedRoute><IncassiList /></ProtectedRoute>} />
                <Route path="/tecnici" element={<ProtectedRoute><TecniciList /></ProtectedRoute>} />
                <Route path="/certificati-energetici" element={<ProtectedRoute><CertificatiEnergeticiList /></ProtectedRoute>} />
                <Route path="/proprietari" element={<ProtectedRoute><ProprietariList /></ProtectedRoute>} />
                <Route path="/condomini" element={<ProtectedRoute><CondominList /></ProtectedRoute>} />
                <Route path="/conduttori" element={<ProtectedRoute><ConduttoriList /></ProtectedRoute>} />
                <Route path="/tabelle-millesimali" element={<ProtectedRoute><TabelleMillesimaliList /></ProtectedRoute>} />
                <Route path="/millesimi-immobile" element={<ProtectedRoute><MillesimiImmobileList /></ProtectedRoute>} />
                <Route path="/categorie-catastali" element={<ProtectedRoute requiredRole="Admin"><CategorieCatastaliList /></ProtectedRoute>} />
                <Route path="/admin/modules" element={<ProtectedRoute requiredPermission="platform.admin"><ModulesAdmin /></ProtectedRoute>} />
                <Route path="/admin/data" element={<ProtectedRoute requiredRole="Admin"><DataAdmin /></ProtectedRoute>} />
                <Route path="/admin/database" element={<ProtectedRoute requiredRole="Admin"><DatabaseManagement /></ProtectedRoute>} />
                <Route path="/modules" element={<ProtectedRoute requiredRole="Admin"><ModulesAdmin /></ProtectedRoute>} />
                <Route path="/tenant/modules" element={<ProtectedRoute requiredPermission="tenant.admin"><TenantModules /></ProtectedRoute>} />

                {/* PEC routes */}
                <Route path="/pec" element={<ProtectedRoute requiredPermission="pec.read"><PecInboxPage /></ProtectedRoute>} />
                <Route path="/pec/admin" element={<ProtectedRoute requiredPermission="pec.admin"><PecAdminPage /></ProtectedRoute>} />

                {/* Esempio Componenti routes - Demo module */}
                <Route path="/esempio/elementi" element={<ProtectedRoute><ElementiEsempioList /></ProtectedRoute>} />

                {/* Dynamic module routes */}
                {!modulesLoading && getDynamicRouteComponents()}
              </Routes>
            </div>
              </AppLayout>
            </NavigationProvider>
          </TenantProvider>
        </AuthProvider>
      </div>
    </Router>
  );
}

export default App;
