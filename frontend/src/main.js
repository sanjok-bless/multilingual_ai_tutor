import { createApp } from 'vue'
import App from './App.vue'
import store from './store'
import './assets/main.css'

const app = createApp(App)

// Enable Vue DevTools in development
if (import.meta.env.DEV) {
  app.config.devtools = true
  app.config.performance = true
}

app.use(store)

app.mount('#app')
