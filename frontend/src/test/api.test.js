import { describe, expect, it } from 'vitest'

import { errorMessage, tokenStore } from '../services/api'

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
