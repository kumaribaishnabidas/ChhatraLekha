/**
 * The single HTTP client of the EduSynC web frontend.
 *
 * Every request carries the bearer token, and a 401 automatically sends the
 * user back to the sign-in page. The React components never talk to Axios
 * directly - they go through this module, so the token handling lives in one
 * place.
 */
import axios from 'axios'

/**
 * The base URL of the EduSynC API.
 *
 * `VITE_API_URL` is read at BUILD time, so changing it needs a new
 * deployment, not just a restart.
 *
 * When it is unset, the frontend talks to `/api` on its own origin. That
 * only works when the API serves the frontend as well - the Docker Compose
 * setup, or the backend on port 8000 with the Vite dev server proxying
 * `/api`. On a **split Vercel + Render deployment** `VITE_API_URL` must be
 * set to the Render URL, because the Vercel rewrite sends every path -
 * `/api` included - to `index.html`.
 */
/**
 * Normalise a configured API URL.
 *
 * A trailing slash would produce a double slash in every request path, and
 * the surrounding whitespace is easy to pick up from a copy-pasted value.
 */
export function normaliseApiUrl(value) {
  return (value || '').trim().replace(/\/+$/, '')
}

export function apiBaseUrl() {
  return normaliseApiUrl(import.meta.env.VITE_API_URL)
}

const BASE_URL = apiBaseUrl()

if (import.meta.env.PROD && !import.meta.env.VITE_API_URL) {
  // eslint-disable-next-line no-console
  console.error(
    'EduSynC: VITE_API_URL is not set. This build talks to "/api" on its own ' +
      'origin, which only works when the API serves the frontend. On a split ' +
      'deployment set VITE_API_URL to the backend URL and rebuild.',
  )
}

const TOKEN_KEY = 'edusync.token'
const REFRESH_KEY = 'edusync.refresh'
const USER_KEY = 'edusync.user'

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

export const tokenStore = {
  get() {
    try {
      return window.localStorage.getItem(TOKEN_KEY) || ''
    } catch {
      return ''
    }
  },
  getRefresh() {
    try {
      return window.localStorage.getItem(REFRESH_KEY) || ''
    } catch {
      return ''
    }
  },
  getUser() {
    try {
      const raw = window.localStorage.getItem(USER_KEY)
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  },
  set({ access_token, refresh_token, ...user }) {
    try {
      window.localStorage.setItem(TOKEN_KEY, access_token)
      if (refresh_token) window.localStorage.setItem(REFRESH_KEY, refresh_token)
      window.localStorage.setItem(USER_KEY, JSON.stringify(user))
    } catch {
      /* storage unavailable - the session simply will not persist */
    }
  },
  clear() {
    try {
      window.localStorage.removeItem(TOKEN_KEY)
      window.localStorage.removeItem(REFRESH_KEY)
      window.localStorage.removeItem(USER_KEY)
    } catch {
      /* ignore */
    }
  },
}

api.interceptors.request.use((config) => {
  const token = tokenStore.get()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => {
    // A misconfigured deployment answers an API call with the SPA's
    // index.html. That is not JSON, and it is not a crash either - it is a
    // configuration mistake, and it deserves a readable message.
    const contentType = response.headers?.['content-type'] || ''
    if (contentType.includes('text/html') && response.config?.url?.startsWith('/')) {
      const error = new Error(
        'The API returned a web page instead of data. VITE_API_URL is probably ' +
          'not set for this build.',
      )
      error.response = response
      error.config = response.config
      return Promise.reject(error)
    }
    return response
  },
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original?._retried) {
      original._retried = true
      const refresh = tokenStore.getRefresh()
      if (refresh) {
        try {
          const { data } = await axios.post(
            `${BASE_URL}/auth/refresh`,
            { refresh_token: refresh },
            { headers: { 'Content-Type': 'application/json' } },
          )
          tokenStore.set(data)
          original.headers = { ...original.headers, Authorization: `Bearer ${data.access_token}` }
          return api(original)
        } catch {
          tokenStore.clear()
        }
      }
      tokenStore.clear()
      if (window.location.pathname !== '/login') {
        window.location.assign('/login')
      }
    }
    return Promise.reject(error)
  },
)

/** The human-readable message of an Axios error. */
export function errorMessage(error, fallback = 'Something went wrong.') {
  const data = error?.response?.data
  // A misconfigured deployment answers with the SPA's HTML, so `data` is a
  // string and must never be shown to the user.
  const detail = data && typeof data === 'object' ? data.detail : undefined
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) {
    return detail.map((item) => item.msg || JSON.stringify(item)).join(' ')
  }
  if (error?.message) return error.message
  return fallback
}

/** The API prefix, so the components can build absolute links to downloads. */
export const API_BASE = BASE_URL
