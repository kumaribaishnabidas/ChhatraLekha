import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import LandingPage from '../pages/LandingPage'
import SignupPage from '../pages/SignupPage'
import AccessibilityPage from '../pages/AccessibilityPage'
import LoginPage from '../pages/LoginPage'
import { AuthProvider } from '../hooks/useAuth'
import { api } from '../services/api'

describe('Stage 0.4: Landing Page & Authentication UI', () => {
  beforeEach(() => {
    api.post = vi.fn()
    api.get = vi.fn().mockResolvedValue({ data: { enabled: false } })
  })

  it('renders LandingPage with all required sections A through I', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    )

    // Section B: Hero & Preview
    expect(screen.getByText(/One trusted record for every student/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Verify a credential/i })).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: /Explore Demo/i }).length).toBeGreaterThanOrEqual(1)

    // Section C: Trust & Social Proof
    expect(screen.getByText(/Engineered for Integrity and National Scale/i)).toBeInTheDocument()
    expect(screen.getByText(/Opaque Verification/i)).toBeInTheDocument()
    expect(screen.getAllByText(/22 Languages/i).length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/High-Entropy QR Seals/i)).toBeInTheDocument()
    expect(screen.getByText(/Immutable Audit Trail/i)).toBeInTheDocument()

    // Section D: Feature Section
    expect(screen.getByText(/Comprehensive Platform Features/i)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Student Dashboard' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Academic Records' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Attendance & Timetable' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Assignments & Resources' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Exams & Results' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Notifications & Bulletins' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Parent / Guardian Access' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Teacher & Faculty Tools' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Institution Administration' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Multilingual & Voice Experience' })).toBeInTheDocument()

    // Section E: Benefits Section
    expect(screen.getByText(/Tailored Benefits for Every Stakeholder/i)).toBeInTheDocument()

    // Section F: Product Preview
    expect(screen.getByText(/Interactive Product Preview/i)).toBeInTheDocument()
    expect(screen.getByText(/Vidya Vikas Institute of Technology/i)).toBeInTheDocument()

    // Section G: Testimonials (Sample Demonstrative)
    expect(screen.getByText(/Sample Demonstrative Personas/i)).toBeInTheDocument()
    expect(screen.getByText(/Rohan Patel \(Sample Student\)/i)).toBeInTheDocument()

    // Section H: FAQ Section
    expect(screen.getByText(/Frequently Asked Questions/i)).toBeInTheDocument()
    expect(screen.getByText(/What is ChhatraLekha\?/i)).toBeInTheDocument()
    expect(screen.getByText(/How does student verification work\?/i)).toBeInTheDocument()

    // Section I: Final CTA
    expect(screen.getByText(/Ready to Experience ChhatraLekha\?/i)).toBeInTheDocument()
  })

  it('switches device preview views in the Hero section', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    )

    // Initially Student tab is active
    expect(screen.getByText(/Digital APAAR Card/i)).toBeInTheDocument()

    // Switch to Parent tab inside phone preview
    const parentTabBtn = screen.getByRole('button', { name: 'Parent' })
    await user.click(parentTabBtn)
    expect(screen.getByText(/Linked Student/i)).toBeInTheDocument()

    // Switch to Teacher tab inside phone preview
    const teacherTabBtn = screen.getByRole('button', { name: 'Teacher' })
    await user.click(teacherTabBtn)
    expect(screen.getByText(/Active Session/i)).toBeInTheDocument()
    expect(screen.getByText(/CS302 - Data Structures/i)).toBeInTheDocument()
  })

  it('expands FAQ accordion items on click', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    )

    const faqButton = screen.getByRole('button', { name: /What is ChhatraLekha\?/i })
    await user.click(faqButton)

    expect(screen.getByText(/unified, multilingual digital academic identity and operations platform/i)).toBeInTheDocument()
  })

  it('renders SignupPage with form controls and validation', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <AuthProvider>
          <SignupPage />
        </AuthProvider>
      </MemoryRouter>,
    )

    expect(screen.getByText(/Get Started with ChhatraLekha/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Full Legal Name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/E-mail address/i)).toBeInTheDocument()
    expect(screen.getByLabelText('Password', { exact: true })).toBeInTheDocument()
    expect(screen.getByLabelText('Confirm Password', { exact: true })).toBeInTheDocument()

    // Attempt submitting without inputs
    const submitBtn = screen.getByRole('button', { name: /Complete Registration/i })
    await user.click(submitBtn)

    expect(screen.getByRole('alert')).toHaveTextContent(/Please provide your full legal name/i)
  })

  it('validates password matching on SignupPage', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <AuthProvider>
          <SignupPage />
        </AuthProvider>
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/Full Legal Name/i), 'Aarav Sharma')
    await user.type(screen.getByLabelText(/E-mail address/i), 'aarav@example.com')
    await user.type(screen.getByLabelText('Password', { exact: true }), 'Password123')
    await user.type(screen.getByLabelText('Confirm Password', { exact: true }), 'DifferentPassword')

    await user.click(screen.getByRole('button', { name: /Complete Registration/i }))
    expect(screen.getByRole('alert')).toHaveTextContent(/Passwords do not match/i)
  })

  it('renders AccessibilityPage with WCAG standards and shortcuts', () => {
    render(
      <MemoryRouter>
        <AccessibilityPage />
      </MemoryRouter>,
    )

    expect(screen.getByText(/Accessibility Statement/i)).toBeInTheDocument()
    expect(screen.getByText(/WCAG 2.1 AA Conformance/i)).toBeInTheDocument()
    expect(screen.getByText(/Platform Keyboard Shortcuts/i)).toBeInTheDocument()
  })

  it('renders quick demo persona shortcuts on LoginPage', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>,
    )

    expect(screen.getByText(/Explore Demo Personas/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Student' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Faculty' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Directorate' })).toBeInTheDocument()
  })
})
