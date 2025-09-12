import { config } from '@vue/test-utils'

// Mock global properties or plugins if needed
config.global.mocks = {
  // Add global mocks here
}

// Mock console methods for cleaner test output
Object.defineProperty(window, 'console', {
  value: {
    ...console,
    // Suppress specific console methods during tests if needed
    warn: vi.fn(),
    error: vi.fn(),
  },
})

// Setup fetch mock for API calls
global.fetch = vi.fn()

beforeEach(() => {
  fetch.mockClear()
})
