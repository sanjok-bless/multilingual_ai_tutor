// === CHAT WORKFLOW ACTIONS ===

import { transformMessagesForContext } from '@/utils/messageTransform.js'

export const sendMessage = async (
  { commit, dispatch, getters, state },
  { content }
) => {
  const currentSession = getters.currentSession
  if (!currentSession) {
    commit('APP_SET_ERROR', {
      message: 'No active session. Please select a language and level.',
      isRetryable: false,
    })
    return
  }

  const userMessage = {
    type: 'user',
    content: content.trim(),
    timestamp: Date.now(),
  }

  try {
    commit('CHAT_SET_LOADING', true)
    commit('APP_CLEAR_ERROR')

    if (!state.app.isRetrying) {
      const sessionKey = state.sessions.currentSessionKey
      await dispatch('addMessageToSessionWithStorage', {
        sessionKey,
        message: userMessage,
      })
    }

    const apiService = await import('@/services/api.js')

    // Transform messages to minimal payload (type + content only)
    const contextMessages = transformMessagesForContext(
      currentSession.messages || [],
      state.app.contextChatLimit
    )

    const response = await apiService.default.sendChatMessage({
      session_id: currentSession.sessionId,
      message: content.trim(),
      language: currentSession.language,
      level: currentSession.level,
      context_messages: contextMessages,
    })

    commit('APP_SET_SUCCESS', '/chat')
    commit('APP_RESET_RETRY_ATTEMPTS')
    commit('APP_CLEAR_ERROR')

    const aiMessage = {
      type: 'ai',
      ai_response: response.ai_response,
      next_phrase: response.next_phrase,
      corrections: response.corrections || [],
      tokens_used: response.tokens_used || 0,
      timestamp: Date.now(),
    }

    const sessionKey = state.sessions.currentSessionKey
    await dispatch('addMessageToSessionWithStorage', {
      sessionKey,
      message: aiMessage,
    })
    commit('CHAT_UPDATE_CURRENT_CORRECTIONS', response.corrections)
  } catch (error) {
    console.error('Error sending message:', error)

    commit('APP_SET_ERROR', {
      message: 'Sorry, I had trouble sending your message. Please try again.',
      isRetryable: true,
      originalContent: content,
      timestamp: Date.now(),
      endpoint: '/chat',
    })
  } finally {
    commit('CHAT_SET_LOADING', false)
  }
}

export const retryLastMessage = async ({ state, commit, dispatch }) => {
  if (
    state.app.currentError &&
    state.app.currentError.isRetryable &&
    state.app.currentError.originalContent &&
    state.app.retryAttempts < state.app.maxRetries
  ) {
    commit('APP_INCREMENT_RETRY_ATTEMPTS')
    commit('APP_SET_RETRYING', true)
    try {
      await dispatch('sendMessage', {
        content: state.app.currentError.originalContent,
      })
    } catch (retryError) {
      console.error('Retry failed:', retryError)
    } finally {
      commit('APP_SET_RETRYING', false)
    }
  }
}

export const requestStartMessage = async ({
  commit,
  dispatch,
  getters,
  state,
}) => {
  const currentSession = getters.currentSession
  if (!currentSession) return

  try {
    commit('CHAT_SET_LOADING', true)
    commit('APP_CLEAR_ERROR')

    const apiService = await import('@/services/api.js')

    // Transform messages to minimal payload (type + content only)
    const contextMessages = transformMessagesForContext(
      currentSession.messages || [],
      state.app.contextStartLimit
    )

    const response = await apiService.default.requestStartMessage({
      session_id: currentSession.sessionId,
      language: currentSession.language,
      level: currentSession.level,
      context_messages: contextMessages,
    })

    commit('APP_SET_SUCCESS', '/start')
    commit('APP_RESET_RETRY_ATTEMPTS')
    commit('APP_CLEAR_ERROR')

    const startMessage = {
      type: 'ai',
      content: response.message,
      ai_response: response.start_message,
      next_phrase: response.next_phrase || null,
      corrections: [],
      tokens_used: response.tokens_used || 0,
      timestamp: Date.now(),
      isStartMessage: true,
    }

    const sessionKey = state.sessions.currentSessionKey
    await dispatch('addMessageToSessionWithStorage', {
      sessionKey,
      message: startMessage,
    })
  } catch (error) {
    console.error('Error getting start message:', error)

    commit('APP_SET_ERROR', {
      message: 'Sorry, I had trouble generating a greeting. Please try again.',
      isRetryable: true,
      timestamp: Date.now(),
      endpoint: '/start',
    })
  } finally {
    commit('CHAT_SET_LOADING', false)
  }
}

export const loadSessionMessages = ({ commit, getters }) => {
  const currentSession = getters.currentSession
  if (currentSession && currentSession.messages) {
    const lastAiMessage = currentSession.messages
      .slice()
      .reverse()
      .find(msg => msg.type === 'ai' && msg.corrections)
    if (lastAiMessage) {
      commit('CHAT_UPDATE_CURRENT_CORRECTIONS', lastAiMessage.corrections)
    }
  }
}

export const retryConnection = async ({ dispatch, state, commit }) => {
  if (state.app.retryAttempts >= state.app.maxRetries) {
    return
  }

  const lastEndpoint = state.app.lastErrorEndpoint
  if (lastEndpoint === '/config') {
    commit('APP_INCREMENT_RETRY_ATTEMPTS')
    dispatch('loadAvailableLanguages')
  } else if (lastEndpoint === '/start') {
    commit('APP_INCREMENT_RETRY_ATTEMPTS')
    dispatch('requestStartMessage')
  } else if (lastEndpoint === '/chat') {
    dispatch('retryLastMessage')
  }
}
