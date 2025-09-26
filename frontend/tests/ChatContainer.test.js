import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createStore } from 'vuex'
import ChatContainer from '@/components/ChatContainer.vue'
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

describe('ChatContainer Component - Error State Bugs', () => {
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

    // Set up initialized state (user/languages succeeded)
    store.commit('USER_SET_AVAILABLE_LANGUAGES', [
      'english',
      'ukrainian',
      'polish',
      'german',
    ])
    store.commit('USER_SET_LANGUAGE', 'english')
    store.commit('USER_SET_LEVEL', 'intermediate')
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('Bug 1: MessageInput blocking when /start fails', () => {
    it('RED TEST: MessageInput should be disabled when /start endpoint fails', async () => {
      // This test will FAIL with current implementation - this is intentional (red test)

      // Setup: User is initialized (languages loaded successfully)
      // This simulates the state after choosing a level, which triggers /start

      // Simulate /start endpoint failure
      store.commit('APP_SET_ERROR', {
        message: 'Failed to generate greeting message',
        isRetryable: true,
        timestamp: Date.now(),
        endpoint: '/start',
      })

      // Mount ChatContainer
      wrapper = mount(ChatContainer, {
        global: {
          plugins: [store],
        },
      })

      // Current Implementation Problem:
      // MessageInput disabled logic: :disabled="isLoading || !isInitialized"
      // - isLoading: false (loading finished)
      // - isInitialized: true (user is initialized)
      // - hasError: true (start failed) - BUT THIS IS NOT CHECKED

      const messageInput = wrapper.findComponent({ name: 'MessageInput' })

      // This assertion will FAIL with current implementation
      // because hasError is not included in disable logic
      expect(messageInput.props('disabled')).toBe(true)

      // Additional verification: error should be visible
      expect(store.getters.hasError).toBe(true)
      expect(store.getters.currentError.endpoint).toBe('/start')

      // User should not be able to type when start message generation failed
      // because the conversation context is not properly established
    })

    it('RED TEST: MessageInput should be enabled when no error state exists', async () => {
      // This test should PASS with current implementation (control test)

      // Setup: User initialized, no errors
      store.commit('CONNECTION_SET_SUCCESS', '/start')
      store.commit('CHAT_CLEAR_ERROR')

      wrapper = mount(ChatContainer, {
        global: {
          plugins: [store],
        },
      })

      const messageInput = wrapper.findComponent({ name: 'MessageInput' })

      // This should work with current implementation
      expect(messageInput.props('disabled')).toBe(false)
      expect(store.getters.hasError).toBe(false)
    })

    it('RED TEST: MessageInput should be disabled during loading state', async () => {
      // This test should PASS with current implementation (control test)

      store.commit('CHAT_SET_LOADING', true)

      wrapper = mount(ChatContainer, {
        global: {
          plugins: [store],
        },
      })

      const messageInput = wrapper.findComponent({ name: 'MessageInput' })

      // This should work with current implementation
      expect(messageInput.props('disabled')).toBe(true)
      expect(store.getters.isLoading).toBe(true)
    })
  })

  describe('Bug 1 Extended: Error states should block input', () => {
    it('RED TEST: MessageInput disabled when /chat fails', async () => {
      // Test that input is disabled for any error state

      store.commit('APP_SET_ERROR', {
        message: 'Message sending failed',
        isRetryable: true,
        timestamp: Date.now(),
        endpoint: '/chat',
      })

      wrapper = mount(ChatContainer, {
        global: {
          plugins: [store],
        },
      })

      const messageInput = wrapper.findComponent({ name: 'MessageInput' })

      // This will FAIL - current implementation doesn't check hasError
      expect(messageInput.props('disabled')).toBe(true)
      expect(store.getters.hasError).toBe(true)
    })

    it('RED TEST: MessageInput disabled when /languages fails', async () => {
      // Test that input is disabled even for language loading errors

      store.commit('APP_SET_ERROR', {
        message: 'Unable to load language options',
        isRetryable: true,
        timestamp: Date.now(),
        endpoint: '/languages',
      })

      wrapper = mount(ChatContainer, {
        global: {
          plugins: [store],
        },
      })

      const messageInput = wrapper.findComponent({ name: 'MessageInput' })

      // This will FAIL - current implementation doesn't check hasError
      expect(messageInput.props('disabled')).toBe(true)
      expect(store.getters.hasError).toBe(true)
    })
  })
})
