import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import StudentAcademicSelectionWizard from '../components/common/StudentAcademicSelectionWizard'
import LoginPage from '../pages/LoginPage'
import { AuthProvider } from '../hooks/useAuth'
import { api } from '../services/api'

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    api: {
      ...actual.api,
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    },
  }
})

const MOCK_CONTEXT = {
  schools: [
    {
      institution_id: 'SCH-DEL-001',
      name: 'Delhi Public School (R.K. Puram)',
      type: 'SCHOOL',
      city: 'New Delhi',
      state: 'Delhi',
      board: 'CBSE',
      classes: [
        { class_name: 'Class 9', sections: ['A', 'B'] },
        { class_name: 'Class 10', sections: ['A', 'B'] },
        { class_name: 'Class 11', sections: ['Science-A', 'Commerce-A'] },
      ],
    },
    {
      institution_id: 'SCH-DAV-101',
      name: 'DAV Public School (Chandrasekharpur)',
      type: 'SCHOOL',
      city: 'Bhubaneswar',
      state: 'Odisha',
      board: 'CBSE',
      classes: [
        { class_name: 'Class 8', sections: ['A'] },
        { class_name: 'Class 10', sections: ['A', 'B'] },
      ],
    },
  ],
  colleges: [
    {
      institution_id: 'INST-0421',
      name: 'Vidya Vikas Institute of Technology',
      type: 'ENGINEERING',
      city: 'Bengaluru',
      state: 'Karnataka',
      courses: [
        {
          program_id: 'BTECH_CSE',
          program_name: 'B.Tech Computer Science & Engineering',
          semesters: ['Semester 1', 'Semester 3', 'Semester 5', 'Semester 7'],
        },
        {
          program_id: 'MCA',
          program_name: 'Master of Computer Applications',
          semesters: ['Semester 1', 'Semester 3'],
        },
      ],
    },
  ],
}

