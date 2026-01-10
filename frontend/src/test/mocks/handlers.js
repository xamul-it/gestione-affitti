import { http, HttpResponse } from 'msw'

const API_BASE_URL = 'http://localhost:8000/api/v1'

export const handlers = [
  // Menu endpoint
  http.get(`${API_BASE_URL}/platform/menu/`, () => {
    return HttpResponse.json([
      {
        id: 1,
        label: 'Dashboard',
        path: '/dashboard',
        icon: 'tachometer-alt',
        order_index: 0,
        parent_id: null,
        children: []
      },
      {
        id: 2,
        label: 'Gestione',
        path: null,
        icon: 'folder',
        order_index: 1,
        parent_id: null,
        children: [
          {
            id: 3,
            label: 'Immobili',
            path: '/immobili',
            icon: 'building',
            order_index: 0,
            parent_id: 2,
            children: []
          },
          {
            id: 4,
            label: 'Affittuari',
            path: '/affittuari',
            icon: 'users',
            order_index: 1,
            parent_id: 2,
            children: []
          }
        ]
      }
    ])
  }),

  // Dashboard endpoint
  http.get(`${API_BASE_URL}/platform/dashboard/my-dashboard`, () => {
    return HttpResponse.json({
      layout: [
        { i: 'widget-1', x: 0, y: 0, w: 6, h: 2 },
        { i: 'widget-2', x: 6, y: 0, w: 6, h: 2 },
        { i: 'widget-3', x: 0, y: 2, w: 12, h: 3 }
      ],
      widgets: [
        {
          id: 'widget-1',
          title: 'Contratti Attivi',
          component: 'ContrattiAttiviWidget',
          category: 'affitti',
          description: 'Numero di contratti attualmente attivi'
        },
        {
          id: 'widget-2',
          title: 'Incassi Mensili',
          component: 'IncassiWidget',
          category: 'financial',
          description: 'Totale incassi del mese corrente'
        },
        {
          id: 'widget-3',
          title: 'Scadenze',
          component: 'ScadenzeWidget',
          category: 'alerts',
          description: 'Contratti e certificati in scadenza'
        }
      ]
    })
  }),

  // Login endpoint
  http.post(`${API_BASE_URL}/auth/login`, async ({ request }) => {
    const body = await request.json()
    if (body.username === 'test' && body.password === 'test123') {
      return HttpResponse.json({
        access_token: 'mock-jwt-token-12345',
        token_type: 'bearer'
      })
    }
    return HttpResponse.json(
      { detail: 'Invalid credentials' },
      { status: 401 }
    )
  }),

  // Error scenarios for testing
  http.get(`${API_BASE_URL}/platform/menu/error`, () => {
    return HttpResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    )
  }),

  http.get(`${API_BASE_URL}/platform/dashboard/error`, () => {
    return HttpResponse.json(
      { detail: 'Dashboard not found' },
      { status: 404 }
    )
  }),
]
