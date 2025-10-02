import { LEVEL_MAPPING } from './state.js'

// === USER DOMAIN MUTATIONS ===
const USER_SET_AVAILABLE_LANGUAGES = (state, languages) => {
  if (Array.isArray(languages) && languages.length > 0) {
    state.user.availableLanguages = languages
  }
}

const USER_SET_LANGUAGE = (state, language) => {
  if (state.user.availableLanguages.includes(language)) {
    state.user.selectedLanguage = language
  }
}

const USER_SET_LEVEL = (state, level) => {
  const cefrLevel = LEVEL_MAPPING[level] || level
  if (Object.values(LEVEL_MAPPING).includes(cefrLevel)) {
    state.user.selectedLevel = cefrLevel
  }
}

// === SESSION DOMAIN MUTATIONS ===
const SESSION_SET_CURRENT = (state, sessionKey) => {
  state.sessions.currentSessionKey = sessionKey
  state.sessions.lastActiveSession = sessionKey
}

const SESSION_SET_STORAGE = (state, sessions) => {
  state.sessions.sessionStorage = sessions
}

const SESSION_ADD = (state, { sessionKey, sessionData }) => {
  state.sessions.sessionStorage[sessionKey] = {
    ...sessionData,
    lastActivity: Date.now(),
  }
}

const SESSION_UPDATE_ACTIVITY = (state, sessionKey) => {
  if (state.sessions.sessionStorage[sessionKey]) {
    state.sessions.sessionStorage[sessionKey].lastActivity = Date.now()
  }
}

const SESSION_ADD_MESSAGE = (state, { sessionKey, message }) => {
  if (state.sessions.sessionStorage[sessionKey]) {
    state.sessions.sessionStorage[sessionKey].messages.push(message)
    state.sessions.sessionStorage[sessionKey].lastActivity = Date.now()
  }
}

const SESSION_SET_INITIALIZING = (state, isInitializing) => {
  state.sessions.isInitializingSession = isInitializing
}

// === CHAT DOMAIN MUTATIONS ===
const CHAT_SET_LOADING = (state, loading) => {
  state.chat.isLoading = loading
}

const CHAT_UPDATE_CURRENT_CORRECTIONS = (state, corrections) => {
  state.chat.currentCorrections = corrections || []
}

// === APP DOMAIN MUTATIONS ===
const APP_SET_SUCCESS = (state, _endpoint) => {
  state.app.isConnected = true
  state.app.lastSuccessfulCall = Date.now()
  state.app.currentError = null
  state.app.lastErrorEndpoint = null
}

const APP_SET_ERROR = (state, error) => {
  state.app.currentError = error
  if (error.endpoint) {
    state.app.isConnected = false
    state.app.lastErrorEndpoint = error.endpoint
  }
}

const APP_CLEAR_ERROR = state => {
  state.app.currentError = null
}

const APP_SET_RETRYING = (state, retrying) => {
  state.app.isRetrying = retrying
}

const APP_INCREMENT_RETRY_ATTEMPTS = state => {
  state.app.retryAttempts += 1
}

const APP_RESET_RETRY_ATTEMPTS = state => {
  state.app.retryAttempts = 0
}

const APP_SET_RETRY_ATTEMPTS = (state, attempts) => {
  state.app.retryAttempts = attempts
}

const APP_SET_CONTEXT_LIMITS = (
  state,
  { contextChatLimit, contextStartLimit }
) => {
  if (contextChatLimit) state.app.contextChatLimit = contextChatLimit
  if (contextStartLimit) state.app.contextStartLimit = contextStartLimit
}

export default {
  // User Domain
  USER_SET_AVAILABLE_LANGUAGES,
  USER_SET_LANGUAGE,
  USER_SET_LEVEL,

  // Session Domain
  SESSION_SET_CURRENT,
  SESSION_SET_STORAGE,
  SESSION_ADD,
  SESSION_UPDATE_ACTIVITY,
  SESSION_ADD_MESSAGE,
  SESSION_SET_INITIALIZING,

  // Chat Domain
  CHAT_SET_LOADING,
  CHAT_UPDATE_CURRENT_CORRECTIONS,

  // App Domain
  APP_SET_SUCCESS,
  APP_SET_ERROR,
  APP_CLEAR_ERROR,
  APP_SET_RETRYING,
  APP_INCREMENT_RETRY_ATTEMPTS,
  APP_RESET_RETRY_ATTEMPTS,
  APP_SET_RETRY_ATTEMPTS,
  APP_SET_CONTEXT_LIMITS,
}
