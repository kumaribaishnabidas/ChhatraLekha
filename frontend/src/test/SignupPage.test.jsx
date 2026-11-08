import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import SignupPage from '../pages/SignupPage'
import { AuthProvider } from '../hooks/useAuth'
import { api } from '../services/api'

function renderSignup() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <SignupPage />
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('SignupPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.post = vi.fn()
  })

  it('renders all form controls and role options', () => {
    renderSignup()
    expect(screen.getByText(/Get Started with ChhatraLekha/i)).toBeInTheDocument()
    expect(screen.getByText('Student')).toBeInTheDocument()
    expect(screen.getByText('Parent / Guardian')).toBeInTheDocument()
    expect(screen.getByText('Teacher / Faculty')).toBeInTheDocument()
    expect(screen.getByText('Institution Admin')).toBeInTheDocument()
    expect(screen.getByLabelText(/Full Legal Name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/E-mail address/i)).toBeInTheDocument()
    expect(screen.getByLabelText('Password', { exact: true })).toBeInTheDocument()
    expect(screen.getByLabelText('Confirm Password', { exact: true })).toBeInTheDocument()
    expect(screen.getByLabelText(/Terms of Service/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Complete Registration/i })).toBeInTheDocument()
  })

  it('shows error if terms and conditions are not accepted', async () => {
    const user = userEvent.setup()
    renderSignup()

    fireEvent.change(screen.getByLabelText(/Full Legal Name/i), { target: { value: 'Aarav Sharma' } })
    fireEvent.change(screen.getByLabelText(/E-mail address/i), { target: { value: 'aarav@example.com' } })
    fireEvent.change(screen.getByLabelText('Password', { exact: true }), { target: { value: 'Password123!' } })
    fireEvent.change(screen.getByLabelText('Confirm Password', { exact: true }), { target: { value: 'Password123!' } })

    // Do NOT check terms
    await user.click(screen.getByRole('button', { name: /Complete Registration/i }))

    expect(screen.getByRole('alert')).toHaveTextContent(/You must agree to the Terms of Service/i)
    expect(api.post).not.toHaveBeenCalled()
  })

  it('submits registration successfully and displays success message', async () => {
    api.post.mockResolvedValue({
      data: {
        status: 'success',
        message: 'Account created successfully! You may now sign in.',
        user_id: 'usr_abc123',
        email: 'aarav.sharma@example.edu.in',
        role: 'student',
        requires_approval: false,
      },
    })

    const user = userEvent.setup()
    renderSignup()

    fireEvent.change(screen.getByLabelText(/Full Legal Name/i), { target: { value: 'Aarav Sharma' } })
    fireEvent.change(screen.getByLabelText(/E-mail address/i), { target: { value: 'aarav.sharma@example.edu.in' } })
    fireEvent.change(screen.getByLabelText('Password', { exact: true }), { target: { value: 'Password123!' } })
    fireEvent.change(screen.getByLabelText('Confirm Password', { exact: true }), { target: { value: 'Password123!' } })
    await user.click(screen.getByLabelText(/Terms of Service/i))

    await user.click(screen.getByRole('button', { name: /Complete Registration/i }))

    await waitFor(() => expect(api.post).toHaveBeenCalled())
    expect(api.post).toHaveBeenCalledWith('/auth/register', {
      email: 'aarav.sharma@example.edu.in',
      password: 'Password123!',
      full_name: 'Aarav Sharma',
      role: 'student',
      identifier: undefined,
    })

    await waitFor(() => {
      expect(screen.getByRole('status')).toHaveTextContent(/Account created successfully/i)
    })
  })

  it('handles server rejection and shows error banner', async () => {
    api.post.mockRejectedValue({
      response: {
        status: 400,
        data: {
          detail: 'Unable to complete registration. If an account already exists with this email, please sign in or reset your password.',
        },
      },
    })

    const user = userEvent.setup()
    renderSignup()

    fireEvent.change(screen.getByLabelText(/Full Legal Name/i), { target: { value: 'Aarav Sharma' } })
    fireEvent.change(screen.getByLabelText(/E-mail address/i), { target: { value: 'existing@example.com' } })
    fireEvent.change(screen.getByLabelText('Password', { exact: true }), { target: { value: 'Password123!' } })
    fireEvent.change(screen.getByLabelText('Confirm Password', { exact: true }), { target: { value: 'Password123!' } })
    await user.click(screen.getByLabelText(/Terms of Service/i))

    await user.click(screen.getByRole('button', { name: /Complete Registration/i }))

    await waitFor(() => expect(api.post).toHaveBeenCalled())
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/Unable to complete registration/i)
    })
  })

  it('submits institution admin registration with approval notice', async () => {
    api.post.mockResolvedValue({
      data: {
        status: 'success',
        message: 'Registration successful. Institutional administrator access requires review before administrative privileges are granted.',
        user_id: 'usr_admin456',
        email: 'principal@school.edu.in',
        role: 'pending',
        requires_approval: true,
      },
    })

    const user = userEvent.setup()
    renderSignup()

    // Select Institution Admin role
    await user.click(screen.getByRole('button', { name: /Institution Admin/i }))

    fireEvent.change(screen.getByLabelText(/Full Legal Name/i), { target: { value: 'Dr. Ramesh Verma' } })
    fireEvent.change(screen.getByLabelText(/E-mail address/i), { target: { value: 'principal@school.edu.in' } })
    fireEvent.change(screen.getByLabelText(/Institution \/ Department Name/i), { target: { value: 'Delhi Public School' } })
    fireEvent.change(screen.getByLabelText('Password', { exact: true }), { target: { value: 'Password123!' } })
    fireEvent.change(screen.getByLabelText('Confirm Password', { exact: true }), { target: { value: 'Password123!' } })
    await user.click(screen.getByLabelText(/Terms of Service/i))

    await user.click(screen.getByRole('button', { name: /Complete Registration/i }))

    await waitFor(() => expect(api.post).toHaveBeenCalled())
    expect(api.post).toHaveBeenCalledWith('/auth/register', {
      email: 'principal@school.edu.in',
      password: 'Password123!',
      full_name: 'Dr. Ramesh Verma',
      role: 'institution_admin',
      identifier: 'Delhi Public School',
    })

    await waitFor(() => {
      expect(screen.getByRole('status')).toHaveTextContent(/Institutional administrator access requires review/i)
    })
  })
})
