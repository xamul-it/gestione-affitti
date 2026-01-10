import { test, expect } from '@playwright/test'

/**
 * E2E Test Suite: Authentication and Navigation Flow
 *
 * This test suite covers the critical user journey:
 * 1. Login with credentials
 * 2. Navigate using dynamic menu
 * 3. View dashboard with widgets
 * 4. Verify protected routes
 */

test.describe('Authentication and Navigation Flow', () => {

  test.beforeEach(async ({ page }) => {
    // Clear any existing auth state
    await page.context().clearCookies()
    await page.evaluate(() => localStorage.clear())
  })

  test('should show login page when not authenticated', async ({ page }) => {
    await page.goto('/')

    // Should redirect to login or show login form
    await expect(page).toHaveURL(/login/)
    await expect(page.getByRole('heading', { name: /login/i })).toBeVisible()
  })

  test('should successfully login with valid credentials', async ({ page }) => {
    // Mock the backend API responses
    await page.route('**/api/v1/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'test-jwt-token',
          token_type: 'bearer'
        })
      })
    })

    await page.route('**/api/v1/platform/menu/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            label: 'Dashboard',
            path: '/dashboard',
            icon: 'tachometer-alt',
            order_index: 0,
            children: []
          },
          {
            id: 2,
            label: 'Gestione',
            path: null,
            icon: 'folder',
            order_index: 1,
            children: [
              {
                id: 3,
                label: 'Immobili',
                path: '/immobili',
                icon: 'building',
                order_index: 0,
                children: []
              }
            ]
          }
        ])
      })
    })

    await page.route('**/api/v1/platform/dashboard/my-dashboard', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          layout: [
            { i: 'widget-1', x: 0, y: 0, w: 6, h: 2 }
          ],
          widgets: [
            {
              id: 'widget-1',
              title: 'Test Widget',
              component: 'TestWidget',
              category: 'test',
              description: 'This is a test widget'
            }
          ]
        })
      })
    })

    await page.goto('/login')

    // Fill login form
    await page.getByLabel(/username|email/i).fill('test@example.com')
    await page.getByLabel(/password/i).fill('password123')

    // Submit form
    await page.getByRole('button', { name: /login|accedi/i }).click()

    // Should redirect to dashboard after successful login
    await expect(page).toHaveURL(/dashboard/, { timeout: 5000 })
  })

  test('should show error message with invalid credentials', async ({ page }) => {
    await page.route('**/api/v1/auth/login', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Invalid credentials'
        })
      })
    })

    await page.goto('/login')

    await page.getByLabel(/username|email/i).fill('wrong@example.com')
    await page.getByLabel(/password/i).fill('wrongpassword')
    await page.getByRole('button', { name: /login|accedi/i }).click()

    // Should show error message
    await expect(page.getByText(/invalid|errore|credenziali/i)).toBeVisible()
  })

  test('complete user journey: login -> menu navigation -> dashboard', async ({ page }) => {
    // Setup API mocks
    await page.route('**/api/v1/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'test-jwt-token',
          token_type: 'bearer'
        })
      })
    })

    await page.route('**/api/v1/platform/menu/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            label: 'Dashboard',
            path: '/dashboard',
            icon: 'tachometer-alt',
            order_index: 0,
            children: []
          },
          {
            id: 2,
            label: 'Gestione',
            path: null,
            icon: 'folder',
            order_index: 1,
            children: [
              {
                id: 3,
                label: 'Immobili',
                path: '/immobili',
                icon: 'building',
                order_index: 0,
                children: []
              },
              {
                id: 4,
                label: 'Affittuari',
                path: '/affittuari',
                icon: 'users',
                order_index: 1,
                children: []
              }
            ]
          }
        ])
      })
    })

    await page.route('**/api/v1/platform/dashboard/my-dashboard', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          layout: [
            { i: 'widget-1', x: 0, y: 0, w: 6, h: 2 },
            { i: 'widget-2', x: 6, y: 0, w: 6, h: 2 }
          ],
          widgets: [
            {
              id: 'widget-1',
              title: 'Contratti Attivi',
              component: 'ContrattiWidget',
              category: 'affitti',
              description: 'Visualizza contratti attivi'
            },
            {
              id: 'widget-2',
              title: 'Incassi Mensili',
              component: 'IncassiWidget',
              category: 'financial',
              description: 'Totale incassi del mese'
            }
          ]
        })
      })
    })

    // Step 1: Login
    await page.goto('/login')
    await page.getByLabel(/username|email/i).fill('test@example.com')
    await page.getByLabel(/password/i).fill('password123')
    await page.getByRole('button', { name: /login|accedi/i }).click()

    // Step 2: Verify dashboard is loaded
    await expect(page).toHaveURL(/dashboard/)
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible()

    // Step 3: Verify dashboard widgets are displayed
    await expect(page.getByText('Contratti Attivi')).toBeVisible()
    await expect(page.getByText('Incassi Mensili')).toBeVisible()

    // Step 4: Verify menu is loaded
    await expect(page.getByText('Dashboard')).toBeVisible()
    await expect(page.getByText('Gestione')).toBeVisible()

    // Step 5: Expand submenu
    await page.getByText('Gestione').click()
    await expect(page.getByText('Immobili')).toBeVisible()
    await expect(page.getByText('Affittuari')).toBeVisible()

    // Step 6: Navigate to submenu item (if routes exist)
    // This would require the actual route to exist in your app
    // await page.getByText('Immobili').click()
    // await expect(page).toHaveURL(/immobili/)
  })

  test('should persist authentication across page reloads', async ({ page }) => {
    await page.route('**/api/v1/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'persistent-token',
          token_type: 'bearer'
        })
      })
    })

    await page.route('**/api/v1/platform/menu/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      })
    })

    await page.route('**/api/v1/platform/dashboard/my-dashboard', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ layout: [], widgets: [] })
      })
    })

    // Login
    await page.goto('/login')
    await page.getByLabel(/username|email/i).fill('test@example.com')
    await page.getByLabel(/password/i).fill('password123')
    await page.getByRole('button', { name: /login|accedi/i }).click()

    await expect(page).toHaveURL(/dashboard/)

    // Reload page
    await page.reload()

    // Should still be on dashboard (not redirected to login)
    await expect(page).toHaveURL(/dashboard/)
  })

  test('should handle menu loading errors gracefully', async ({ page }) => {
    await page.route('**/api/v1/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'test-token',
          token_type: 'bearer'
        })
      })
    })

    // Menu endpoint returns error
    await page.route('**/api/v1/platform/menu/', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Internal server error'
        })
      })
    })

    await page.route('**/api/v1/platform/dashboard/my-dashboard', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ layout: [], widgets: [] })
      })
    })

    await page.goto('/login')
    await page.getByLabel(/username|email/i).fill('test@example.com')
    await page.getByLabel(/password/i).fill('password123')
    await page.getByRole('button', { name: /login|accedi/i }).click()

    // Should show error in menu area
    await expect(page.getByText(/errore menu/i)).toBeVisible()

    // Should have retry button
    await expect(page.getByRole('button', { name: /riprova/i })).toBeVisible()
  })

  test('should handle dashboard loading errors gracefully', async ({ page }) => {
    await page.route('**/api/v1/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'test-token',
          token_type: 'bearer'
        })
      })
    })

    await page.route('**/api/v1/platform/menu/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      })
    })

    // Dashboard endpoint returns error
    await page.route('**/api/v1/platform/dashboard/my-dashboard', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Dashboard error'
        })
      })
    })

    await page.goto('/login')
    await page.getByLabel(/username|email/i).fill('test@example.com')
    await page.getByLabel(/password/i).fill('password123')
    await page.getByRole('button', { name: /login|accedi/i }).click()

    // Should show error message
    await expect(page.getByText(/errore caricamento dashboard/i)).toBeVisible()

    // Should have retry button
    await expect(page.getByRole('button', { name: /riprova/i })).toBeVisible()
  })
})
