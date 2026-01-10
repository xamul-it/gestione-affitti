# Testing Documentation

## Overview

This project has a comprehensive testing infrastructure with unit tests, component tests, and end-to-end tests.

**Test Statistics:**
- 33 unit/component tests (all passing)
- 8 E2E test scenarios
- Test coverage for critical user flows

## Tech Stack

- **Vitest** (v2.1.8): Fast unit test runner compatible with Vite
- **React Testing Library** (v16.3.0): Component testing utilities
- **@testing-library/user-event** (v14.6.1): User interaction simulation
- **@testing-library/jest-dom** (v6.9.1): Custom matchers for DOM assertions
- **MSW** (Mock Service Worker v2.12.3): API request mocking
- **Playwright** (v1.57.0): End-to-end browser testing

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── Platform/
│   │       ├── DynamicMenu.jsx
│   │       └── DynamicMenu.test.jsx      # Component tests
│   ├── pages/
│   │   ├── Dashboard.jsx
│   │   └── Dashboard.test.jsx            # Page component tests
│   └── test/
│       ├── setup.js                       # Global test setup
│       └── mocks/
│           ├── handlers.js                # MSW request handlers
│           └── server.js                  # MSW server setup
├── e2e/
│   └── auth-and-navigation.spec.js       # E2E tests
├── vitest.config.js                      # Vitest configuration
└── playwright.config.js                  # Playwright configuration
```

## Running Tests

### Unit and Component Tests

```bash
# Run tests in watch mode (recommended for development)
npm test

# Run tests once and exit
npm run test:run

# Run tests with UI interface
npm run test:ui

# Run tests with coverage report
npm run test:coverage
```

### End-to-End Tests

```bash
# Run E2E tests (headless)
npm run test:e2e

# Run E2E tests with UI interface
npm run test:e2e:ui

# Run E2E tests in headed mode (watch browser)
npm run test:e2e:headed

# Debug E2E tests
npm run test:e2e:debug
```

### Run All Tests

```bash
npm run test:all
```

## Writing Tests

### Example: Component Test

```javascript
import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import MyComponent from './MyComponent'

describe('MyComponent', () => {
  beforeEach(() => {
    // Setup runs before each test
    localStorage.clear()
  })

  it('should render correctly', async () => {
    render(
      <BrowserRouter>
        <MyComponent />
      </BrowserRouter>
    )

    // Wait for async operations
    await waitFor(() => {
      expect(screen.getByText('Expected Text')).toBeInTheDocument()
    })
  })

  it('should handle user interactions', async () => {
    const user = userEvent.setup()

    render(
      <BrowserRouter>
        <MyComponent />
      </BrowserRouter>
    )

    const button = screen.getByRole('button', { name: /click me/i })
    await user.click(button)

    expect(screen.getByText('Clicked!')).toBeInTheDocument()
  })
})
```

### Example: Mocking API Responses

```javascript
import { server } from '../test/mocks/server'
import { http, HttpResponse } from 'msw'

it('should handle API errors', async () => {
  // Override default handler for this test
  server.use(
    http.get('http://localhost:8000/api/v1/endpoint', () => {
      return HttpResponse.json(
        { detail: 'Error occurred' },
        { status: 500 }
      )
    })
  )

  render(<MyComponent />)

  await waitFor(() => {
    expect(screen.getByText(/error/i)).toBeInTheDocument()
  })
})
```

### Example: E2E Test

```javascript
import { test, expect } from '@playwright/test'

test('user can login and navigate', async ({ page }) => {
  // Mock API response
  await page.route('**/api/v1/auth/login', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ access_token: 'test-token' })
    })
  })

  // Navigate and interact
  await page.goto('/login')
  await page.getByLabel(/username/i).fill('test@example.com')
  await page.getByLabel(/password/i).fill('password123')
  await page.getByRole('button', { name: /login/i }).click()

  // Assert navigation occurred
  await expect(page).toHaveURL(/dashboard/)
})
```

## Test Coverage

Current test coverage includes:

### DynamicMenu Component (16 tests)
- Loading states
- Error handling (no auth, API failures)
- Empty states
- Menu rendering and icons
- Hierarchical menu expand/collapse
- Active route highlighting
- Authorization headers
- Accessibility (ARIA landmarks, list structure)

### Dashboard Component (17 tests)
- Loading states
- Error handling with retry functionality
- Empty states
- Widget rendering (title, description, category, component)
- Grid layout system
- Widget count display
- Refresh functionality
- Authorization headers
- Widget filtering (only render what's in layout)
- Accessibility (heading hierarchy, button labels)

### E2E Tests (8 scenarios)
- Login page display for unauthenticated users
- Successful login flow
- Invalid credentials error handling
- Complete user journey (login → menu → dashboard)
- Authentication persistence across reloads
- Menu loading error handling
- Dashboard loading error handling
- Error retry functionality

## Best Practices

### 1. Test User Behavior, Not Implementation

**Good:**
```javascript
await user.click(screen.getByRole('button', { name: /submit/i }))
expect(screen.getByText('Success!')).toBeInTheDocument()
```

**Bad:**
```javascript
expect(component.state.isSubmitted).toBe(true)
```

### 2. Use Accessible Queries

Priority order:
1. `getByRole()` - Best for accessibility
2. `getByLabelText()` - Form inputs
3. `getByText()` - Non-interactive content
4. `getByTestId()` - Last resort

### 3. Clean Up Between Tests

Tests should be independent. The setup file handles:
- Clearing localStorage
- Resetting mock functions
- Cleaning up DOM
- Resetting MSW handlers

### 4. Wait for Async Operations

```javascript
// Use waitFor for assertions that depend on async operations
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument()
})

// Or use findBy queries (combines getBy + waitFor)
const element = await screen.findByText('Loaded')
```

### 5. Mock External Dependencies

- API calls are mocked with MSW
- localStorage is mocked in setup
- window.matchMedia is mocked for responsive tests

## Troubleshooting

### Tests Timeout

Increase timeout in test or config:
```javascript
it('slow test', async () => {
  // ...
}, 10000) // 10 second timeout
```

### React Router Warnings

Wrap components in BrowserRouter:
```javascript
const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}
```

### API Mocks Not Working

1. Check MSW server is imported in setup.js
2. Verify endpoint URL matches exactly
3. Check request method (GET, POST, etc.)
4. Use `server.resetHandlers()` in afterEach

### E2E Tests Failing

1. Ensure dev server is running (handled automatically by webServer config)
2. Check selectors are correct and stable
3. Add explicit waits: `await page.waitForSelector('.element')`
4. Use `--headed` mode to debug: `npm run test:e2e:headed`

## CI/CD Integration

Tests are designed to run in CI environments:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    npm ci
    npm run test:run
    npm run test:e2e
```

Playwright automatically handles browser installation in CI.

## Additional Resources

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev/)
- [MSW Documentation](https://mswjs.io/)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

## Contributing

When adding new features:

1. Write tests first (TDD) or alongside implementation
2. Aim for meaningful coverage of critical paths
3. Test edge cases and error states
4. Ensure tests are fast and deterministic
5. Update this documentation if adding new test patterns

## Performance

Current test execution times:
- Unit/Component tests: ~23 seconds for 33 tests
- E2E tests: Varies based on scenarios (typically 30-60 seconds)

Tips for faster tests:
- Use `test.only()` to run single tests during development
- Minimize waitFor timeouts
- Mock heavy operations
- Run tests in parallel (default in Vitest)
