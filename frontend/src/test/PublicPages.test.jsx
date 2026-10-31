import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import LandingPage from '../pages/LandingPage'
import AboutPage from '../pages/AboutPage'
import FaqPage from '../pages/FaqPage'
import ContactPage from '../pages/ContactPage'
import PrivacyPage from '../pages/PrivacyPage'
import TermsPage from '../pages/TermsPage'
import NotFoundPage from '../pages/NotFoundPage'

describe('Public Pages', () => {
  it('renders LandingPage with headline and call to actions', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    )
    expect(screen.getByText(/One trusted record for every student/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Verify a credential/i })).toBeInTheDocument()
  })

  it('renders AboutPage with problem statement details', () => {
    render(
      <MemoryRouter>
        <AboutPage />
      </MemoryRouter>,
    )
    expect(screen.getByText(/Academic Record Verification/i)).toBeInTheDocument()
    expect(screen.getByText(/About ChhatraLekha/i)).toBeInTheDocument()
  })

  it('renders FaqPage with accordion questions', () => {
    render(
      <MemoryRouter>
        <FaqPage />
      </MemoryRouter>,
    )
    expect(screen.getByText(/What is APAAR\?/i)).toBeInTheDocument()
  })

  it('renders ContactPage with form inputs', () => {
    render(
      <MemoryRouter>
        <ContactPage />
      </MemoryRouter>,
    )
    expect(screen.getByLabelText(/Your Name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Send Message/i })).toBeInTheDocument()
  })

  it('renders PrivacyPage and TermsPage with draft disclaimer', () => {
    const { unmount } = render(
      <MemoryRouter>
        <PrivacyPage />
      </MemoryRouter>,
    )
    expect(screen.getByText(/Privacy Policy/i)).toBeInTheDocument()
    expect(screen.getByText(/Draft for the prototype/i)).toBeInTheDocument()
    unmount()

    render(
      <MemoryRouter>
        <TermsPage />
      </MemoryRouter>,
    )
    expect(screen.getByText(/Terms of Service/i)).toBeInTheDocument()
  })

  it('renders NotFoundPage on invalid routes', () => {
    render(
      <MemoryRouter initialEntries={['/some/unknown/path']}>
        <Routes>
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </MemoryRouter>,
    )
    expect(screen.getByText(/404/i)).toBeInTheDocument()
    expect(screen.getByText(/Resource Not Found/i)).toBeInTheDocument()
  })
})
