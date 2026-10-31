import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import AuthCallbackPage from '../pages/AuthCallbackPage'
import LoginPage from '../pages/LoginPage'
import { AuthProvider } from '../hooks/useAuth'
import { api } from '../services/api'

function renderLogin() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('the Google sign-in button', () => {
  beforeEach(() => {
    api.get = vi.fn(() => Promise.resolve({ data: { enabled: true } }))
    api.post = vi.fn()
  })

  it('is offered when the backend says Google sign-in is configured', async () => {
    renderLogin()
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /sign in with google/i })).toBeInTheDocument(),
    )
  })

  it('is hidden when the backend says Google sign-in is off', async () => {
    api.get = vi.fn(() => Promise.resolve({ data: { enabled: false } }))
    renderLogin()
    await waitFor(() => expect(api.get).toHaveBeenCalled())
    expect(screen.queryByRole('button', { name: /sign in with google/i })).not.toBeInTheDocument()
  })

  it('sends the browser to the backend when it is clicked', async () => {
    const assign = vi.fn()
    delete window.location
    window.location = { assign, pathname: '/login', hash: '' }

    const user = userEvent.setup()
    renderLogin()
    const button = await screen.findByRole('button', { name: /sign in with google/i })
    await user.click(button)

    expect(assign).toHaveBeenCalledWith('/api/auth/google')
  })
})

describe('the Google callback page', () => {
  beforeEach(() => {
    api.get = vi.fn(() => Promise.resolve({ data: { enabled: true } }))
  })

  it('stores the tokens and clears the fragment', async () => {
    window.location.hash =
      '#access_token=abc&refresh_token=def&role=aicte_admin'
    // jsdom does not update window.location when the history is rewritten,
    // so the call itself is what is asserted.
    const replaceState = vi.spyOn(window.history, 'replaceState')

    render(
      <MemoryRouter>
        <AuthProvider>
          <AuthCallbackPage />
        </AuthProvider>
      </MemoryRouter>,
    )

    await waitFor(() =>
      expect(window.localStorage.getItem('chhatralekha.token')).toBe('abc'),
    )
    expect(window.localStorage.getItem('chhatralekha.refresh')).toBe('def')
    expect(replaceState).toHaveBeenCalledWith({}, '', window.location.pathname)
  })

  it('explains a failure instead of crashing', async () => {
    window.location.hash = '#error=Google+refused+the+sign-in'

    render(
      <MemoryRouter>
        <AuthProvider>
          <AuthCallbackPage />
        </AuthProvider>
      </MemoryRouter>,
    )

    await waitFor(() =>
      expect(screen.getByText(/Google refused the sign-in/i)).toBeInTheDocument(),
    )
    expect(window.localStorage.getItem('chhatralekha.token')).toBeNull()
  })
})
