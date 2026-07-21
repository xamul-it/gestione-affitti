export const manifest = {
  id: 'gestione_pec',
  displayName: 'PEC',
  version: '2026031901',
  description: 'Gestione caselle PEC con audit e notifiche',
  author: 'Modstack',
  category: 'Comunicazioni',
  icon: 'envelope',
  dependencies: [],
  routes: [
    { path: '/pec', component: 'PecInboxPage', label: 'Caselle PEC', icon: 'envelope' },
    { path: '/pec/admin', component: 'PecAdminPage', label: 'Configura PEC', icon: 'cog' },
  ],
  menuItems: [
    {
      id: 'pec.inbox',
      label: 'Caselle PEC',
      path: '/pec',
      icon: '✉️',
      orderIndex: 50,
      requiredPermission: 'pec.read',
    },
    {
      id: 'pec.admin',
      label: 'Configura PEC',
      path: '/pec/admin',
      icon: '⚙️',
      orderIndex: 60,
      requiredPermission: 'pec.admin',
    },
  ],
  widgets: [
    {
      id: 'pec.summary',
      title: 'PEC – Messaggi non letti',
      component: 'PecSummaryWidget',
      defaultWidth: 4,
      defaultHeight: 3,
      category: 'stats',
      requiredPermission: 'pec.read',
    },
  ],
  permissions: ['pec.admin', 'pec.read', 'pec.reply', 'pec.audit.view'],
};

export default manifest;
