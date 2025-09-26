import { LEVEL_MAPPING } from './state.js'

// === INITIALIZATION ORCHESTRATION ACTIONS ===

export const loadAvailableLanguages = async ({
  commit,
  dispatch,
  getters,
  state,
}) => {
  try {
    const apiService = await import('@/services/api.js')
    const languages = await apiService.default.getSupportedLanguages()

    commit('USER_SET_AVAILABLE_LANGUAGES', languages)

    const wasRetry = state.app.lastErrorEndpoint === '/languages'

    commit('APP_SET_SUCCESS', '/languages')
    commit('APP_RESET_RETRY_ATTEMPTS')

    if (languages.length > 1) {
      const lastActiveSession = getters.lastActiveSession
      if (lastActiveSession?.language) {
        commit('USER_SET_LANGUAGE', lastActiveSession.language)
        commit('USER_SET_LEVEL', lastActiveSession.level)
      } else {
        commit('USER_SET_LANGUAGE', state.user.defaultSelectedLanguage)
      }
    }

    if (wasRetry && languages.length > 1) {
      setTimeout(async () => {
        try {
          await dispatch('continueInitializationAfterLanguages')
        } catch (error) {
          console.error(
            'Failed to continue initialization after /languages retry:',
            error
          )
        }
      }, 0)
    }

    return { success: true, languages }
  } catch (error) {
    console.error('Error loading available languages:', error)

    commit('APP_SET_ERROR', {
      message: error.message || 'Unable to load language options',
      isRetryable: true,
      timestamp: Date.now(),
      endpoint: '/languages',
    })

    commit('USER_SET_AVAILABLE_LANGUAGES', ['english'])
    return { success: false, languages: ['english'] }
  }
}

export const selectLanguage = ({ commit, dispatch, state }, language) => {
  commit('USER_SET_LANGUAGE', language)
  const level = state.user.selectedLevel
  dispatch('getOrCreateSession', { language, level })
}

export const selectLevel = ({ commit, dispatch, state }, level) => {
  commit('USER_SET_LEVEL', level)
  const language = state.user.selectedLanguage
  const cefrLevel = LEVEL_MAPPING[level] || level
  dispatch('getOrCreateSession', { language, level: cefrLevel })
}

export const updateFromCurrentSession = ({ commit, getters }) => {
  const currentSession = getters.currentSession
  if (currentSession && getters.isInitialized) {
    commit('USER_SET_LANGUAGE', currentSession.language)
    commit('USER_SET_LEVEL', currentSession.level)
  }
}

export const initializeDefaults = ({ commit, dispatch, getters }) => {
  if (!getters.hasAnySessions) {
    commit('USER_SET_LEVEL', 'B2')
  } else {
    dispatch('updateFromCurrentSession')
  }
}

export const initializeSessionWithLock = async ({
  state,
  commit,
  dispatch,
  getters,
}) => {
  if (state.sessions.isInitializingSession) {
    return
  }

  if (!state.app.isConnected) {
    console.log('Skipping session initialization - API not connected')
    return
  }

  try {
    commit('SESSION_SET_INITIALIZING', true)

    const currentSession = getters.currentSession
    if (!currentSession) return

    const { needsDailyStart } = await import('@/utils/dateUtils.js')
    const shouldGetStartMessage =
      currentSession.messages.length === 0 || needsDailyStart(currentSession)

    const lastMessage =
      currentSession.messages.length > 0
        ? currentSession.messages[currentSession.messages.length - 1]
        : null

    const shouldResendLastMessage =
      lastMessage &&
      lastMessage.type === 'user' &&
      !needsDailyStart(currentSession)

    if (shouldResendLastMessage) {
      await dispatch('sendMessage', { content: lastMessage.content })
    } else if (shouldGetStartMessage) {
      await dispatch('requestStartMessage')
    } else {
      const lastAiMessage = currentSession.messages
        .slice()
        .reverse()
        .find(msg => msg.type === 'ai')
      if (lastAiMessage && lastAiMessage.corrections) {
        commit('CHAT_UPDATE_CURRENT_CORRECTIONS', lastAiMessage.corrections)
      }
    }
  } finally {
    commit('SESSION_SET_INITIALIZING', false)
  }
}

export const continueInitializationAfterLanguages = async ({ dispatch }) => {
  try {
    await dispatch('initializeDefaults')
    await dispatch('loadSessionMessages')
    await dispatch('initializeSessionWithLock')
    console.log('Initialization resumed and completed after /languages retry')
  } catch (error) {
    console.error(
      'Error continuing initialization after /languages retry:',
      error
    )
  }
}
