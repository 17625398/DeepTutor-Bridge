import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import { i18n } from './i18n'
import App from './App.vue'
import './styles/global.scss'

// Apply theme classes before mount to prevent FOUC (Flash of Unstyled Content)
const savedBrightness = localStorage.getItem('hermes_brightness') || 'system'
const savedStyle = localStorage.getItem('hermes_style') || 'ink'

// Resolve dark mode
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
const isDark = savedBrightness === 'dark' || (savedBrightness === 'system' && prefersDark)

// Resolve style
const isComic = savedStyle === 'comic'

// Apply classes to prevent FOUC
if (isDark) {
  document.documentElement.classList.add('dark')
}
if (isComic) {
  document.documentElement.classList.add('comic')
}

// Read token from URL BEFORE router initializes (hash router strips params)
const urlParams = new URLSearchParams(window.location.search)
const hashQuery = window.location.hash.split('?')[1]
const urlToken = urlParams.get('token') || (hashQuery ? new URLSearchParams(hashQuery).get('token') : null)
if (urlToken) {
  ;(window as any).__LOGIN_TOKEN__ = urlToken
}

// Auto-initialize localStorage config in dev mode
if (import.meta.env.DEV) {
  // Set default server URL for WebSocket connections (local Web UI backend) only if not already set
  if (!localStorage.getItem('hermes_server_url')) {
    localStorage.setItem('hermes_server_url', 'http://127.0.0.1:8648')
  }
  // Set default auth token (matches .env AUTH_TOKEN) only if not already set
  if (!localStorage.getItem('hermes_api_key')) {
    localStorage.setItem('hermes_api_key', '123456')
  }
  // Set default profile
  if (!localStorage.getItem('hermes_active_profile_name')) {
    localStorage.setItem('hermes_active_profile_name', 'default')
  }
}

const app = createApp(App)
app.use(createPinia())
app.use(i18n)
app.use(router)
app.mount('#app')
