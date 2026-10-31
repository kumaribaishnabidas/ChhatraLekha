import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

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

describe('LoginPage', () => {
  beforeEach(() => {
    api.post = vi.fn()
  })

  it('renders the sign-in form', () => {
    renderLogin()
    expect(screen.getByLabelText(/e-mail address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('signs in and stores the token', async () => {
    api.post.mockResolvedValue({
      data: {
        access_token: 'token-123',
        refresh_token: 'refresh-123',
        role: 'aicte_admin',
        user_id: 'USR-1',
        display_name: 'Aicte Admin',
        institution_id: null,
      },
    })

    const user = userEvent.setup()
    renderLogin()
    await user.type(screen.getByLabelText(/e-mail address/i), 'aicte@chhatralekha.test')
    await user.type(screen.getByLabelText(/password/i), 'Test@1234')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => expect(api.post).toHaveBeenCalled())
    expect(api.post).toHaveBeenCalledWith('/auth/login', {
      email: 'aicte@chhatralekha.test',
      password: 'Test@1234',
    })
    await waitFor(() =>
      expect(window.localStorage.getItem('chhatralekha.token')).toBe('token-123'),
    )
  })

  it('shows the server error message', async () => {
    api.post.mockRejectedValue({
      response: { data: { detail: 'Invalid e-mail address or password.' } },
    })

    const user = userEvent.setup()
    renderLogin()
    await user.type(screen.getByLabelText(/e-mail address/i), 'aicte@chhatralekha.test')
    await user.type(screen.getByLabelText(/password/i), 'wrong')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent('Invalid e-mail address or password.'),
    )
  })
})
