import { createStore } from 'vuex'
import chat from './modules/chat.js'
import user from './modules/user.js'
import session from './modules/session.js'

export default createStore({
  modules: {
    chat,
    user,
    session,
  },
  strict: import.meta.env.MODE !== 'production',
})