describe('StudentAcademicSelectionWizard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.get.mockImplementation((url) => {
      if (url.includes('/auth/demo-academic-context')) {
        return Promise.resolve({ data: MOCK_CONTEXT })
      }
      if (url.includes('/auth/google/config')) {
        return Promise.resolve({ data: { enabled: false } })
      }
      return Promise.resolve({ data: {} })
    })
    api.post.mockResolvedValue({
      data: {
        access_token: 'demo-token-abc',
        refresh_token: 'demo-refresh-xyz',
        role: 'student',
        user_id: 'DEMO-STUDENT-01',
      },
    })
  })

  it('does not render when isOpen is false', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <StudentAcademicSelectionWizard isOpen={false} onClose={vi.fn()} />
        </AuthProvider>
      </MemoryRouter>,
    )
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('renders Step 1 (Education Type selection) when open', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <StudentAcademicSelectionWizard isOpen={true} onClose={vi.fn()} />
        </AuthProvider>
      </MemoryRouter>,
    )

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(
      await screen.findByText(/Are you a School student or a College student/i),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /School Student/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /College Student/i })).toBeInTheDocument()
  })

  it('progresses to School details in Step 2 with school-specific fields', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <AuthProvider>
          <StudentAcademicSelectionWizard isOpen={true} onClose={vi.fn()} />
        </AuthProvider>
      </MemoryRouter>,
    )

    await screen.findByText(/Are you a School student or a College student/i)

    // Step 1: Default is School -> Click Continue
    const continueBtn = screen.getByRole('button', { name: /Continue/i })
    await user.click(continueBtn)

    // Step 2: Should show School & Class selection
    expect(await screen.findByText(/Select School & Class/i)).toBeInTheDocument()
    expect(screen.getByText(/School \/ Institution/i)).toBeInTheDocument()
    expect(screen.getByText(/Class Level/i)).toBeInTheDocument()

    // Test Back button
    const backBtn = screen.getByRole('button', { name: /Back/i })
    await user.click(backBtn)
    expect(
      await screen.findByText(/Are you a School student or a College student/i),
    ).toBeInTheDocument()
  })

  it('progresses to College details in Step 2 when College is selected', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <AuthProvider>
          <StudentAcademicSelectionWizard isOpen={true} onClose={vi.fn()} />
        </AuthProvider>
      </MemoryRouter>,
    )

    await screen.findByText(/Are you a School student or a College student/i)

    // Select College
    const collegeOption = screen.getByRole('button', { name: /College Student/i })
    await user.click(collegeOption)

    // Click Continue
    const continueBtn = screen.getByRole('button', { name: /Continue/i })
    await user.click(continueBtn)

    // Step 2: Should show College & Program selection
    expect(await screen.findByText(/Select College & Course/i)).toBeInTheDocument()
    expect(screen.getByText(/College \/ Institution/i)).toBeInTheDocument()
    expect(screen.getByText(/Course \/ Degree Programme/i)).toBeInTheDocument()
    expect(screen.getByText(/Academic Semester/i)).toBeInTheDocument()
  })

  it('completes the full flow and submits contextual demo login', async () => {
    const handleSuccess = vi.fn()
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <AuthProvider>
          <StudentAcademicSelectionWizard isOpen={true} onClose={vi.fn()} onSuccess={handleSuccess} />
        </AuthProvider>
      </MemoryRouter>,
    )

    await screen.findByText(/Are you a School student or a College student/i)

    // Step 1: Continue with School
    await user.click(screen.getByRole('button', { name: /Continue/i }))

    // Step 2: Review details and click Continue to Step 3
    await screen.findByText(/Select School & Class/i)
    await user.click(screen.getByRole('button', { name: /Continue/i }))

    // Step 3: Confirmation Summary
    await screen.findByText(/Confirm Demo Student Profile/i)
    expect(screen.getByText(/Delhi Public School \(R\.K\. Puram\)/i)).toBeInTheDocument()

    // Click Enter Student Dashboard
    const launchBtn = screen.getByRole('button', { name: /Enter Student Dashboard/i })
    await user.click(launchBtn)

    await waitFor(() => expect(api.post).toHaveBeenCalled())
    expect(api.post).toHaveBeenCalledWith(
      '/auth/demo-login',
      expect.objectContaining({
        role: 'student',
        education_type: 'school',
        institution_id: 'SCH-DEL-001',
      }),
    )
    expect(handleSuccess).toHaveBeenCalled()
  })

  it('handles submission error gracefully without closing', async () => {
    api.post.mockRejectedValue({
      response: {
        data: {
          detail: "School institution 'SCH-DEL-001' is not available in demo options.",
        },
      },
    })

    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <AuthProvider>
          <StudentAcademicSelectionWizard isOpen={true} onClose={vi.fn()} />
        </AuthProvider>
      </MemoryRouter>,
    )

    await screen.findByText(/Are you a School student or a College student/i)
    await user.click(screen.getByRole('button', { name: /Continue/i }))
    await screen.findByText(/Select School & Class/i)
    await user.click(screen.getByRole('button', { name: /Continue/i }))

    await screen.findByText(/Confirm Demo Student Profile/i)
    await user.click(screen.getByRole('button', { name: /Enter Student Dashboard/i }))

    expect(
      await screen.findByText(/School institution 'SCH-DEL-001' is not available in demo options/i),
    ).toBeInTheDocument()
  })
})

describe('LoginPage Student Persona Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.get.mockImplementation((url) => {
      if (url.includes('/auth/demo-academic-context')) {
        return Promise.resolve({ data: MOCK_CONTEXT })
      }
      if (url.includes('/auth/google/config')) {
        return Promise.resolve({ data: { enabled: false } })
      }
      return Promise.resolve({ data: {} })
    })
    api.post.mockResolvedValue({
      data: {
        access_token: 'token-abc',
        role: 'student',
      },
    })
  })

  it('opens Academic Selection Wizard when Student demo persona is clicked, without instant login', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>,
    )

    // Find the Student quick demo button
    const studentBtn = screen.getByRole('button', { name: 'Student' })
    await user.click(studentBtn)

    // Academic Selection Wizard should open
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(
      await screen.findByText(/Are you a School student or a College student/i),
    ).toBeInTheDocument()

    // demo-login should NOT have been called yet
    expect(api.post).not.toHaveBeenCalled()
  })
})
