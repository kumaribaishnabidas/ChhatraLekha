import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import StudentHomePage from '../pages/student/StudentHomePage'
import StudentIdCardPage from '../pages/student/StudentIdCardPage'
import StudentSharePage from '../pages/student/StudentSharePage'
import StudentConsentPage from '../pages/student/StudentConsentPage'
import StudentUploadsPage from '../pages/student/StudentUploadsPage'
import StudentResultsPage from '../pages/student/StudentResultsPage'
import StudentActivityPage from '../pages/student/StudentActivityPage'
import { AuthProvider } from '../hooks/useAuth'
import { api } from '../services/api'

const MOCK_PROFILE = {
  student_id: 'CL-STU-001',
  student_name: 'Baishnabi Das',
  apaar_id_masked: '•••• •••• 7890',
  institution_name: 'National Institute of Technology',
  program_name: 'B.Tech Computer Science',
  academic_year: '2024-25',
  record_status: 'ACTIVE',
  is_claimed: true,
}

const MOCK_CARD = {
  card_type: 'Student Digital ID',
  chhatralekha_student_id: 'CL-STU-001',
  student_name: 'Baishnabi Das',
  apaar_id_masked: '•••• •••• 7890',
  institution_name: 'National Institute of Technology',
  program_name: 'B.Tech Computer Science',
  academic_year: '2024-25',
  roll_number: 'CSE-2024-042',
  record_status: 'ACTIVE',
  issued_date: '2024-08-01',
  token: 'mock-opaque-token-123',
  token_url: 'http://localhost:5173/verify/t/mock-opaque-token-123',
}

const MOCK_SHARES = [
  {
    token_id: 'tok-1',
    token: 'opaque-tok-1',
    share_url: 'http://localhost:5173/verify/t/opaque-tok-1',
    status: 'ACTIVE',
    allowed_fields: ['institution', 'programme', 'academic_year', 'status'],
    expires_at: '2026-11-01T20:00:00Z',
    created_at: '2026-10-31T20:00:00Z',
    access_count: 3,
  },
]

const MOCK_CONSENT = {
  purposes: [
    {
      purpose: 'EMPLOYMENT_VERIFICATION',
      label: 'Employment & Background Verification',
      description: 'Allows verified employers to check degree standing.',
      is_granted: true,
      last_updated: '2026-10-31T20:00:00Z',
    },
  ],
  ledger: [
    {
      consent_id: 'c-1',
      purpose: 'EMPLOYMENT_VERIFICATION',
      status: 'GRANTED',
      timestamp: '2026-10-31T20:00:00Z',
    },
  ],
}

const MOCK_UPLOADS = [
  {
    upload_id: 'up-1',
    filename: 'marksheet_sem1.pdf',
    document_type: 'Marksheet',
    status: 'APPROVED',
    created_at: '2026-10-31T20:00:00Z',
    matched_fields: ['name', 'roll_number'],
    mismatched_fields: [],
    confidence_score: 0.98,
  },
]

const MOCK_RESULTS = {
  cgpa: 8.92,
  total_credits_earned: 44,
  semesters: [
    {
      semester: 'Semester 1',
      sgpa: 8.8,
      credits: 22,
      subjects: [
        { code: 'CS101', name: 'Intro to Programming', credits: 4, grade: 'A', points: 8.0 },
      ],
    },
  ],
}

const MOCK_ACTIVITY = [
  {
    id: 'act-1',
    action: 'ISSUE_SHARE_TOKEN',
    details: 'Created 24h verification link for employer check.',
    category: 'SHARE',
    timestamp: '2026-10-31T20:00:00Z',
  },
]

describe('Student Portal Pages', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    localStorage.clear()
    localStorage.setItem(
      'chhatralekha.auth',
      JSON.stringify({
        token: 'test-token',
        user: { role: 'student', full_name: 'Baishnabi Das', apaar_id: '984210357890' },
      }),
    )

    api.get = vi.fn((url) => {
      if (url === '/auth/me') {
        return Promise.resolve({
          data: { user_id: 'USR-STU', role: 'student', full_name: 'Baishnabi Das', apaar_id: '984210357890' },
        })
      }
      if (url === '/me/profile') return Promise.resolve({ data: MOCK_PROFILE })
      if (url === '/me/id-card') return Promise.resolve({ data: MOCK_CARD })
      if (url === '/me/shares') return Promise.resolve({ data: MOCK_SHARES })
      if (url === '/me/consent') return Promise.resolve({ data: MOCK_CONSENT })
      if (url === '/me/uploads') return Promise.resolve({ data: MOCK_UPLOADS })
      if (url === '/me/results') return Promise.resolve({ data: MOCK_RESULTS })
      if (url === '/me/activity') return Promise.resolve({ data: MOCK_ACTIVITY })
      return Promise.resolve({ data: [] })
    })
  })

  it('renders StudentHomePage with profile identity cards', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <StudentHomePage />
        </AuthProvider>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('Baishnabi Das')).toBeInTheDocument()
    })
    expect(screen.getByText(/National Institute of Technology/i)).toBeInTheDocument()
    expect(screen.getByText('CL-STU-001')).toBeInTheDocument()
  })

  it('renders StudentIdCardPage with verification token and print trigger', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <StudentIdCardPage />
        </AuthProvider>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('CSE-2024-042')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: /Print ID Card/i })).toBeInTheDocument()
    expect(screen.getByText(/Scan to Verify Authenticity/i)).toBeInTheDocument()
  })

  it('renders StudentSharePage with active share links and revocation option', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <StudentSharePage />
        </AuthProvider>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('tok-1')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: /Generate Verification Link/i })).toBeInTheDocument()
    expect(screen.getByText('Revoke')).toBeInTheDocument()
  })

  it('renders StudentConsentPage with purpose toggle switches and ledger history', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <StudentConsentPage />
        </AuthProvider>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('Employment & Background Verification')).toBeInTheDocument()
    })
    expect(screen.getByText(/Consent Audit Ledger/i)).toBeInTheDocument()
  })

  it('renders StudentUploadsPage with upload dropzone and review status', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <StudentUploadsPage />
        </AuthProvider>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('marksheet_sem1.pdf')).toBeInTheDocument()
    })
    expect(screen.getByText(/Human-in-the-Loop Required/i)).toBeInTheDocument()
    expect(screen.getByText('APPROVED')).toBeInTheDocument()
  })

  it('renders StudentResultsPage with CGPA and semester breakdown', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <StudentResultsPage />
        </AuthProvider>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('8.92')).toBeInTheDocument()
    })
    expect(screen.getByText('CS101')).toBeInTheDocument()
    expect(screen.getByText('Intro to Programming')).toBeInTheDocument()
  })

  it('renders StudentActivityPage with audit timeline', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <StudentActivityPage />
        </AuthProvider>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('ISSUE SHARE TOKEN')).toBeInTheDocument()
    })
    expect(screen.getByText(/Created 24h verification link for employer check./i)).toBeInTheDocument()
  })
})
