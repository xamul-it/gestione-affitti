/**
 * Example Test File
 *
 * This file demonstrates common testing patterns used in this project.
 * Copy and adapt these patterns when writing new tests.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { server } from './mocks/server'
import { http, HttpResponse } from 'msw'

// Example component for demonstration
function ExampleComponent({ title }) {
  return (
    <div>
      <h1>{title}</h1>
      <button>Click me</button>
    </div>
  )
}

// Helper to render with React Router
const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('Example Test Patterns', () => {

  beforeEach(() => {
    // Runs before each test
    localStorage.clear()
    vi.clearAllMocks()
  })

  // Pattern 1: Basic rendering test
  it('should render component with props', () => {
    render(<ExampleComponent title="Test Title" />)

    expect(screen.getByText('Test Title')).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  // Pattern 2: User interaction test
  it('should handle user interactions', async () => {
    const user = userEvent.setup()

    render(<ExampleComponent title="Interactive Test" />)

    const button = screen.getByRole('button', { name: /click me/i })
    await user.click(button)

    // Assert something happened
    // expect(screen.getByText('Clicked!')).toBeInTheDocument()
  })

  // Pattern 3: Testing with React Router
  it('should work with routing', () => {
    renderWithRouter(<ExampleComponent title="Router Test" />)

    expect(screen.getByText('Router Test')).toBeInTheDocument()
  })

  // Pattern 4: Testing async operations
  it('should handle async data loading', async () => {
    render(<ExampleComponent title="Async Test" />)

    // Wait for async operation to complete
    await waitFor(() => {
      expect(screen.getByText('Async Test')).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  // Pattern 5: Testing with localStorage
  it('should read from localStorage', () => {
    localStorage.setItem('test_key', 'test_value')

    // Your component logic here
    const value = localStorage.getItem('test_key')
    expect(value).toBe('test_value')
  })

  // Pattern 6: Mocking API responses
  it('should handle API success', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/test', () => {
        return HttpResponse.json({
          data: 'success'
        })
      })
    )

    // Test component that makes API call
    // await waitFor(() => {
    //   expect(screen.getByText('success')).toBeInTheDocument()
    // })
  })

  // Pattern 7: Mocking API errors
  it('should handle API errors', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/test', () => {
        return HttpResponse.json(
          { detail: 'Error occurred' },
          { status: 500 }
        )
      })
    )

    // Test error handling
    // await waitFor(() => {
    //   expect(screen.getByText(/error/i)).toBeInTheDocument()
    // })
  })

  // Pattern 8: Testing form submission
  it('should submit form data', async () => {
    const user = userEvent.setup()

    // Assuming a form component
    // render(<FormComponent />)

    // await user.type(screen.getByLabelText(/username/i), 'testuser')
    // await user.type(screen.getByLabelText(/password/i), 'password123')
    // await user.click(screen.getByRole('button', { name: /submit/i }))

    // expect(screen.getByText('Success')).toBeInTheDocument()
  })

  // Pattern 9: Testing conditional rendering
  it('should show/hide elements conditionally', () => {
    const { rerender } = render(<ExampleComponent title="Initial" />)

    expect(screen.getByText('Initial')).toBeInTheDocument()

    rerender(<ExampleComponent title="Updated" />)

    expect(screen.getByText('Updated')).toBeInTheDocument()
    expect(screen.queryByText('Initial')).not.toBeInTheDocument()
  })

  // Pattern 10: Testing accessibility
  it('should be accessible', () => {
    render(<ExampleComponent title="Accessibility Test" />)

    // Check for ARIA roles
    expect(screen.getByRole('button')).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
  })

  // Pattern 11: Snapshot testing (use sparingly)
  it('should match snapshot', () => {
    const { container } = render(<ExampleComponent title="Snapshot Test" />)

    // Snapshots should be used for components that rarely change
    // expect(container.firstChild).toMatchSnapshot()
  })

  // Pattern 12: Testing loading states
  it('should show loading state', async () => {
    // Mock slow API response
    server.use(
      http.get('http://localhost:8000/api/v1/slow', async () => {
        await new Promise(resolve => setTimeout(resolve, 100))
        return HttpResponse.json({ data: 'loaded' })
      })
    )

    // Component should show loading initially
    // expect(screen.getByText(/loading/i)).toBeInTheDocument()

    // Then show loaded content
    // await waitFor(() => {
    //   expect(screen.getByText('loaded')).toBeInTheDocument()
    // })
  })
})

// Example E2E Test Pattern (in e2e/ directory)
/*
import { test, expect } from '@playwright/test'

test.describe('Example E2E Flow', () => {

  test('should complete user journey', async ({ page }) => {
    // Mock API
    await page.route('**/api/v1/data', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true })
      })
    })

    // Navigate
    await page.goto('/page')

    // Interact
    await page.getByLabel('Input').fill('test value')
    await page.getByRole('button', { name: /submit/i }).click()

    // Assert
    await expect(page.getByText('Success')).toBeVisible()
    await expect(page).toHaveURL(/\/success/)
  })
})
*/
