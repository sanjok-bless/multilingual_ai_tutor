// === BASIC GETTERS (Direct State Access) ===
// User Domain
const currentLanguage = state => state.user.selectedLanguage
const currentLevel = state => state.user.selectedLevel
const availableLanguages = state => state.user.availableLanguages

// Session Domain
const allSessions = state => state.sessions.sessionStorage

// Chat Domain
const isLoading = state => state.chat.isLoading

// App Domain
const currentError = state => state.app.currentError
const isRetrying = state => state.app.isRetrying

// === COMPUTED GETTERS (Depend on Basic Getters) ===
// User Domain
const isInitialized = state => state.user.availableLanguages.length > 1

const availableLevels = () => [
  { key: 'A2', label: 'Beginner', cefr: 'A2' },
  { key: 'B2', label: 'Intermediate', cefr: 'B2' },
  { key: 'C2', label: 'Advanced', cefr: 'C2' },
]

// Session Domain
const currentSession = state => {
  return state.sessions.currentSessionKey
    ? state.sessions.sessionStorage[state.sessions.currentSessionKey]
    : null
}

const hasAnySessions = state =>
  Object.keys(state.sessions.sessionStorage).length > 0

const lastActiveSession = state => {
  if (
    !state.sessions.lastActiveSession ||
    !state.sessions.sessionStorage[state.sessions.lastActiveSession]
  ) {
    const sessionKeys = Object.keys(state.sessions.sessionStorage)
    if (sessionKeys.length === 0) return null

    const mostRecent = sessionKeys.reduce((latest, key) => {
      const session = state.sessions.sessionStorage[key]
      const latestSession = state.sessions.sessionStorage[latest]
      return session.lastActivity > latestSession.lastActivity ? key : latest
    })

    return state.sessions.sessionStorage[mostRecent]
  }
  return state.sessions.sessionStorage[state.sessions.lastActiveSession]
}

// === CROSS-DOMAIN GETTERS (Complex Logic) ===
const allMessages = (state, getters) => {
  const session = getters.currentSession
  return session ? session.messages : []
}

const hasError = state => !!state.app.currentError

const shouldShowRetryButton = state => {
  const error = state.app.currentError
  return !!(
    error &&
    error.isRetryable &&
    state.app.retryAttempts < state.app.maxRetries
  )
}

const shouldShowTryLater = state => {
  const error = state.app.currentError
  return !!(
    error &&
    error.isRetryable &&
    state.app.retryAttempts >= state.app.maxRetries
  )
}

const isAnonymousUser = (state, getters) => {
  return getters.hasAnySessions
}

export default {
  // Basic Getters
  currentLanguage,
  currentLevel,
  availableLanguages,
  allSessions,
  isLoading,
  currentError,
  isRetrying,

  // Computed Getters
  isInitialized,
  availableLevels,
  currentSession,
  hasAnySessions,
  lastActiveSession,

  // Cross-Domain Getters
  allMessages,
  hasError,
  shouldShowRetryButton,
  shouldShowTryLater,
  isAnonymousUser,
}
