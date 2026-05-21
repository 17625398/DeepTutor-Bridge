import router from '@/router'

const DEFAULT_BASE_URL = ''

export function getBaseUrl(): string {
  // 获取 localStorage 中的配置
  const storedUrl = localStorage.getItem('hermes_server_url')
  
  // 在开发模式下：通过 Vite 代理避免 CORS 问题
  if (import.meta.env.DEV) {
    return ''
  }
  
  // 生产模式下：使用 localStorage 中的配置或默认值
  return storedUrl || DEFAULT_BASE_URL
}

export function getBaseUrlValue(): string {
  // 返回 localStorage 中存储的服务器地址（用于显示）
  return localStorage.getItem('hermes_server_url') || ''
}

export function getApiKey(): string {
  return localStorage.getItem('hermes_api_key') || ''
}

export function setServerUrl(url: string) {
  localStorage.setItem('hermes_server_url', url)
}

export function setApiKey(key: string) {
  localStorage.setItem('hermes_api_key', key)
}

export function clearApiKey() {
  localStorage.removeItem('hermes_api_key')
}

export function hasApiKey(): boolean {
  return !!getApiKey()
}

/**
 * Get current active profile name.
 * Reads from store first (authoritative source), falls back to localStorage.
 */
function getActiveProfileName(): string | null {
  try {
    // Dynamic import to avoid circular dependency
    const { useProfilesStore } = require('@/stores/hermes/profiles')
    const store = useProfilesStore()
    // Store is the source of truth - it's updated from /api/hermes/profiles
    return store.activeProfileName
  } catch {
    // Fallback to localStorage if store is not available (e.g., during initialization)
    return localStorage.getItem('hermes_active_profile_name')
  }
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const base = getBaseUrl()
  const url = `${base}${path}`
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers as Record<string, string>,
  }

  const apiKey = getApiKey()
  if (apiKey) {
    headers['Authorization'] = `Bearer ${apiKey}`
  }

  // Inject active profile header for proxied gateway requests
  const profileName = getActiveProfileName()
  if (profileName && profileName !== 'default') {
    headers['X-Hermes-Profile'] = profileName
  }

  const res = await fetch(url, { ...options, headers })

  // Global 401 handler — only redirect to login for local BFF endpoints
  // Proxied gateway requests should not trigger logout
  const isLocalBff = !path.startsWith('/api/hermes/v1/') &&
    !path.startsWith('/api/hermes/jobs') &&
    !path.startsWith('/api/hermes/skills')

  if (res.status === 401 && isLocalBff) {
    clearApiKey()
    if (router.currentRoute.value.name !== 'login') {
      router.replace({ name: 'login' })
    }
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`API Error ${res.status}: ${text || res.statusText}`)
  }

  return res.json()
}
