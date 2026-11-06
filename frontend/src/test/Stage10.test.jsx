import { render, screen } from '@testing-library/react'
import axios from 'axios'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import LoginPage from '../pages/LoginPage'
import {
  api,
  logoutUser,
  refreshAccessToken,
  tokenStore,
} from '../services/api'

describe('Stage 0.10: Secure Authentication Session Lifecycle Frontend', () => {
  beforeEach(() => {
    tokenStore.clear()
    vi.restoreAllMocks()
    api.post = vi.fn().mockResolvedValue({ data: { status: 'success' } })
    api.get = vi.fn().mockResolvedValue({ data: { enabled: false } })
  })

  it('refreshAccessToken de-duplicates concurrent refresh invocations', async () => {
    tokenStore.set({
      access_token: 'old_access',
      refresh_token: 'old_refresh',
      user_id: 'USR-1',
      role: 'student',
    })

    let resolvePost
    const postPromise = new Promise((resolve) => {
      resolvePost = resolve
    })

    const axiosSpy = vi.spyOn(axios, 'post').mockReturnValue(postPromise)

    // Trigger two simultaneous refresh calls
    const p1 = refreshAccessToken()
    const p2 = refreshAccessToken()

    // Assert that only ONE axios.post was made
    expect(axiosSpy).toHaveBeenCalledTimes(1)

    // Resolve the single mock network call
    resolvePost({
      data: {
        access_token: 'rotated_access_token',
        refresh_token: 'rotated_refresh_token',
        role: 'student',
        user_id: 'USR-1',
      },
    })

    const [res1, res2] = await Promise.all([p1, p2])

    expect(res1).toBe('rotated_access_token')
    expect(res2).toBe('rotated_access_token')
    expect(tokenStore.get()).toBe('rotated_access_token')
    expect(tokenStore.getRefresh()).toBe('rotated_refresh_token')
  })

  it('logoutUser dispatches POST /auth/logout with refresh_token and clears local tokenStore', async () => {
    tokenStore.set({
      access_token: 'active_access',
      refresh_token: 'active_refresh',
      user_id: 'USR-STU-01',
      role: 'student',
    })

    expect(tokenStore.get()).toBe('active_access')
    expect(tokenStore.getRefresh()).toBe('active_refresh')

    await logoutUser(false)

    expect(api.post).toHaveBeenCalledWith('/auth/logout', {
      refresh_token: 'active_refresh',
      all_sessions: false,
    })
    expect(tokenStore.get()).toBe('')
    expect(tokenStore.getRefresh()).toBe('')
    expect(tokenStore.getUser()).toBeNull()
  })

  it('LoginPage renders clear user-facing notice on session expiration query parameter', () => {
    render(
      <MemoryRouter initialEntries={['/login?expired=1']}>
        <LoginPage />
      </MemoryRouter>,
    )

    expect(screen.getByText(/Your session has expired. Please sign in again./i)).toBeInTheDocument()
  })
})
