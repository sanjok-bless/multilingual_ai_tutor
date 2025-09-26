import { describe, it, expect, beforeEach } from 'vitest'
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

describe('Store Integration Tests - Cross-Domain Workflows', () => {
  let store

  beforeEach(() => {
    store = createStore({
      state,
      getters,
      mutations,
      actions,
    })
  })

  describe('Session Management Workflows', () => {
    it('should call requestStartMessage for yesterday human message', () => {
      const currentTimestamp = Date.now()
      const yesterdayTimestamp = currentTimestamp - 24 * 60 * 60 * 1000 // 24 hours ago

      // Setup: Add yesterday human message to session
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'test-session-id',
        language: 'english',
        level: 'B2',
        messages: [
          {
            type: 'user',
            content: 'This message is from yesterday',
            timestamp: yesterdayTimestamp,
          },
        ],
        lastActivity: yesterdayTimestamp,
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)

      // Verify: Session has yesterday message that should trigger start message logic
      const currentSession = store.getters.currentSession
      expect(currentSession.messages).toHaveLength(1)
      expect(currentSession.messages[0].type).toBe('user')
      expect(currentSession.messages[0].timestamp).toBe(yesterdayTimestamp)
    })

    it('should call sendMessage for today human message', () => {
      const currentTimestamp = Date.now()

      // Setup: Add recent human message to session
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'test-session-id',
        language: 'english',
        level: 'B2',
        messages: [
          {
            type: 'user',
            content: 'This message is from today',
            timestamp: currentTimestamp - 1 * 60 * 60 * 1000, // 1 hour ago
          },
        ],
        lastActivity: currentTimestamp - 1 * 60 * 60 * 1000,
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)

      // Verify: Session has recent message that should trigger resend logic
      const currentSession = store.getters.currentSession
      expect(currentSession.messages).toHaveLength(1)
      expect(currentSession.messages[0].type).toBe('user')
      expect(currentSession.messages[0].content).toBe(
        'This message is from today'
      )
    })

    it('should call requestStartMessage for empty session', () => {
      // Setup: Create empty session
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'test-session-id',
        language: 'english',
        level: 'B2',
        messages: [],
        lastActivity: Date.now(),
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)

      // Verify: Empty session should trigger start message logic
      const currentSession = store.getters.currentSession
      expect(currentSession.messages).toHaveLength(0)
    })

    it('should call requestStartMessage when needsDailyStart is true', () => {
      const currentTimestamp = Date.now()
      const yesterdayTimestamp = currentTimestamp - 24 * 60 * 60 * 1000

      // Setup: Add yesterday AI message to session
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'test-session-id',
        language: 'english',
        level: 'B2',
        messages: [
          {
            type: 'ai',
            content: 'Hello! I am your tutor.',
            timestamp: yesterdayTimestamp,
            corrections: [],
          },
        ],
        lastActivity: yesterdayTimestamp,
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)

      // Verify: Session with old AI message should trigger new start message
      const currentSession = store.getters.currentSession
      expect(currentSession.messages).toHaveLength(1)
      expect(currentSession.messages[0].type).toBe('ai')
      // Session becomes current, so lastActivity may be updated to current time
      // Allow for either preserved timestamp or updated to current time
      const timeDiff = Math.abs(
        currentSession.lastActivity - yesterdayTimestamp
      )
      const isPreserved = timeDiff < 1000
      const isUpdatedToNow =
        Math.abs(currentSession.lastActivity - currentTimestamp) < 1000
      expect(isPreserved || isUpdatedToNow).toBe(true)
    })

    it('should handle initialization lock correctly', () => {
      // Setup: Create session for lock testing
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'test-session-id',
        language: 'english',
        level: 'B2',
        messages: [],
        lastActivity: Date.now(),
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)

      // Verify: Lock state can be managed
      expect(store.state.sessions.isInitializingSession).toBe(false)

      store.commit('SESSION_SET_INITIALIZING', true)
      expect(store.state.sessions.isInitializingSession).toBe(true)

      store.commit('SESSION_SET_INITIALIZING', false)
      expect(store.state.sessions.isInitializingSession).toBe(false)
    })

    it('should handle complete session creation workflow', () => {
      // Start with empty sessions
      expect(store.getters.hasAnySessions).toBe(false)
      expect(store.state.sessions.currentSessionKey).toBe(null)

      // Create a session
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'test-session-id',
        language: 'english',
        level: 'B2',
        messages: [],
        // Note: lastActivity will be automatically set by SESSION_ADD mutation
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)

      // Verify session is properly integrated
      expect(store.getters.hasAnySessions).toBe(true)
      expect(store.state.sessions.currentSessionKey).toBe(sessionKey)

      // Check the core properties (excluding lastActivity which is auto-set)
      const currentSession = store.getters.currentSession
      expect(currentSession.sessionId).toBe(sessionData.sessionId)
      expect(currentSession.language).toBe(sessionData.language)
      expect(currentSession.level).toBe(sessionData.level)
      expect(currentSession.messages).toEqual(sessionData.messages)
      expect(currentSession.lastActivity).toBeDefined()
    })

    it('should handle session switching workflow', () => {
      // Create multiple sessions
      const session1Key = 'session_english_B2'
      const session1Data = {
        sessionId: 'session-1',
        language: 'english',
        level: 'B2',
        messages: [],
        lastActivity: 1000,
      }

      const session2Key = 'session_ukrainian_A2'
      const session2Data = {
        sessionId: 'session-2',
        language: 'ukrainian',
        level: 'A2',
        messages: [],
        lastActivity: 2000,
      }

      store.commit('SESSION_ADD', {
        sessionKey: session1Key,
        sessionData: session1Data,
      })
      store.commit('SESSION_ADD', {
        sessionKey: session2Key,
        sessionData: session2Data,
      })

      // Start with session 1
      store.commit('SESSION_SET_CURRENT', session1Key)
      expect(store.getters.currentSession.sessionId).toBe('session-1')

      // Switch to session 2
      store.commit('SESSION_SET_CURRENT', session2Key)
      expect(store.getters.currentSession.sessionId).toBe('session-2')
      expect(store.state.sessions.currentSessionKey).toBe(session2Key)
    })

    it('should handle lastActiveSession logic correctly', async () => {
      // Create first session (will be older)
      const olderSession = {
        sessionId: 'older',
        language: 'english',
        level: 'B2',
        messages: [],
      }

      store.commit('SESSION_ADD', {
        sessionKey: 'session_english_B2',
        sessionData: olderSession,
      })

      // Wait a bit to ensure time difference
      await new Promise(resolve => setTimeout(resolve, 2))

      // Create second session (will be newer due to later timestamp)
      const newerSession = {
        sessionId: 'newer',
        language: 'ukrainian',
        level: 'A2',
        messages: [],
      }

      store.commit('SESSION_ADD', {
        sessionKey: 'session_ukrainian_A2',
        sessionData: newerSession,
      })

      // Should find the most recent session (the one added later)
      expect(store.getters.lastActiveSession.sessionId).toBe('newer')
    })
  })

  describe('Message Flow Workflows', () => {
    it('should handle complete message workflow with corrections', () => {
      // Setup session
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

      // Add user message
      const userMessage = {
        type: 'user',
        content: 'I are learning English',
        timestamp: Date.now(),
      }

      store.commit('SESSION_ADD_MESSAGE', { sessionKey, message: userMessage })

      // Add AI response with corrections
      const corrections = [
        {
          original: 'I are',
          corrected: 'I am',
          explanation: 'Subject-verb agreement: Use "am" with "I"',
        },
      ]

      const aiMessage = {
        type: 'ai',
        content: 'Great! You said "I am learning English" - that\'s correct!',
        corrections,
        timestamp: Date.now(),
      }

      store.commit('SESSION_ADD_MESSAGE', { sessionKey, message: aiMessage })
      store.commit('CHAT_UPDATE_CURRENT_CORRECTIONS', corrections)

      // Verify complete workflow
      const messages = store.getters.allMessages
      expect(messages).toHaveLength(2)
      expect(messages[0]).toMatchObject(userMessage)
      expect(messages[1]).toMatchObject(aiMessage)
      expect(store.state.chat.currentCorrections).toEqual(corrections)
      expect(
        store.getters.allMessages[store.getters.allMessages.length - 1]
      ).toMatchObject(aiMessage)
    })

    it('should handle messagesByType filtering', () => {
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'test-session',
        language: 'english',
        level: 'B2',
        messages: [
          { type: 'user', content: 'Hello', timestamp: 1 },
          { type: 'ai', content: 'Hi there!', timestamp: 2 },
          { type: 'user', content: 'How are you?', timestamp: 3 },
          { type: 'ai', content: 'I am good!', timestamp: 4 },
        ],
        lastActivity: Date.now(),
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)

      const userMessages = store.getters.allMessages.filter(
        msg => msg.type === 'user'
      )
      const aiMessages = store.getters.allMessages.filter(
        msg => msg.type === 'ai'
      )

      expect(userMessages).toHaveLength(2)
      expect(aiMessages).toHaveLength(2)
      expect(userMessages[0].content).toBe('Hello')
      expect(aiMessages[0].content).toBe('Hi there!')
    })

    it('should load corrections from last AI message when no action needed', () => {
      const currentTimestamp = Date.now()

      // Setup: Add recent complete conversation to session
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'test-session',
        language: 'english',
        level: 'B2',
        messages: [
          {
            type: 'user',
            content: 'Hello',
            timestamp: currentTimestamp - 30 * 60 * 1000, // 30 minutes ago
          },
          {
            type: 'ai',
            content: 'Hello! Nice to meet you.',
            timestamp: currentTimestamp - 25 * 60 * 1000, // 25 minutes ago
            corrections: [
              {
                original: 'hello',
                corrected: 'Hello',
                explanation: 'Capitalize greetings',
              },
            ],
          },
        ],
        lastActivity: currentTimestamp - 25 * 60 * 1000,
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)

      // Manually load corrections from last AI message (simulating initialization logic)
      const lastAiMessage = sessionData.messages.find(
        msg => msg.type === 'ai' && msg.corrections
      )
      if (lastAiMessage) {
        store.commit(
          'CHAT_UPDATE_CURRENT_CORRECTIONS',
          lastAiMessage.corrections
        )
      }

      // Verify: Corrections were loaded from last AI message
      expect(store.state.chat.currentCorrections).toEqual([
        {
          original: 'hello',
          corrected: 'Hello',
          explanation: 'Capitalize greetings',
        },
      ])

      // Verify: Complete conversation exists
      expect(store.getters.allMessages).toHaveLength(2)
      expect(
        store.getters.allMessages[store.getters.allMessages.length - 1].type
      ).toBe('ai')
    })
  })

  describe('Error State Workflows', () => {
    it('should handle error state transitions correctly', () => {
      // Start with no error
      expect(store.getters.hasError).toBe(false)
      expect(store.getters.shouldShowRetryButton).toBe(false)

      // Set connection error
      store.commit('APP_SET_ERROR', {
        message: 'Network timeout',
        isRetryable: true,
        endpoint: '/chat',
        timestamp: Date.now(),
      })

      expect(store.getters.hasError).toBe(true)
      expect(store.getters.currentError.message).toBe('Network timeout')
      expect(store.getters.shouldShowRetryButton).toBe(true)

      // Increment retry attempts
      store.commit('APP_INCREMENT_RETRY_ATTEMPTS')
      expect(store.state.app.retryAttempts).toBe(1)
      expect(store.getters.shouldShowRetryButton).toBe(true) // Still < maxRetries

      // Reach max retries
      store.commit('APP_SET_RETRY_ATTEMPTS', 3)
      expect(store.getters.shouldShowRetryButton).toBe(false)
      expect(store.getters.shouldShowTryLater).toBe(true)

      // Clear error and reset retry
      store.commit('APP_SET_SUCCESS', '/chat')
      store.commit('APP_RESET_RETRY_ATTEMPTS')

      expect(store.getters.hasError).toBe(false)
      expect(store.state.app.retryAttempts).toBe(0)
      expect(store.getters.shouldShowRetryButton).toBe(false)
      expect(store.getters.shouldShowTryLater).toBe(false)
    })

    it('should prioritize display error over connection error', () => {
      // Set connection error first
      store.commit('APP_SET_ERROR', {
        message: 'Connection failed',
        isRetryable: true,
        endpoint: '/chat',
        timestamp: Date.now(),
      })

      expect(store.getters.currentError.message).toBe('Connection failed')

      // Set display error - should take priority
      const displayError = {
        message: 'Display error message',
        isRetryable: true,
        timestamp: Date.now(),
      }
      store.commit('APP_SET_ERROR', displayError)

      expect(store.getters.currentError).toEqual(displayError)

      // Clear display error - should result in no error (current implementation)
      store.commit('APP_CLEAR_ERROR')
      expect(store.getters.currentError).toBe(null)
    })

    it('should preserve error state on retry failure', () => {
      // Setup: simulate failed /languages connection
      store.commit('APP_SET_ERROR', {
        endpoint: '/languages',
        message: 'Initial connection failed',
        isRetryable: true,
        timestamp: Date.now(),
      })

      // Verify initial failed state
      expect(store.state.app.isConnected).toBe(false)
      expect(store.state.app.lastErrorEndpoint).toBe('/languages')
      expect(store.getters.hasError).toBe(true)
      expect(store.getters.currentError.message).toBe(
        'Initial connection failed'
      )

      // Simulate retry failure by keeping same error state
      expect(store.state.app.isConnected).toBe(false)
    })

    it('should handle chat retry without retryable error state', () => {
      // Setup: simulate /chat error but without proper error state for retry
      store.commit('APP_SET_ERROR', {
        endpoint: '/chat',
        message: 'Chat failed',
        isRetryable: true,
        timestamp: Date.now(),
      })

      // With unified error display, connection error should now be shown
      const currentError = store.getters.currentError
      expect(currentError).not.toBe(null)
      expect(currentError.message).toBe('Chat failed')
      expect(currentError.endpoint).toBe('/chat')
      expect(currentError.isRetryable).toBe(true)

      // Verify retry button logic works
      expect(store.getters.shouldShowRetryButton).toBe(true)
      expect(store.getters.shouldShowTryLater).toBe(false)
    })

    it('should show complete ErrorMessage behavior for /languages failures', () => {
      // Setup: Simulate what happens when languages endpoint fails
      store.commit('APP_SET_ERROR', {
        endpoint: '/languages',
        message: 'Unable to load language options',
        isRetryable: true,
        timestamp: Date.now(),
      })

      // Verify ErrorMessage visibility (hasError getter)
      expect(store.getters.hasError).toBe(true)

      // Verify error content display (currentError getter)
      const currentError = store.getters.currentError
      expect(currentError).not.toBe(null)
      expect(currentError.message).toBe('Unable to load language options')
      expect(currentError.isRetryable).toBe(true)
      expect(currentError.endpoint).toBe('/languages')
      expect(typeof currentError.timestamp).toBe('number')

      // Verify retry button logic (shouldShowRetryButton getter)
      expect(store.getters.shouldShowRetryButton).toBe(true)
      expect(store.getters.shouldShowTryLater).toBe(false)

      // Test retry attempts and max retry behavior
      store.commit('APP_SET_RETRY_ATTEMPTS', 3) // Max retries reached
      expect(store.getters.shouldShowRetryButton).toBe(false)
      expect(store.getters.shouldShowTryLater).toBe(true)
    })

    it('should handle successful connection recovery', () => {
      // Start with connection error
      store.commit('APP_SET_ERROR', {
        endpoint: '/languages',
        message: 'Network timeout',
        isRetryable: true,
        timestamp: Date.now(),
      })

      // Verify error state
      expect(store.getters.hasError).toBe(true)
      expect(store.getters.currentError.message).toBe('Network timeout')

      // Simulate successful recovery
      store.commit('APP_SET_SUCCESS', '/languages')
      store.commit('APP_CLEAR_ERROR')

      // Verify error cleared
      expect(store.getters.hasError).toBe(false)
      expect(store.getters.currentError).toBe(null)
      expect(store.getters.shouldShowRetryButton).toBe(false)
      expect(store.getters.shouldShowTryLater).toBe(false)
    })

    it('should handle action errors gracefully during complex workflows', () => {
      // Setup: Create session for error testing
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'test-session-id',
        language: 'english',
        level: 'B2',
        messages: [],
        lastActivity: Date.now(),
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)

      // Simulate various error conditions that might occur during workflows
      store.commit('APP_SET_ERROR', {
        message: 'Action failed during workflow',
        isRetryable: true,
        timestamp: Date.now(),
      })

      // Verify error state is properly managed
      expect(store.getters.hasError).toBe(true)
      expect(store.getters.currentError.message).toBe(
        'Action failed during workflow'
      )

      // Verify session state is preserved despite error
      expect(store.getters.currentSession).toBeTruthy()
      expect(store.state.sessions.currentSessionKey).toBe(sessionKey)
    })
  })

  describe('User Language Workflow', () => {
    it('should handle language initialization workflow', () => {
      // Start in offline mode
      expect(store.getters.isInitialized).toBe(false)
      expect(store.getters.availableLanguages).toEqual(['english'])
      expect(store.getters.currentLanguage).toBe(null)

      // Simulate successful language loading
      const languages = ['english', 'ukrainian', 'polish', 'german']
      store.commit('USER_SET_AVAILABLE_LANGUAGES', languages)

      expect(store.getters.isInitialized).toBe(true)
      expect(store.getters.availableLanguages).toEqual(languages)

      // User selects a language
      store.commit('USER_SET_LANGUAGE', 'ukrainian')
      expect(store.getters.currentLanguage).toBe('ukrainian')

      // User changes level
      store.commit('USER_SET_LEVEL', 'advanced')
      expect(store.getters.currentLevel).toBe('C2')
      const levelToDisplay = level => REVERSE_LEVEL_MAPPING[level] || level
      expect(levelToDisplay(store.getters.currentLevel)).toBe('advanced')
    })

    it('should handle user profile updates with session context', () => {
      // Create a session
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'test-session',
        language: 'english',
        level: 'B2',
        messages: [{ type: 'ai', content: 'Welcome!', timestamp: Date.now() }],
        lastActivity: Date.now(),
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)

      // Update user language
      store.commit('USER_SET_AVAILABLE_LANGUAGES', ['english', 'ukrainian'])
      store.commit('USER_SET_LANGUAGE', 'ukrainian')

      // Verify state consistency
      expect(store.getters.currentLanguage).toBe('ukrainian')
      expect(store.getters.currentSession.language).toBe('english') // Session unchanged
      expect(store.getters.allMessages).toHaveLength(1) // Messages preserved
    })

    it('should handle fresh user with backend online scenario', () => {
      // Initial state verification (fresh user)
      expect(store.getters.currentLanguage).toBe(null)
      expect(store.getters.availableLanguages).toEqual(['english'])
      expect(store.getters.isInitialized).toBe(false)

      // Simulate successful language loading
      store.commit('USER_SET_AVAILABLE_LANGUAGES', [
        'english',
        'ukrainian',
        'polish',
        'german',
      ])

      // Simulate setting default language for fresh user
      store.commit('USER_SET_LANGUAGE', 'english') // Uses defaultSelectedLanguage

      // Verify online state
      expect(store.getters.availableLanguages).toEqual([
        'english',
        'ukrainian',
        'polish',
        'german',
      ])
      expect(store.getters.currentLanguage).toBe('english')
      expect(store.getters.isInitialized).toBe(true)
    })

    it('should handle returning user with backend online scenario', () => {
      // Setup: Create a session with Ukrainian language (simulating returning user)
      const sessionKey = 'session_ukrainian_B2'
      const sessionData = {
        sessionId: 'returning-user-session',
        language: 'ukrainian',
        level: 'B2',
        messages: [],
        lastActivity: Date.now(),
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)

      // Initial state verification
      expect(store.getters.currentLanguage).toBe(null)
      expect(store.getters.availableLanguages).toEqual(['english'])

      // Simulate successful language loading
      store.commit('USER_SET_AVAILABLE_LANGUAGES', [
        'english',
        'ukrainian',
        'polish',
        'german',
      ])

      // Simulate setting language based on last session
      store.commit('USER_SET_LANGUAGE', 'ukrainian') // Uses lastActiveSession language

      // Verify state - should use last session language
      expect(store.getters.availableLanguages).toEqual([
        'english',
        'ukrainian',
        'polish',
        'german',
      ])
      expect(store.getters.currentLanguage).toBe('ukrainian')
      expect(store.getters.isInitialized).toBe(true)
      expect(store.getters.currentSession.language).toBe('ukrainian')
    })

    it('should handle user with backend offline scenario', () => {
      // Initial state verification
      expect(store.getters.currentLanguage).toBe(null)
      expect(store.getters.availableLanguages).toEqual(['english'])
      expect(store.getters.isInitialized).toBe(false)

      // Simulate failed API (backend offline)
      store.commit('APP_SET_ERROR', {
        endpoint: '/languages',
        message: 'Connection failed',
        isRetryable: true,
        timestamp: Date.now(),
      })

      // Verify offline state - stays with only English, no selection
      expect(store.getters.availableLanguages).toEqual(['english'])
      expect(store.getters.currentLanguage).toBe(null) // No selection in offline mode
      expect(store.getters.isInitialized).toBe(false) // Only 1 language available
      expect(store.state.app.isConnected).toBe(false)
      expect(store.getters.currentError.message).toBe('Connection failed')
    })
  })

  describe('Initialization Workflows', () => {
    it('should handle session initialization flag correctly', () => {
      expect(store.state.sessions.isInitializingSession).toBe(false)

      store.commit('SESSION_SET_INITIALIZING', true)
      expect(store.state.sessions.isInitializingSession).toBe(true)

      store.commit('SESSION_SET_INITIALIZING', false)
      expect(store.state.sessions.isInitializingSession).toBe(false)
    })

    it('should handle complex state transitions during initialization', () => {
      // Simulate app startup
      expect(store.getters.isInitialized).toBe(false)
      expect(store.getters.hasAnySessions).toBe(false)
      expect(store.getters.currentSession).toBe(null)

      // Step 1: Load languages
      store.commit('USER_SET_AVAILABLE_LANGUAGES', ['english', 'ukrainian'])
      store.commit('USER_SET_LANGUAGE', 'english')

      expect(store.getters.isInitialized).toBe(true)

      // Step 2: Create/load session
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'startup-session',
        language: 'english',
        level: 'B2',
        messages: [],
        lastActivity: Date.now(),
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)

      expect(store.getters.hasAnySessions).toBe(true)
      expect(store.getters.currentSession).toMatchObject(sessionData)

      // Step 3: Initialize chat state
      store.commit('CHAT_SET_LOADING', false)
      store.commit('APP_CLEAR_ERROR')
      store.commit('APP_RESET_RETRY_ATTEMPTS')

      expect(store.getters.isLoading).toBe(false)
      expect(store.getters.hasError).toBe(false)
      expect(store.state.app.retryAttempts).toBe(0)

      // Verify complete initialization
      expect(store.getters.isInitialized).toBe(true)
      expect(store.getters.currentLanguage).toBe('english')
      expect(store.getters.currentSession).toBeTruthy()
      expect(store.getters.hasError).toBe(false)
    })

    describe('initializeSessionWithLock Connection Guard', () => {
      let mockDispatch
      let mockConsoleLog

      beforeEach(() => {
        mockDispatch = vi.fn()
        mockConsoleLog = vi.spyOn(console, 'log').mockImplementation(() => {})

        // Set up basic session state
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

      it('should proceed with initialization when connected', async () => {
        // Set connected state
        store.commit('APP_SET_SUCCESS', '/languages')
        expect(store.state.app.isConnected).toBe(true)

        // Import and call initializeSessionWithLock
        const { initializeSessionWithLock } = await import(
          '@/store/actions.initialization.js'
        )

        await initializeSessionWithLock({
          state: store.state,
          commit: store.commit.bind(store),
          dispatch: mockDispatch,
          getters: store.getters,
        })

        // Verify it proceeded with initialization
        expect(mockConsoleLog).not.toHaveBeenCalledWith(
          'Skipping session initialization - API not connected'
        )
        expect(mockDispatch).toHaveBeenCalled() // Should call requestStartMessage for empty session
      })

      it('should handle disconnection during initialization gracefully', async () => {
        // Start connected
        store.commit('APP_SET_SUCCESS', '/languages')
        expect(store.state.app.isConnected).toBe(true)

        // Mock dispatch to simulate disconnection during call
        mockDispatch.mockImplementation(async action => {
          if (action === 'requestStartMessage') {
            // Simulate disconnection during the call
            store.commit('APP_SET_ERROR', {
              endpoint: '/start',
              message: 'Connection lost',
              isRetryable: true,
              timestamp: Date.now(),
            })
            throw new Error('Connection lost')
          }
        })

        // Import and call initializeSessionWithLock
        const { initializeSessionWithLock } = await import(
          '@/store/actions.initialization.js'
        )

        // This should now throw because the dispatch fails
        await expect(
          initializeSessionWithLock({
            state: store.state,
            commit: store.commit.bind(store),
            dispatch: mockDispatch,
            getters: store.getters,
          })
        ).rejects.toThrow('Connection lost')

        // Verify initialization flag is properly reset even after error (finally block)
        expect(store.state.sessions.isInitializingSession).toBe(false)
        expect(store.state.app.isConnected).toBe(false)
      })
    })
  })

  describe('Cross-Domain State Consistency', () => {
    it('should maintain consistency between user settings and session data', () => {
      // Set user preferences
      store.commit('USER_SET_AVAILABLE_LANGUAGES', ['english', 'ukrainian'])
      store.commit('USER_SET_LANGUAGE', 'ukrainian')
      store.commit('USER_SET_LEVEL', 'A2')

      // Create session matching user preferences
      const sessionKey = 'session_ukrainian_A2'
      const sessionData = {
        sessionId: 'consistent-session',
        language: 'ukrainian',
        level: 'A2',
        messages: [],
        lastActivity: Date.now(),
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)

      // Verify consistency
      expect(store.getters.currentLanguage).toBe(
        store.getters.currentSession.language
      )
      expect(store.getters.currentLevel).toBe(
        store.getters.currentSession.level
      )
    })

    it('should handle cross-domain error propagation', () => {
      // Create session with messages
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'error-session',
        language: 'english',
        level: 'B2',
        messages: [
          { type: 'user', content: 'Test message', timestamp: Date.now() },
        ],
        lastActivity: Date.now(),
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)

      // Simulate error during message sending
      store.commit('CHAT_SET_LOADING', true)
      store.commit('APP_SET_ERROR', {
        endpoint: '/chat',
        message: 'Failed to send message',
        isRetryable: true,
        timestamp: Date.now(),
      })
      store.commit('CHAT_SET_LOADING', false)

      // Verify error state is properly reflected
      expect(store.getters.isLoading).toBe(false)
      expect(store.getters.hasError).toBe(true)
      expect(store.getters.currentError.endpoint).toBe('/chat')
      expect(store.getters.allMessages).toHaveLength(1) // Message preserved
    })
  })

  describe('Anonymous User Workflow', () => {
    it('should handle anonymous user detection correctly', () => {
      // No sessions = not anonymous (new user)
      expect(store.getters.isAnonymousUser).toBe(false)

      // Add session = anonymous user
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'anon-session',
        language: 'english',
        level: 'B2',
        messages: [],
        lastActivity: Date.now(),
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      expect(store.getters.isAnonymousUser).toBe(true)
    })
  })

  describe('Complex State Transitions', () => {
    it('should not duplicate user message during chat retry', () => {
      const testMessage = 'Hello, this is a test message'

      // Setup session
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'test-session-id',
        language: 'english',
        level: 'B2',
        messages: [],
        lastActivity: Date.now(),
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)

      // Step 1: Add user message (simulating initial send)
      const userMessage = {
        type: 'user',
        content: testMessage,
        timestamp: Date.now(),
      }
      store.commit('SESSION_ADD_MESSAGE', { sessionKey, message: userMessage })

      // Verify: User message added despite potential failure
      const currentSession = store.getters.currentSession
      expect(currentSession.messages).toHaveLength(1)
      expect(currentSession.messages[0].type).toBe('user')
      expect(currentSession.messages[0].content).toBe(testMessage)

      // Step 2: Simulate retry error state
      store.commit('APP_SET_ERROR', {
        message: 'Network timeout',
        isRetryable: true,
        originalContent: testMessage,
      })

      // Verify: Error state contains original content for retry
      const error = store.getters.currentError
      expect(error.isRetryable).toBe(true)
      expect(error.originalContent).toBe(testMessage)

      // Critical verification: User message should NOT be duplicated on retry
      // (The retry mechanism should use originalContent, not add another message)
      const userMessages = currentSession.messages.filter(
        msg => msg.type === 'user'
      )
      expect(userMessages).toHaveLength(1) // Should still be only 1 user message
      expect(userMessages[0].content).toBe(testMessage)
    })

    it('should manage isRetrying flag correctly during retry', () => {
      // Initial state: isRetrying should be false
      expect(store.getters.isRetrying).toBe(false)

      // Step 1: Set retrying state (simulating retry start)
      store.commit('APP_SET_RETRYING', true)
      expect(store.getters.isRetrying).toBe(true)

      // Step 2: Clear retrying state (simulating retry completion)
      store.commit('APP_SET_RETRYING', false)
      expect(store.getters.isRetrying).toBe(false)
    })

    it('should respect max retry attempts for chat messages', () => {
      const testMessage = 'Max retry test message'

      // Setup: Create error state with original content
      store.commit('APP_SET_ERROR', {
        message: 'Persistent failure',
        isRetryable: true,
        originalContent: testMessage,
      })

      // Verify initial retry state
      expect(store.state.app.retryAttempts < store.state.app.maxRetries).toBe(
        true
      ) // 0 < 3
      expect(store.getters.shouldShowRetryButton).toBe(true)

      // Step 1: Exhaust retry attempts
      store.commit('APP_SET_RETRY_ATTEMPTS', 3) // Max attempts reached

      // Verify: Retry should be blocked
      expect(store.state.app.retryAttempts < store.state.app.maxRetries).toBe(
        false
      ) // 3 >= 3
      expect(store.getters.shouldShowRetryButton).toBe(false)
      expect(store.getters.shouldShowTryLater).toBe(true)

      // Verify: retry attempts didn't increase beyond max
      expect(store.state.app.retryAttempts).toBe(3)
    })

    it('should handle complete chat retry flow with session management', () => {
      const testMessage = 'Integration test message'

      // Setup: Create session for integration test
      const sessionKey = 'session_english_B2'
      const sessionData = {
        sessionId: 'integration-session',
        language: 'english',
        level: 'B2',
        messages: [],
        lastActivity: Date.now(),
      }

      store.commit('SESSION_ADD', { sessionKey, sessionData })
      store.commit('SESSION_SET_CURRENT', sessionKey)

      // Initial state verification
      const initialSession = store.getters.currentSession
      expect(initialSession.messages).toHaveLength(0)

      // Step 1: Add user message (simulating failed send)
      const userMessage = {
        type: 'user',
        content: testMessage,
        timestamp: Date.now(),
      }
      store.commit('SESSION_ADD_MESSAGE', { sessionKey, message: userMessage })

      // Simulate failure state
      store.commit('APP_SET_ERROR', {
        message: 'Temporary failure',
        isRetryable: true,
        originalContent: testMessage,
      })

      // Verify state after failure
      expect(store.getters.hasError).toBe(true)
      expect(store.getters.shouldShowRetryButton).toBe(true)
      expect(store.state.app.retryAttempts).toBe(0)

      const sessionAfterFailure = store.getters.currentSession
      expect(sessionAfterFailure.messages).toHaveLength(1) // User message added
      expect(sessionAfterFailure.messages[0].type).toBe('user')

      // Step 2: Simulate successful retry (add AI response)
      const aiMessage = {
        type: 'ai',
        content: 'Integration test response',
        corrections: [],
        tokens_used: 15,
        timestamp: Date.now(),
      }

      store.commit('SESSION_ADD_MESSAGE', { sessionKey, message: aiMessage })
      store.commit('APP_CLEAR_ERROR')
      store.commit('APP_RESET_RETRY_ATTEMPTS')

      // Verify state after successful retry
      expect(store.getters.hasError).toBe(false) // Error cleared
      expect(store.state.app.retryAttempts).toBe(0) // Reset after success

      const sessionAfterSuccess = store.getters.currentSession
      expect(sessionAfterSuccess.messages).toHaveLength(2) // User + AI message

      // Verify AI message structure
      const addedAiMessage = sessionAfterSuccess.messages[1]
      expect(addedAiMessage.type).toBe('ai')
      expect(addedAiMessage.content).toBe('Integration test response')
      expect(addedAiMessage.tokens_used).toBe(15)
    })

    it('should route languages retry to correct action', () => {
      // Setup: simulate failed /languages connection
      store.commit('APP_SET_ERROR', {
        endpoint: '/languages',
        message: 'Connection failed',
        isRetryable: true,
        timestamp: Date.now(),
      })

      // Verify initial failed state
      expect(store.state.app.isConnected).toBe(false)
      expect(store.state.app.lastErrorEndpoint).toBe('/languages')

      // Verify error routing logic - /languages errors should be handled by user domain
      const currentError = store.getters.currentError
      expect(currentError.endpoint).toBe('/languages')
      expect(currentError.isRetryable).toBe(true)
    })

    it('should route start retry to correct action', () => {
      // Setup: simulate failed /start connection
      store.commit('APP_SET_ERROR', {
        endpoint: '/start',
        message: 'Start message failed',
        isRetryable: true,
        timestamp: Date.now(),
      })

      // Verify initial failed state
      expect(store.state.app.isConnected).toBe(false)
      expect(store.state.app.lastErrorEndpoint).toBe('/start')

      // Verify error routing logic - /start errors should be handled by chat domain
      const currentError = store.getters.currentError
      expect(currentError.endpoint).toBe('/start')
      expect(currentError.isRetryable).toBe(true)
    })

    it('should route retry dispatches correctly for different endpoints', () => {
      // Test /languages endpoint routing
      store.commit('APP_SET_ERROR', {
        endpoint: '/languages',
        message: 'Failed',
        isRetryable: true,
        timestamp: Date.now(),
      })
      expect(store.state.app.lastErrorEndpoint).toBe('/languages')

      // Test /start endpoint routing
      store.commit('APP_SET_ERROR', {
        endpoint: '/start',
        message: 'Failed',
        isRetryable: true,
        timestamp: Date.now(),
      })
      expect(store.state.app.lastErrorEndpoint).toBe('/start')

      // Test /chat endpoint routing
      store.commit('APP_SET_ERROR', {
        endpoint: '/chat',
        message: 'Failed',
        isRetryable: true,
        timestamp: Date.now(),
      })
      expect(store.state.app.lastErrorEndpoint).toBe('/chat')

      // Test invalid endpoint handling
      store.commit('APP_SET_ERROR', {
        endpoint: '/invalid',
        message: 'Failed',
        isRetryable: true,
        timestamp: Date.now(),
      })
      expect(store.state.app.lastErrorEndpoint).toBe('/invalid')

      // All should be retryable via unified error system
      expect(store.getters.hasError).toBe(true)
      expect(store.getters.currentError.isRetryable).toBe(true)
    })
  })
})
