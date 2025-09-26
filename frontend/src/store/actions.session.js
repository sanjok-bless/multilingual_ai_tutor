import { generateUUID } from '@/utils/uuid.js'

// === SESSION MANAGEMENT ACTIONS ===

export const loadFromLocalStorage = ({ commit, dispatch }) => {
  try {
    const storedSessions = {}
    const lastActiveSession = localStorage.getItem('last_active_session')

    for (const key in localStorage) {
      if (key.startsWith('session_')) {
        const sessionData = JSON.parse(localStorage.getItem(key))
        storedSessions[key] = sessionData
      }
    }

    commit('SESSION_SET_STORAGE', storedSessions)

    if (lastActiveSession && storedSessions[lastActiveSession]) {
      commit('SESSION_SET_CURRENT', lastActiveSession)
    } else if (Object.keys(storedSessions).length > 0) {
      const mostRecentSession = Object.keys(storedSessions).reduce(
        (latest, key) => {
          return storedSessions[key].lastActivity >
            storedSessions[latest].lastActivity
            ? key
            : latest
        }
      )
      commit('SESSION_SET_CURRENT', mostRecentSession)
    } else {
      dispatch('createDefaultSession')
    }
  } catch (error) {
    console.error('Error loading sessions from localStorage:', error)
    dispatch('createDefaultSession')
  }
}

export const createDefaultSession = ({ dispatch }) => {
  dispatch('createSession', {
    language: 'english',
    level: 'B2',
    sessionKey: 'session_english_B2',
  })
}

export const createSession = (
  { commit },
  { language, level, sessionKey = null }
) => {
  const sessionId = generateUUID()
  const key = sessionKey || `session_${language}_${level}`

  const sessionData = {
    sessionId,
    language,
    level,
    messages: [],
    lastActivity: Date.now(),
  }

  localStorage.setItem(key, JSON.stringify(sessionData))
  localStorage.setItem('last_active_session', key)

  commit('SESSION_ADD', { sessionKey: key, sessionData })
  commit('SESSION_SET_CURRENT', key)

  return { sessionKey: key, sessionData }
}

export const switchSession = ({ commit, state }, sessionKey) => {
  if (state.sessions.sessionStorage[sessionKey]) {
    commit('SESSION_SET_CURRENT', sessionKey)

    localStorage.setItem('last_active_session', sessionKey)
    const sessionData = state.sessions.sessionStorage[sessionKey]
    localStorage.setItem(sessionKey, JSON.stringify(sessionData))
  }
}

export const getOrCreateSession = (
  { state, dispatch },
  { language, level }
) => {
  const sessionKey = `session_${language}_${level}`

  if (state.sessions.sessionStorage[sessionKey]) {
    dispatch('switchSession', sessionKey)
    return {
      sessionKey,
      sessionData: state.sessions.sessionStorage[sessionKey],
    }
  } else {
    return dispatch('createSession', { language, level, sessionKey })
  }
}

export const updateSessionInStorage = ({ state }, sessionKey) => {
  if (state.sessions.sessionStorage[sessionKey]) {
    const sessionData = state.sessions.sessionStorage[sessionKey]
    localStorage.setItem(sessionKey, JSON.stringify(sessionData))
  }
}

export const addMessageToSessionWithStorage = (
  { commit, dispatch },
  { sessionKey, message }
) => {
  if (!sessionKey || !message) {
    throw new Error(
      'Session key and message are required for addMessageToSessionWithStorage'
    )
  }

  commit('SESSION_ADD_MESSAGE', { sessionKey, message })
  dispatch('updateSessionInStorage', sessionKey)
}
