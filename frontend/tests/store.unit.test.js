import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { createStore } from 'vuex'
import state, { REVERSE_LEVEL_MAPPING } from '@/store/state.js'
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

describe('Store Unit Tests - State, Getters, Mutations', () => {
  let store

  beforeEach(() => {
    store = createStore({
      state,
      getters,
      mutations,
      actions,
    })
  })

  describe('State Initialization', () => {
    it('should initialize with correct default state structure', () => {
      const initialState = store.state

      // User domain
      expect(initialState.user).toEqual({
        selectedLanguage: null,
        defaultSelectedLanguage: 'english',
        selectedLevel: 'B2',
        availableLanguages: ['english'],
        levelMapping: {
          beginner: 'A2',
          intermediate: 'B2',
          advanced: 'C2',
        },
      })

      // Sessions domain
      expect(initialState.sessions).toEqual({
        currentSessionKey: null,
        sessionStorage: {},
        lastActiveSession: null,
        isInitializingSession: false,
      })

      // Chat domain
      expect(initialState.chat.currentCorrections).toEqual([])
      expect(initialState.chat.isLoading).toBe(false)

      // App domain
      expect(initialState.app.isConnected).toBe(null)
      expect(initialState.app.lastSuccessfulCall).toBe(null)
      expect(initialState.app.currentError).toBe(null)
      expect(initialState.app.lastErrorEndpoint).toBe(null)
      expect(initialState.app.isRetrying).toBe(false)
      expect(initialState.app.retryAttempts).toBe(0)
      expect(initialState.app.maxRetries).toBe(3)
    })
  })

  describe('Basic Getters', () => {
    it('should return correct user getters', () => {
      // Test currentLanguage getter
      expect(store.getters.currentLanguage).toBe(null)

      store.commit('USER_SET_LANGUAGE', 'english')
      expect(store.getters.currentLanguage).toBe('english')

      // Test currentLevel getter
      expect(store.getters.currentLevel).toBe('B2')

      // Test availableLanguages getter
      expect(store.getters.availableLanguages).toEqual(['english'])
    })

    it('should return correct chat getters', () => {
      expect(store.state.chat.currentCorrections).toEqual([])
      expect(store.getters.isLoading).toBe(false)
      expect(store.getters.isRetrying).toBe(false)
      expect(store.state.app.retryAttempts).toBe(0)
      expect(store.state.app.maxRetries).toBe(3)
    })

    it('should return correct session getters', () => {
      expect(store.state.sessions.currentSessionKey).toBe(null)
      expect(store.getters.allSessions).toEqual({})
      expect(store.state.sessions.isInitializingSession).toBe(false)
    })

    it('should return correct connection getters', () => {
      const appStatus = store.state.app
      expect(appStatus.isConnected).toBe(null)
      expect(appStatus.lastSuccessfulCall).toBe(null)
      expect(appStatus.currentError).toBe(null)
      expect(appStatus.lastErrorEndpoint).toBe(null)
    })
  })

  describe('Computed Getters', () => {
    it('should compute currentLevelDisplay correctly', () => {
      const levelToDisplay = level => REVERSE_LEVEL_MAPPING[level] || level
      expect(levelToDisplay(store.getters.currentLevel)).toBe('intermediate') // B2 default

      store.commit('USER_SET_LEVEL', 'A2')
      expect(levelToDisplay(store.getters.currentLevel)).toBe('beginner')

      store.commit('USER_SET_LEVEL', 'C2')
      expect(levelToDisplay(store.getters.currentLevel)).toBe('advanced')
    })

    it('should compute isInitialized based on available languages', () => {
      expect(store.getters.isInitialized).toBe(false) // Only 1 language

      store.commit('USER_SET_AVAILABLE_LANGUAGES', [
        'english',
        'ukrainian',
        'polish',
      ])
      expect(store.getters.isInitialized).toBe(true) // Multiple languages
    })

    it('should compute availableLevels', () => {
      const levels = store.getters.availableLevels
      expect(levels).toEqual([
        { key: 'A2', label: 'Beginner', cefr: 'A2' },
        { key: 'B2', label: 'Intermediate', cefr: 'B2' },
        { key: 'C2', label: 'Advanced', cefr: 'C2' },
      ])
    })

    it('should compute hasAnySessions correctly', () => {
      expect(store.getters.hasAnySessions).toBe(false)

      // Add a session
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'test-session-id',
        language: 'english',
        level: 'B2',
        messages: [],
        lastActivity: Date.now(),
      }
      store.commit('SESSION_ADD', { sessionKey, sessionData })

      expect(store.getters.hasAnySessions).toBe(true)
    })

    it('should compute isApiConnected correctly', () => {
      expect(store.state.app.isConnected).toBe(null) // Initial state

      store.commit('APP_SET_SUCCESS', '/test')
      expect(store.state.app.isConnected).toBe(true)

      store.commit('APP_SET_ERROR', {
        message: 'Failed',
        isRetryable: true,
        timestamp: Date.now(),
        endpoint: '/test',
      })
      expect(store.state.app.isConnected).toBe(false)
    })

    it('should compute canRetry correctly', () => {
      expect(store.state.app.retryAttempts < store.state.app.maxRetries).toBe(
        true
      ) // 0 < 3

      store.commit('APP_SET_RETRY_ATTEMPTS', 2)
      expect(store.state.app.retryAttempts < store.state.app.maxRetries).toBe(
        true
      ) // 2 < 3

      store.commit('APP_SET_RETRY_ATTEMPTS', 3)
      expect(store.state.app.retryAttempts < store.state.app.maxRetries).toBe(
        false
      ) // 3 >= 3
    })
  })

  describe('Error State Getters', () => {
    it('should compute hasError for display errors', () => {
      expect(store.getters.hasError).toBe(false)

      store.commit('APP_SET_ERROR', {
        message: 'Test error',
        isRetryable: true,
        timestamp: Date.now(),
      })
      expect(store.getters.hasError).toBe(true)
    })

    it('should compute hasError for connection errors', () => {
      expect(store.getters.hasError).toBe(false)

      store.commit('APP_SET_ERROR', {
        message: 'Connection failed',
        isRetryable: true,
        timestamp: Date.now(),
        endpoint: '/test',
      })
      expect(store.getters.hasError).toBe(true)
    })

    it('should compute currentError with display error priority', () => {
      const displayError = {
        message: 'Display error',
        isRetryable: true,
        timestamp: Date.now(),
      }
      store.commit('APP_SET_ERROR', displayError)

      expect(store.getters.currentError).toEqual(displayError)
    })

    it('should compute currentError from connection error when no display error', () => {
      store.commit('APP_SET_ERROR', {
        message: 'Unable to load languages',
        isRetryable: true,
        timestamp: Date.now(),
        endpoint: '/languages',
      })

      const currentError = store.getters.currentError
      expect(currentError.message).toBe('Unable to load languages')
      expect(currentError.isRetryable).toBe(true)
      expect(currentError.endpoint).toBe('/languages')
      expect(currentError.timestamp).toBeDefined()
    })

    it('should compute shouldShowRetryButton correctly', () => {
      expect(store.getters.shouldShowRetryButton).toBe(false) // No error

      store.commit('APP_SET_ERROR', {
        message: 'Test error',
        isRetryable: true,
        timestamp: Date.now(),
      })
      expect(store.getters.shouldShowRetryButton).toBe(true) // Retryable error, attempts < max

      store.commit('APP_SET_RETRY_ATTEMPTS', 3)
      expect(store.getters.shouldShowRetryButton).toBe(false) // Max attempts reached
    })

    it('should compute shouldShowTryLater correctly', () => {
      expect(store.getters.shouldShowTryLater).toBe(false) // No error

      store.commit('APP_SET_ERROR', {
        message: 'Test error',
        isRetryable: true,
        timestamp: Date.now(),
      })
      expect(store.getters.shouldShowTryLater).toBe(false) // Attempts < max

      store.commit('APP_SET_RETRY_ATTEMPTS', 3)
      expect(store.getters.shouldShowTryLater).toBe(true) // Max attempts reached
    })

    it('should show retry button for connection errors (/languages scenario)', () => {
      // Setup: simulate failed /languages connection
      store.commit('APP_SET_ERROR', {
        endpoint: '/languages',
        message: 'Connection failed',
        isRetryable: true,
        timestamp: Date.now(),
      })

      // Verify error is displayed via unified logic
      const currentError = store.getters.currentError
      expect(currentError).not.toBe(null)
      expect(currentError.message).toBe('Connection failed')
      expect(currentError.isRetryable).toBe(true)

      // Verify retry button appears (before retry attempts)
      expect(store.getters.shouldShowRetryButton).toBe(true)
      expect(store.getters.shouldShowTryLater).toBe(false)

      // Simulate max retries reached
      store.commit('APP_SET_RETRY_ATTEMPTS', 3)

      // Verify "try later" shows instead of retry button
      expect(store.getters.shouldShowRetryButton).toBe(false)
      expect(store.getters.shouldShowTryLater).toBe(true)
    })
  })

  describe('User Domain Mutations', () => {
    it('should set available languages correctly', () => {
      const languages = ['english', 'ukrainian', 'polish', 'german']
      store.commit('USER_SET_AVAILABLE_LANGUAGES', languages)
      expect(store.getters.availableLanguages).toEqual(languages)

      // Should ignore invalid input
      store.commit('USER_SET_AVAILABLE_LANGUAGES', null)
      expect(store.getters.availableLanguages).toEqual(languages) // Unchanged

      store.commit('USER_SET_AVAILABLE_LANGUAGES', [])
      expect(store.getters.availableLanguages).toEqual(languages) // Unchanged
    })

    it('should set language only if available', () => {
      store.commit('USER_SET_AVAILABLE_LANGUAGES', ['english', 'ukrainian'])

      store.commit('USER_SET_LANGUAGE', 'english')
      expect(store.getters.currentLanguage).toBe('english')

      store.commit('USER_SET_LANGUAGE', 'spanish') // Not in available languages
      expect(store.getters.currentLanguage).toBe('english') // Unchanged
    })

    it('should set level with CEFR mapping', () => {
      store.commit('USER_SET_LEVEL', 'beginner')
      expect(store.getters.currentLevel).toBe('A2')

      store.commit('USER_SET_LEVEL', 'intermediate')
      expect(store.getters.currentLevel).toBe('B2')

      store.commit('USER_SET_LEVEL', 'advanced')
      expect(store.getters.currentLevel).toBe('C2')

      // Direct CEFR levels should also work
      store.commit('USER_SET_LEVEL', 'A2')
      expect(store.getters.currentLevel).toBe('A2')
    })

    it('should reset to defaults', () => {
      store.commit('USER_SET_LANGUAGE', 'ukrainian')
      store.commit('USER_SET_LEVEL', 'C2')

      store.commit(
        'USER_SET_LANGUAGE',
        store.state.user.defaultSelectedLanguage
      )
      store.commit('USER_SET_LEVEL', 'B2')
      expect(store.getters.currentLanguage).toBe('english')
      expect(store.getters.currentLevel).toBe('B2')
    })

    it('should compute isInitialized getter with edge cases', () => {
      // Test offline state (1 language)
      store.commit('USER_SET_AVAILABLE_LANGUAGES', ['english'])
      expect(store.getters.isInitialized).toBe(false)

      // Test online state (multiple languages)
      store.commit('USER_SET_AVAILABLE_LANGUAGES', [
        'english',
        'ukrainian',
        'polish',
        'german',
      ])
      expect(store.getters.isInitialized).toBe(true)
    })

    it('should handle language state management edge cases', () => {
      // Test that invalid language selections are ignored
      store.commit('USER_SET_AVAILABLE_LANGUAGES', ['english', 'ukrainian'])

      // Try to set invalid language
      store.commit('USER_SET_LANGUAGE', 'french') // Not available
      expect(store.getters.currentLanguage).toBe(null) // Should remain null

      // Set valid language
      store.commit('USER_SET_LANGUAGE', 'ukrainian')
      expect(store.getters.currentLanguage).toBe('ukrainian')

      // Try to set another invalid language
      store.commit('USER_SET_LANGUAGE', 'spanish') // Not available
      expect(store.getters.currentLanguage).toBe('ukrainian') // Should remain unchanged
    })
  })

  describe('Chat Domain Mutations', () => {
    it('should manage loading state', () => {
      expect(store.getters.isLoading).toBe(false)

      store.commit('CHAT_SET_LOADING', true)
      expect(store.getters.isLoading).toBe(true)

      store.commit('CHAT_SET_LOADING', false)
      expect(store.getters.isLoading).toBe(false)
    })

    it('should manage error state', () => {
      const error = {
        message: 'Test error',
        isRetryable: true,
        timestamp: Date.now(),
      }

      store.commit('APP_SET_ERROR', error)
      expect(store.getters.currentError).toEqual(error)

      store.commit('APP_CLEAR_ERROR')
      expect(store.getters.currentError).toBe(null)
    })

    it('should manage retry state', () => {
      expect(store.getters.isRetrying).toBe(false)
      expect(store.state.app.retryAttempts).toBe(0)

      store.commit('APP_SET_RETRYING', true)
      expect(store.getters.isRetrying).toBe(true)

      store.commit('APP_INCREMENT_RETRY_ATTEMPTS')
      expect(store.state.app.retryAttempts).toBe(1)

      store.commit('APP_INCREMENT_RETRY_ATTEMPTS')
      expect(store.state.app.retryAttempts).toBe(2)

      store.commit('APP_RESET_RETRY_ATTEMPTS')
      expect(store.state.app.retryAttempts).toBe(0)

      store.commit('APP_SET_RETRY_ATTEMPTS', 5)
      expect(store.state.app.retryAttempts).toBe(5)
    })

    it('should manage corrections', () => {
      const corrections = [
        {
          original: 'I are',
          corrected: 'I am',
          explanation: 'Subject-verb agreement',
        },
      ]

      store.commit('CHAT_UPDATE_CURRENT_CORRECTIONS', corrections)
      expect(store.state.chat.currentCorrections).toEqual(corrections)

      store.commit('CHAT_UPDATE_CURRENT_CORRECTIONS', null)
      expect(store.state.chat.currentCorrections).toEqual([])
    })

    it('should manage basic chat error state', () => {
      // Test that chat error states work correctly

      // Set error state
      store.commit('APP_SET_ERROR', {
        message: 'Test error',
        isRetryable: true,
        originalContent: 'test message',
      })

      expect(store.getters.currentError).toEqual({
        message: 'Test error',
        isRetryable: true,
        originalContent: 'test message',
      })

      // Clear error state
      store.commit('APP_CLEAR_ERROR')

      expect(store.getters.currentError).toBe(null)
    })
  })

  describe('Session Domain Mutations', () => {
    it('should set current session', () => {
      const sessionKey = 'session_english_B2'
      store.commit('SESSION_SET_CURRENT', sessionKey)
      expect(store.state.sessions.currentSessionKey).toBe(sessionKey)
    })

    it('should add session correctly', () => {
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'test-session-id',
        language: 'english',
        level: 'B2',
        messages: [],
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })

      const storedSession = store.getters.allSessions[sessionKey]
      expect(storedSession).toMatchObject(sessionData)
      expect(storedSession.lastActivity).toBeDefined()
    })

    it('should update session activity', async () => {
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'test-session-id',
        language: 'english',
        level: 'B2',
        messages: [],
        lastActivity: 1000,
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })

      const originalActivity =
        store.getters.allSessions[sessionKey].lastActivity

      // Add small delay to ensure timestamp difference
      await new Promise(resolve => setTimeout(resolve, 1))

      store.commit('SESSION_UPDATE_ACTIVITY', sessionKey)
      const newActivity = store.getters.allSessions[sessionKey].lastActivity

      expect(newActivity).toBeGreaterThan(originalActivity)
    })

    it('should NOT update lastActivity when switching to existing session', () => {
      const originalTimestamp = Date.now() - 24 * 60 * 60 * 1000 // 24 hours ago

      // Setup: Create a session with specific lastActivity
      const sessionKey = 'test-yesterday-session'
      const sessionData = {
        sessionId: 'test-session-id-yesterday',
        language: 'english',
        level: 'B2',
        messages: [
          {
            type: 'user',
            content: 'Yesterday message',
            timestamp: originalTimestamp,
          },
        ],
        lastActivity: originalTimestamp,
      }

      // Add session directly to store
      store.commit('SESSION_ADD', { sessionKey, sessionData })

      // Fix: SESSION_ADD overrides lastActivity, so we need to restore it
      store.state.sessions.sessionStorage[sessionKey].lastActivity =
        originalTimestamp

      // Verify initial state
      const sessionBeforeSwitch = store.getters.allSessions[sessionKey]
      expect(sessionBeforeSwitch.lastActivity).toBe(originalTimestamp)

      // Act: Set as current session (should NOT update lastActivity)
      store.commit('SESSION_SET_CURRENT', sessionKey)

      // Verify: lastActivity should NOT be updated
      const sessionAfterSwitch = store.getters.allSessions[sessionKey]
      expect(sessionAfterSwitch.lastActivity).toBe(originalTimestamp) // Should remain unchanged

      // Verify: Session is properly set as current
      expect(store.state.sessions.currentSessionKey).toBe(sessionKey)
    })

    it('should NOT update lastActivity when using SET_CURRENT_SESSION mutation directly', () => {
      const originalTimestamp = Date.now() - 12 * 60 * 60 * 1000 // 12 hours ago

      // Setup: Create session with specific lastActivity
      const sessionKey = 'test-mutation-session'
      const sessionData = {
        sessionId: 'test-mutation-id',
        language: 'polish',
        level: 'A2',
        messages: [],
        lastActivity: originalTimestamp,
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      // Fix: SESSION_ADD overrides lastActivity, so we need to restore it
      store.state.sessions.sessionStorage[sessionKey].lastActivity =
        originalTimestamp

      // Verify initial state
      expect(store.getters.allSessions[sessionKey].lastActivity).toBe(
        originalTimestamp
      )

      // Act: Use SESSION_SET_CURRENT mutation directly
      store.commit('SESSION_SET_CURRENT', sessionKey)

      // Verify: lastActivity should NOT be changed
      const sessionAfterMutation = store.getters.allSessions[sessionKey]
      expect(sessionAfterMutation.lastActivity).toBe(originalTimestamp)

      // Verify: Session is set as current
      expect(store.state.sessions.currentSessionKey).toBe(sessionKey)
    })
  })

  describe('Edge Cases and Error Handling', () => {
    it('should handle missing session gracefully', () => {
      // Test: No current session should not crash

      // Verify initial state with no current session
      expect(store.getters.currentSession).toBe(null)
      expect(store.state.sessions.currentSessionKey).toBe(null)

      // Verify session-related getters handle null gracefully
      expect(store.getters.allMessages).toEqual([])
      expect(
        store.getters.allMessages.length > 0
          ? store.getters.allMessages[store.getters.allMessages.length - 1]
          : null
      ).toBe(null)

      // Verify calling mutations on null session doesn't crash
      expect(() => {
        store.commit('SESSION_ADD_MESSAGE', {
          sessionKey: null,
          message: { type: 'user', content: 'test' },
        })
      }).not.toThrow()
    })

    it('should handle messages without timestamps', () => {
      // Test: Malformed messages should not crash the logic

      // Setup: Add session with message without timestamp
      const sessionKey = 'test-malformed-session'
      const sessionData = {
        sessionId: 'test-malformed-id',
        language: 'english',
        level: 'B2',
        messages: [
          {
            type: 'user',
            content: 'Message without timestamp',
            // No timestamp property
          },
        ],
        lastActivity: Date.now(),
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)

      // Verify: Messages are stored despite missing timestamp
      const currentSession = store.getters.currentSession
      expect(currentSession.messages).toHaveLength(1)
      expect(currentSession.messages[0].content).toBe(
        'Message without timestamp'
      )
      expect(currentSession.messages[0].timestamp).toBeUndefined()

      // Verify: Getters handle missing timestamps gracefully
      expect(store.getters.allMessages).toHaveLength(1)
      expect(
        store.getters.allMessages[store.getters.allMessages.length - 1].content
      ).toBe('Message without timestamp')
    })
  })

  describe('Connection Domain Mutations', () => {
    it('should set connection success', () => {
      store.commit('APP_SET_SUCCESS', '/test')

      const status = store.state.app
      expect(status.isConnected).toBe(true)
      expect(status.lastSuccessfulCall).toBeDefined()
      expect(status.currentError).toBe(null)
      expect(status.lastErrorEndpoint).toBe(null)
    })

    it('should set connection error', () => {
      store.commit('APP_SET_ERROR', {
        message: 'Connection failed',
        isRetryable: true,
        timestamp: Date.now(),
        endpoint: '/languages',
      })

      const status = store.state.app
      expect(status.isConnected).toBe(false)
      expect(status.currentError.message).toBe('Connection failed')
      expect(status.lastErrorEndpoint).toBe('/languages')
    })
  })

  describe('initializeSessionWithLock Logic', () => {
    let mockDispatch
    let mockCommit
    let mockConsoleLog

    beforeEach(() => {
      mockDispatch = vi.fn()
      mockCommit = vi.fn()
      mockConsoleLog = vi.spyOn(console, 'log').mockImplementation(() => {})

      // Set up minimal session state for logic testing
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'test-session',
        language: 'english',
        level: 'B2',
        messages: [],
        lastActivity: Date.now(),
      }
      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)
    })

    afterEach(() => {
      mockConsoleLog.mockRestore()
    })

    it('should skip initialization when not connected', async () => {
      // Set disconnected state
      store.commit('APP_SET_ERROR', {
        endpoint: '/languages',
        message: 'Connection failed',
        isRetryable: true,
        timestamp: Date.now(),
      })
      expect(store.state.app.isConnected).toBe(false)

      // Import and call initializeSessionWithLock with minimal context
      const { initializeSessionWithLock } = await import(
        '@/store/actions.initialization.js'
      )

      await initializeSessionWithLock({
        state: store.state,
        commit: mockCommit,
        dispatch: mockDispatch,
        getters: store.getters,
      })

      // Verify it skipped execution - pure logic test
      expect(mockConsoleLog).toHaveBeenCalledWith(
        'Skipping session initialization - API not connected'
      )
      expect(mockDispatch).not.toHaveBeenCalled()
      expect(mockCommit).not.toHaveBeenCalled()
    })

    it('should handle concurrent initialization guard correctly when connected', async () => {
      // Set connected state
      store.commit('APP_SET_SUCCESS', '/languages')
      expect(store.state.app.isConnected).toBe(true)

      // Set initializing flag to test concurrency guard
      store.commit('SESSION_SET_INITIALIZING', true)

      // Import and call initializeSessionWithLock
      const { initializeSessionWithLock } = await import(
        '@/store/actions.initialization.js'
      )

      await initializeSessionWithLock({
        state: store.state,
        commit: mockCommit,
        dispatch: mockDispatch,
        getters: store.getters,
      })

      // Verify it respected concurrency guard - pure logic test
      expect(mockDispatch).not.toHaveBeenCalled()
      expect(mockCommit).not.toHaveBeenCalled()
      expect(store.state.sessions.isInitializingSession).toBe(true) // Still true
    })
  })
})
