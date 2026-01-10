import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Dashboard from './Dashboard'
import { server } from '../test/mocks/server'
import { http, HttpResponse } from 'msw'

describe('Dashboard Component', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('Loading State', () => {
    it('should display loading spinner initially', () => {
      localStorage.setItem('access_token', 'test-token')
      render(<Dashboard />)

      expect(screen.getByText(/caricamento dashboard/i)).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should display error message when API fails', async () => {
      localStorage.setItem('access_token', 'test-token')

      server.use(
        http.get('http://localhost:8000/api/v1/platform/dashboard/my-dashboard', () => {
          return HttpResponse.json(
            { detail: 'Dashboard not found' },
            { status: 404 }
          )
        })
      )

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/errore caricamento dashboard/i)).toBeInTheDocument()
        expect(screen.getByText(/dashboard not found/i)).toBeInTheDocument()
      })
    })

    it('should have retry button that reloads dashboard', async () => {
      const user = userEvent.setup()
      localStorage.setItem('access_token', 'test-token')

      // First call fails
      server.use(
        http.get('http://localhost:8000/api/v1/platform/dashboard/my-dashboard', () => {
          return HttpResponse.json(
            { detail: 'Error' },
            { status: 500 }
          )
        })
      )

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/errore caricamento dashboard/i)).toBeInTheDocument()
      })

      // Reset to successful response
      server.resetHandlers()

      const retryButton = screen.getByRole('button', { name: /riprova/i })
      await user.click(retryButton)

      await waitFor(() => {
        expect(screen.getByText(/contratti attivi/i)).toBeInTheDocument()
      })
    })
  })

  describe('Empty State', () => {
    it('should display empty message when no widgets', async () => {
      localStorage.setItem('access_token', 'test-token')

      server.use(
        http.get('http://localhost:8000/api/v1/platform/dashboard/my-dashboard', () => {
          return HttpResponse.json({
            layout: [],
            widgets: []
          })
        })
      )

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/nessun widget disponibile/i)).toBeInTheDocument()
        expect(screen.getByText(/non ci sono widget configurati/i)).toBeInTheDocument()
      })
    })
  })

  describe('Dashboard Rendering', () => {
    it('should render dashboard header with title', async () => {
      localStorage.setItem('access_token', 'test-token')

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument()
      })
    })

    it('should render refresh button', async () => {
      localStorage.setItem('access_token', 'test-token')

      render(<Dashboard />)

      await waitFor(() => {
        const refreshButton = screen.getByRole('button', { name: /aggiorna/i })
        expect(refreshButton).toBeInTheDocument()
      })
    })

    it('should render all widgets from API', async () => {
      localStorage.setItem('access_token', 'test-token')

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('Contratti Attivi')).toBeInTheDocument()
        expect(screen.getByText('Incassi Mensili')).toBeInTheDocument()
        expect(screen.getByText('Scadenze')).toBeInTheDocument()
      })
    })

    it('should display widget component names', async () => {
      localStorage.setItem('access_token', 'test-token')

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('ContrattiAttiviWidget')).toBeInTheDocument()
        expect(screen.getByText('IncassiWidget')).toBeInTheDocument()
        expect(screen.getByText('ScadenzeWidget')).toBeInTheDocument()
      })
    })

    it('should display widget descriptions', async () => {
      localStorage.setItem('access_token', 'test-token')

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/numero di contratti attualmente attivi/i)).toBeInTheDocument()
        expect(screen.getByText(/totale incassi del mese corrente/i)).toBeInTheDocument()
        expect(screen.getByText(/contratti e certificati in scadenza/i)).toBeInTheDocument()
      })
    })

    it('should display widget categories', async () => {
      localStorage.setItem('access_token', 'test-token')

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('affitti')).toBeInTheDocument()
        expect(screen.getByText('financial')).toBeInTheDocument()
        expect(screen.getByText('alerts')).toBeInTheDocument()
      })
    })
  })

  describe('Widget Layout', () => {
    it('should apply grid layout based on widget configuration', async () => {
      localStorage.setItem('access_token', 'test-token')

      render(<Dashboard />)

      await waitFor(() => {
        const widgets = screen.getAllByRole('heading', { level: 3 })
        expect(widgets.length).toBeGreaterThan(0)
      })

      // Check that widgets have grid styling
      const widgetContainers = document.querySelectorAll('.widget-container')
      expect(widgetContainers.length).toBe(3)

      // First widget should span 6 columns
      expect(widgetContainers[0]).toHaveStyle({ gridColumn: 'span 6' })
      // Second widget should span 6 columns
      expect(widgetContainers[1]).toHaveStyle({ gridColumn: 'span 6' })
      // Third widget should span 12 columns
      expect(widgetContainers[2]).toHaveStyle({ gridColumn: 'span 12' })
    })
  })

  describe('Dashboard Info', () => {
    it('should display widget count information', async () => {
      localStorage.setItem('access_token', 'test-token')

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText(/visualizzati 3 widget di 3 disponibili/i)).toBeInTheDocument()
      })
    })
  })

  describe('Refresh Functionality', () => {
    it('should reload dashboard data when refresh button is clicked', async () => {
      const user = userEvent.setup()
      localStorage.setItem('access_token', 'test-token')

      let requestCount = 0

      server.use(
        http.get('http://localhost:8000/api/v1/platform/dashboard/my-dashboard', () => {
          requestCount++
          return HttpResponse.json({
            layout: [{ i: 'widget-1', x: 0, y: 0, w: 12, h: 2 }],
            widgets: [{
              id: 'widget-1',
              title: `Widget Request ${requestCount}`,
              component: 'TestWidget',
              category: 'test'
            }]
          })
        })
      )

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('Widget Request 1')).toBeInTheDocument()
      })

      const refreshButton = screen.getByRole('button', { name: /aggiorna/i })
      await user.click(refreshButton)

      await waitFor(() => {
        expect(screen.getByText('Widget Request 2')).toBeInTheDocument()
      })

      expect(requestCount).toBe(2)
    })
  })

  describe('Authorization', () => {
    it('should send authorization header with token', async () => {
      const token = 'test-dashboard-token'
      localStorage.setItem('access_token', token)

      let requestHeaders = null

      server.use(
        http.get('http://localhost:8000/api/v1/platform/dashboard/my-dashboard', ({ request }) => {
          requestHeaders = Object.fromEntries(request.headers.entries())
          return HttpResponse.json({ layout: [], widgets: [] })
        })
      )

      render(<Dashboard />)

      await waitFor(() => {
        expect(requestHeaders).toBeTruthy()
        expect(requestHeaders.authorization).toBe(`Bearer ${token}`)
      })
    })
  })

  describe('Widget Filtering', () => {
    it('should only render widgets that exist in layout', async () => {
      localStorage.setItem('access_token', 'test-token')

      server.use(
        http.get('http://localhost:8000/api/v1/platform/dashboard/my-dashboard', () => {
          return HttpResponse.json({
            layout: [
              { i: 'widget-1', x: 0, y: 0, w: 6, h: 2 },
              // widget-3 is in widgets array but not in layout
            ],
            widgets: [
              {
                id: 'widget-1',
                title: 'Visible Widget',
                component: 'VisibleWidget',
                category: 'test'
              },
              {
                id: 'widget-3',
                title: 'Hidden Widget',
                component: 'HiddenWidget',
                category: 'test'
              }
            ]
          })
        })
      )

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByText('Visible Widget')).toBeInTheDocument()
        expect(screen.queryByText('Hidden Widget')).not.toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', async () => {
      localStorage.setItem('access_token', 'test-token')

      render(<Dashboard />)

      await waitFor(() => {
        const h1 = screen.getByRole('heading', { level: 1, name: /dashboard/i })
        expect(h1).toBeInTheDocument()

        const h3s = screen.getAllByRole('heading', { level: 3 })
        expect(h3s.length).toBe(3)
      })
    })

    it('should have descriptive button labels', async () => {
      localStorage.setItem('access_token', 'test-token')

      render(<Dashboard />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /aggiorna/i })).toBeInTheDocument()
      })
    })
  })
})
