import { describe, expect, it } from 'vitest'

import { apiBaseUrl, errorMessage, normaliseApiUrl, tokenStore } from '../services/api'

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
})
