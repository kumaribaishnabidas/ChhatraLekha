import { describe, expect, it } from 'vitest'

import { api, apiBaseUrl, apiOrigin, errorMessage, normaliseApiUrl, tokenStore } from '../services/api'

describe('errorMessage', () => {
  it('uses a string detail', () => {
    expect(errorMessage({ response: { data: { detail: 'Nope.' } } })).toBe('Nope.')
  })

  it('joins the pydantic validation details', () => {
    const error = {
      response: { data: { detail: [{ msg: 'field required' }, { msg: 'bad value' }] } },
    }
    expect(errorMessage(error)).toBe('field required bad value')
  })

  it('falls back to a generic message', () => {
    expect(errorMessage({}, 'Fallback.')).toBe('Fallback.')
  })
})

describe('tokenStore', () => {
  it('stores and reads the token, the refresh token and the user', () => {
    tokenStore.set({
      access_token: 'abc',
      refresh_token: 'def',
      user_id: 'USR-1',
      role: 'aicte_admin',
    })
    expect(tokenStore.get()).toBe('abc')
    expect(tokenStore.getRefresh()).toBe('def')
    expect(tokenStore.getUser().role).toBe('aicte_admin')
  })

  it('clears everything', () => {
    tokenStore.set({ access_token: 'abc', refresh_token: 'def' })
    tokenStore.clear()
    expect(tokenStore.get()).toBe('')
    expect(tokenStore.getRefresh()).toBe('')
    expect(tokenStore.getUser()).toBeNull()
  })
})

describe('the API base URL', () => {
  it('strips a trailing slash from the configured URL', () => {
    expect(normaliseApiUrl('https://edusync-api.onrender.com/')).toBe(
      'https://edusync-api.onrender.com',
    )
    expect(normaliseApiUrl('https://edusync-api.onrender.com///')).toBe(
      'https://edusync-api.onrender.com',
    )
  })

  it('is an empty string when the URL is unset', () => {
    expect(normaliseApiUrl(undefined)).toBe('')
    expect(normaliseApiUrl('')).toBe('')
    expect(normaliseApiUrl('   ')).toBe('')
  })

  it('trims the surrounding whitespace', () => {
    expect(normaliseApiUrl('  https://edusync-api.onrender.com  ')).toBe(
      'https://edusync-api.onrender.com',
    )
  })

  it('leaves a URL without a trailing slash alone', () => {
    expect(normaliseApiUrl('https://edusync-api.onrender.com')).toBe(
      'https://edusync-api.onrender.com',
    )
  })

  it('never ends with a slash', () => {
    expect(apiBaseUrl().endsWith('/')).toBe(false)
  })

  it('keeps the /api prefix when no URL is configured', () => {
    // The API lives under /api. With no VITE_API_URL the frontend talks to
    // /api on its own origin.
    expect(apiOrigin()).toBe('')
    expect(apiBaseUrl()).toBe('/api')
  })

  it('keeps the /api prefix on a configured origin too', () => {
    // Axios only prefixes baseURL onto a *relative* path, and every path in
    // this app starts with a slash. If /api were left out of the base URL it
    // would be silently dropped from every request.
    expect(apiBaseUrl()).toContain('/api')
  })

  it('builds the sign-in URL with the /api prefix', () => {
    // The regression that made the sign-in form fail: the request went to
    // /auth/login instead of /api/auth/login and came back 405.
    expect(api.getUri({ url: '/auth/login' })).toBe('/api/auth/login')
    expect(api.getUri({ url: '/students' })).toBe('/api/students')
    expect(api.getUri({ url: '/verify/token/abc' })).toBe('/api/verify/token/abc')
  })
})
