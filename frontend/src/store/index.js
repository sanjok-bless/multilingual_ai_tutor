import { createStore } from 'vuex'
import state from './state.js'
import getters from './getters.js'
import mutations from './mutations.js'
import * as sessionActions from './actions.session.js'
import * as chatActions from './actions.chat.js'
import * as initializationActions from './actions.initialization.js'

const actions = {
  // Session Actions
  ...sessionActions,

  // Chat Actions
  ...chatActions,

  // Initialization Actions
  ...initializationActions,
}

export default createStore({
  state,
  getters,
  mutations,
  actions,
  strict: import.meta.env.MODE !== 'production',
})
