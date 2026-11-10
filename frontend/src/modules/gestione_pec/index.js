import { widgetRegistry } from '../../core/widgets';

// Dashboard widget: registered like the other modules' widgets so the
// dashboard can load it by name.
widgetRegistry.registerWidget(
  'PecSummaryWidget',
  'gestione_pec',
  () => import('./widgets/PecSummaryWidget')
);

export { default as PecInboxPage } from './pages/PecInboxPage';
export { default as PecAdminPage } from './pages/PecAdminPage';
export { default as PecSummaryWidget } from './widgets/PecSummaryWidget';
export { manifest } from './manifest';
