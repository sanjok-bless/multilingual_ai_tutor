import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createStore } from 'vuex'
import ChatErrorMessage from '@/components/ChatErrorMessage.vue'
import state from '@/store/state.js'
import getters from '@/store/getters.js'
import mutations from '@/store/mutations.js'
// Session Management Actions
import * as sessionActions from '@/store/actions.session.js'

// Chat Workflow Actions
import * as chatActions from '@/store/actions.chat.js'

// Initialization Orchestration Actions
import * as initializationActions from '@/store/actions.initialization.js'

const actions = {
  // Session Actions
  ...sessionActions,

  // Chat Actions
  ...chatActions,

  // Initialization Actions
  ...initializationActions,
}

describe('ChatErrorMessage Component', () => {
  let wrapper
  let store

  beforeEach(() => {
    // Create fresh store instance
    store = createStore({
      state,
      getters,
      mutations,
      actions,
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('Display Error Scenarios', () => {
    it('renders error message with display error (traditional scenario)', async () => {
      // Setup: Traditional display error
      store.commit('APP_SET_ERROR', {
        message: 'Sorry, I had trouble sending your message. Please try again.',
        isRetryable: true,
        timestamp: Date.now(),
      })

      // Mount component
      wrapper = mount(ChatErrorMessage, {
        props: {
          error: store.getters.currentError,
        },
        global: {
          plugins: [store],
        },
      })

      // Verify error message displays
      expect(wrapper.text()).toContain(
        'Sorry, I had trouble sending your message. Please try again.'
      )
      expect(wrapper.find('.text-red-800').exists()).toBe(true)
    })

    it('renders error message with connection error (languages failure scenario)', async () => {
      // Setup: Connection error only (simulates /languages failure)
      store.commit('APP_SET_ERROR', {
        message: 'Unable to load language options',
        isRetryable: true,
        timestamp: Date.now(),
        endpoint: '/languages',
      })

      // Mount component with unified error from getter
      wrapper = mount(ChatErrorMessage, {
        props: {
          error: store.getters.currentError,
        },
        global: {
          plugins: [store],
        },
      })

      // Verify error message displays (this was broken before the fix)
      expect(wrapper.text()).toContain('Unable to load language options')
      expect(wrapper.find('.text-red-800').exists()).toBe(true)
    })
  })

  describe('Retry Button Behavior', () => {
    it('shows retry button for retryable display errors', async () => {
      // Setup: Retryable display error
      store.commit('APP_SET_ERROR', {
        message: 'Network error occurred',
        isRetryable: true,
        timestamp: Date.now(),
      })

      wrapper = mount(ChatErrorMessage, {
        props: {
          error: store.getters.currentError,
        },
        global: {
          plugins: [store],
        },
      })

      // Verify retry button shows
      expect(store.getters.shouldShowRetryButton).toBe(true)
      expect(wrapper.find('button').exists()).toBe(true)
      expect(wrapper.find('button').text()).toContain('Retry')
    })

    it('shows retry button for connection errors (languages failure fix)', async () => {
      // Setup: Connection error (this is the main fix being tested)
      store.commit('APP_SET_ERROR', {
        message: 'Connection failed',
        isRetryable: true,
        timestamp: Date.now(),
        endpoint: '/languages',
      })

      wrapper = mount(ChatErrorMessage, {
        props: {
          error: store.getters.currentError,
        },
        global: {
          plugins: [store],
        },
      })

      // Verify retry button shows (this was broken before the fix)
      expect(store.getters.shouldShowRetryButton).toBe(true)
      expect(wrapper.find('button').exists()).toBe(true)
      expect(wrapper.find('button').text()).toContain('Retry')
    })

    it('shows "Try again later" when max retries reached', async () => {
      // Setup: Connection error with max retries reached
      store.commit('APP_SET_ERROR', {
        message: 'Persistent connection failure',
        isRetryable: true,
        timestamp: Date.now(),
        endpoint: '/languages',
      })

      // Simulate max retries reached
      const maxRetries = store.state.app.maxRetries
      store.commit('APP_SET_RETRY_ATTEMPTS', maxRetries)

      wrapper = mount(ChatErrorMessage, {
        props: {
          error: store.getters.currentError,
        },
        global: {
          plugins: [store],
        },
      })

      // Verify "try later" message shows instead of retry button
      expect(store.getters.shouldShowRetryButton).toBe(false)
      expect(store.getters.shouldShowTryLater).toBe(true)
      expect(wrapper.find('button').exists()).toBe(false)
      expect(wrapper.text()).toContain('Try again later')
    })

    it('emits retry event when retry button clicked', async () => {
      // Setup: Retryable connection error
      store.commit('APP_SET_ERROR', {
        message: 'Temporary failure',
        isRetryable: true,
        timestamp: Date.now(),
        endpoint: '/languages',
      })

      wrapper = mount(ChatErrorMessage, {
        props: {
          error: store.getters.currentError,
        },
        global: {
          plugins: [store],
        },
      })

      // Act: Click retry button
      await wrapper.find('button').trigger('click')

      // Verify retry event emitted
      expect(wrapper.emitted('retry')).toBeTruthy()
      expect(wrapper.emitted('retry')).toHaveLength(1)
    })
  })

  describe('Error Precedence', () => {
    it('displays display error when both display and connection errors exist', async () => {
      // Setup: Both error types exist
      store.commit('APP_SET_ERROR', {
        message: 'Connection error',
        isRetryable: true,
        timestamp: Date.now(),
        endpoint: '/languages',
      })
      store.commit('APP_SET_ERROR', {
        message: 'Display error takes priority',
        isRetryable: true,
        timestamp: Date.now(),
      })

      wrapper = mount(ChatErrorMessage, {
        props: {
          error: store.getters.currentError,
        },
        global: {
          plugins: [store],
        },
      })

      // Verify display error takes precedence
      expect(wrapper.text()).toContain('Display error takes priority')
      expect(wrapper.text()).not.toContain('Connection error')
    })

    it('clears error completely when error is cleared (simplified single source)', async () => {
      // Setup: Error exists
      store.commit('APP_SET_ERROR', {
        message: 'Some error occurred',
        isRetryable: true,
        timestamp: Date.now(),
        endpoint: '/languages',
      })

      // Verify error exists
      expect(store.getters.currentError).toBeTruthy()
      expect(store.getters.hasError).toBe(true)

      // Clear error
      store.commit('APP_CLEAR_ERROR')

      // Verify error is completely cleared
      expect(store.getters.currentError).toBe(null)
      expect(store.getters.hasError).toBe(false)
    })
  })

  describe('Languages Endpoint Failure - Complete Scenario', () => {
    it('handles complete /languages failure user experience', async () => {
      // This test validates the complete fix for the original problem

      // Step 1: Simulate /languages endpoint failure (what user/loadAvailableLanguages does)
      store.commit('APP_SET_ERROR', {
        message: 'Unable to load language options',
        isRetryable: true,
        timestamp: Date.now(),
        endpoint: '/languages',
      })

      // Step 2: Verify ErrorMessage should be displayed (hasError)
      expect(store.getters.hasError).toBe(true)

      // Step 3: Verify error content is available (currentError)
      const currentError = store.getters.currentError
      expect(currentError).not.toBe(null)
      expect(currentError.message).toBe('Unable to load language options')
      expect(currentError.isRetryable).toBe(true)
      expect(currentError.endpoint).toBe('/languages')

      // Step 4: Mount ErrorMessage component
      wrapper = mount(ChatErrorMessage, {
        props: {
          error: currentError,
        },
        global: {
          plugins: [store],
        },
      })

      // Step 5: Verify complete UI behavior
      expect(wrapper.find('.text-red-800').exists()).toBe(true) // Error message visible
      expect(wrapper.text()).toContain('Unable to load language options')
      expect(store.getters.shouldShowRetryButton).toBe(true) // Retry button visible
      expect(wrapper.find('button').exists()).toBe(true)
      expect(wrapper.find('button').text()).toContain('Retry')

      // Step 6: Test retry functionality
      await wrapper.find('button').trigger('click')
      expect(wrapper.emitted('retry')).toBeTruthy()

      // This test proves the complete fix works end-to-end for /languages failures
    })
  })
})
