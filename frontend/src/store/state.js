// === DOMAIN CONSTANTS ===
const LEVEL_MAPPING = {
  beginner: 'A2',
  intermediate: 'B2',
  advanced: 'C2',
}

const REVERSE_LEVEL_MAPPING = {
  A2: 'beginner',
  B2: 'intermediate',
  C2: 'advanced',
}

export default () => ({
  // === USER DOMAIN ===
  user: {
    selectedLanguage: null,
    defaultSelectedLanguage: 'english',
    selectedLevel: 'B2',
    availableLanguages: ['english'],
    levelMapping: LEVEL_MAPPING,
  },

  // === SESSION DOMAIN ===
  sessions: {
    currentSessionKey: null,
    sessionStorage: {},
    lastActiveSession: null,
    isInitializingSession: false,
  },

  // === CHAT DOMAIN ===
  chat: {
    currentMessages: [],
    currentCorrections: [],
    isLoading: false,
  },

  // === APP DOMAIN ===
  app: {
    isConnected: null,
    lastSuccessfulCall: null,
    currentError: null,
    lastErrorEndpoint: null,
    isRetrying: false,
    retryAttempts: 0,
    maxRetries: 3,
    contextChatLimit: 40,
    contextStartLimit: 20,
  },
})

// === LEVEL MAPPING UTILITIES ===
export { LEVEL_MAPPING, REVERSE_LEVEL_MAPPING }
