import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import OnboardingPage from '../pages/OnboardingPage'
import InstitutionDashboardPage from '../pages/InstitutionDashboardPage'
import { AuthProvider } from '../hooks/useAuth'
import { api, tokenStore } from '../services/api'

describe('Stage 0.5: User Onboarding, Role Selection & Institution Joining', () => {
  beforeEach(() => {
    sessionStorage.clear()
    api.post = vi.fn().mockImplementation((url, data) => {
      if (url.includes('/onboarding/profile')) {
        return Promise.resolve({ data: { status: 'success', ...data } })
      }
      if (url.includes('/onboarding/join-request')) {
        return Promise.resolve({
          data: {
            request_id: 'MREQ-TEST-1234',
            institution_id: data.institution_id,
            requested_role: data.requested_role,
            status: 'PENDING',
            created_at: new Date().toISOString(),
          },
        })
      }
      if (url.includes('/onboarding/complete')) {
        return Promise.resolve({
          data: {
            status: 'completed',
            target_dashboard: data.selected_role === 'student' ? '/me' : '/dashboard',
          },
        })
      }
      return Promise.resolve({ data: {} })
    })

    api.get = vi.fn().mockImplementation((url) => {
      if (url.includes('/onboarding/institutions')) {
        return Promise.resolve({
          data: [
            {
              institution_id: 'INST-001',
              name: 'Delhi Institute of Technology',
              category: 'COLLEGE',
              institution_type: 'ENGINEERING',
              city: 'New Delhi',
              state: 'Delhi',
              is_registered: true,
            },
            {
              institution_id: 'INST-002',
              name: 'Kendriya Vidyalaya No 1',
              category: 'SCHOOL',
              institution_type: 'SECONDARY',
              city: 'Bhubaneswar',
              state: 'Odisha',
              is_registered: false,
            },
          ],
        })
      }
      if (url.includes('/join-requests')) {
        return Promise.resolve({
          data: [
            {
              request_id: 'MREQ-REQ-001',
              user_id: 'OTHER-USER-01',
              user_name: 'Pooja Verma',
              user_email: 'pooja@example.com',
              requested_role: 'student',
              status: 'PENDING',
              role_details: { course_name: 'B.Tech IT' },
            },
            {
              request_id: 'MREQ-SELF-002',
              user_id: 'CURRENT-ADMIN-01',
              user_name: 'Self Admin',
              user_email: 'admin@example.com',
              requested_role: 'teacher',
              status: 'PENDING',
              role_details: { department: 'Physics' },
            },
          ],
        })
      }
      if (url.includes('/corrections/review-tasks')) {
        return Promise.resolve({ data: [] })
      }
      if (url.includes('/students')) {
        return Promise.resolve({ data: [] })
      }
      return Promise.resolve({ data: {} })
    })
  })

  it('renders Step 1 (Welcome) and transitions to Step 2 (Account Purpose)', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <AuthProvider>
          <OnboardingPage />
        </AuthProvider>
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: /Welcome to ChhatraLekha/i })).toBeInTheDocument()
    expect(screen.getByText(/What you will complete in this setup:/i)).toBeInTheDocument()

    const startBtn = screen.getByRole('button', { name: /Get Started/i })
    await user.click(startBtn)

    // Should arrive at Step 2
    expect(screen.getByRole('heading', { name: /Choose Your Account Purpose/i })).toBeInTheDocument()
    expect(screen.getByText('Student')).toBeInTheDocument()
    expect(screen.getByText('Parent / Guardian')).toBeInTheDocument()
    expect(screen.getByText('Teacher / Faculty')).toBeInTheDocument()
    expect(screen.getByText('Institution Administrator')).toBeInTheDocument()

    // Must show security notice regarding privileged administration
    expect(screen.getByText(/Security Governance Notice:/i)).toBeInTheDocument()
    expect(screen.getByText(/University-wide registrars, state education departments, and national administrators must be provisioned through formal institutional onboarding/i)).toBeInTheDocument()
  })

  it('completes basic profile in Step 3 and saves via API', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <AuthProvider>
          <OnboardingPage />
        </AuthProvider>
      </MemoryRouter>,
    )

    // Advance 1 -> 2 -> 3
    await user.click(screen.getByRole('button', { name: /Get Started/i }))
    await user.click(screen.getByRole('button', { name: /Continue/i }))

    expect(screen.getByRole('heading', { name: /Complete Basic Profile/i })).toBeInTheDocument()

    const nameInput = screen.getByPlaceholderText(/e.g., Aarav Sharma/i)
    await user.clear(nameInput)
    await user.type(nameInput, 'Ananya Sen')

    const phoneInput = screen.getByPlaceholderText(/\+91 98765 43210/i)
    await user.type(phoneInput, '+919876543210')

    await user.click(screen.getByRole('button', { name: /Continue/i }))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        '/onboarding/profile',
        expect.objectContaining({
          full_name: 'Ananya Sen',
          phone: '+919876543210',
        }),
      )
    })
  })

  it('searches and selects an institution in Step 4', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <AuthProvider>
          <OnboardingPage />
        </AuthProvider>
      </MemoryRouter>,
    )

    // Advance 1 -> 2 -> 3 -> 4
    await user.click(screen.getByRole('button', { name: /Get Started/i }))
    await user.click(screen.getByRole('button', { name: /Continue/i }))
    const nameInput = screen.getByPlaceholderText(/e.g., Aarav Sharma/i)
    await user.type(nameInput, 'Aarav')
    await user.click(screen.getByRole('button', { name: /Continue/i }))

    // Now in Step 4 (Institution Discovery)
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Discover Educational Institution/i })).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText('Delhi Institute of Technology')).toBeInTheDocument()
      expect(screen.getByText('Kendriya Vidyalaya No 1')).toBeInTheDocument()
    })

    // Click on Delhi Institute of Technology
    await user.click(screen.getByText('Delhi Institute of Technology'))

    // The card is selected
    expect(screen.getByText('Selected')).toBeInTheDocument()

    // Can now continue to Step 5
    await user.click(screen.getByRole('button', { name: /Continue/i }))

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Provide Role Information/i })).toBeInTheDocument()
    })
  })

  it('enforces parent child protection validation in Step 5', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <AuthProvider>
          <OnboardingPage />
        </AuthProvider>
      </MemoryRouter>,
    )

    // Go to step 2 and select Parent
    await user.click(screen.getByRole('button', { name: /Get Started/i }))
    await user.click(screen.getByText('Parent / Guardian'))
    await user.click(screen.getByRole('button', { name: /Continue/i }))

    // Step 3
    const nameInput = screen.getByPlaceholderText(/e.g., Aarav Sharma/i)
    await user.type(nameInput, 'Parent Sunita')
    await user.click(screen.getByRole('button', { name: /Continue/i }))

    // Step 4 (select institution)
    await waitFor(() => screen.getByText('Delhi Institute of Technology'))
    await user.click(screen.getByText('Delhi Institute of Technology'))
    await user.click(screen.getByRole('button', { name: /Continue/i }))

    // Step 5 (Parent details)
    await waitFor(() => {
      expect(screen.getByText(/Child Privacy Protection Policy:/i)).toBeInTheDocument()
    })

    // Attempting to proceed without Student Identifier or DOB gives error
    await user.click(screen.getByRole('button', { name: /Review Application/i }))
    expect(screen.getByRole('alert')).toHaveTextContent(/Both Student Identifier and Date of Birth are mandatory for parent linking/i)
  })

  it('reviews and submits join request to reach Step 7 (Completion)', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <AuthProvider>
          <OnboardingPage />
        </AuthProvider>
      </MemoryRouter>,
    )

    // Step 1
    await user.click(screen.getByRole('button', { name: /Get Started/i }))
    // Step 2 (student)
    await user.click(screen.getByRole('button', { name: /Continue/i }))
    // Step 3 (profile)
    const nameInput = screen.getByPlaceholderText(/e.g., Aarav Sharma/i)
    await user.type(nameInput, 'Aarav')
    await user.click(screen.getByRole('button', { name: /Continue/i }))
    // Step 4 (institution)
    await waitFor(() => screen.getByText('Delhi Institute of Technology'))
    await user.click(screen.getByText('Delhi Institute of Technology'))
    await user.click(screen.getByRole('button', { name: /Continue/i }))
    // Step 5 (details)
    await waitFor(() => screen.getByRole('heading', { name: /Provide Role Information/i }))
    await user.click(screen.getByRole('button', { name: /Review Application/i }))

    // Step 6 (Review)
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Review Your Information/i })).toBeInTheDocument()
      expect(screen.getByText('Delhi Institute of Technology')).toBeInTheDocument()
    })

    // Submit join request
    await user.click(screen.getByRole('button', { name: /Submit Join Request/i }))

    // Step 7 (Completion)
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Join Request Submitted Successfully/i })).toBeInTheDocument()
      expect(screen.getByText('MREQ-TEST-1234')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Go to Workspace/i })).toBeInTheDocument()
    })
  })

  it('renders Institution Membership Requests on InstitutionDashboardPage and prevents self-approval', async () => {
    tokenStore.set({
      access_token: 'fake-token',
      user_id: 'CURRENT-ADMIN-01',
      institution_id: 'INST-001',
      role: 'institution_admin',
    })

    render(
      <MemoryRouter>
        <AuthProvider>
          <InstitutionDashboardPage />
        </AuthProvider>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText(/Membership Join Requests/i)).toBeInTheDocument()
    })

    // Other user's request has enabled Approve/Reject buttons
    await waitFor(() => {
      expect(screen.getByText('Pooja Verma')).toBeInTheDocument()
    })
    const approveButtons = screen.getAllByRole('button', { name: /Approve/i })
    expect(approveButtons.length).toBeGreaterThanOrEqual(1)

    // Current admin's self request has self-approval prohibited
    expect(screen.getByText(/Self-approval prohibited: Another administrator must review your application/i)).toBeInTheDocument()
  })
})
