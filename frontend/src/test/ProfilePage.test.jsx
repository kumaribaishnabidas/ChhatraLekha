import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import ProfilePage from '../pages/ProfilePage'
import { api } from '../services/api'
import { AuthContext } from '../hooks/useAuth'

vi.mock('../services/api', () => ({
  api: {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockProfile = {
  user_id: 'DEMO-STUDENT-01',
  full_name: 'Aarav Sharma',
  role: 'student',
  role_label: 'Student',
  email: 'student.demo@example.com',
  personal_email: 'student.demo@example.com',
  personal_email_verified: true,
  institution_email: 'aarav.sharma@inst0421.edu.in',
  institution_email_verified: false,
  mobile: '+91 98765 43210',
  preferred_language: 'en',
  institution_id: 'INST-0421',
  institution_name: 'Vidya Vikas Institute of Technology',
  account_status: 'ACTIVE',
  created_at: '2024-01-01T00:00:00Z',
  profile_completion_percentage: 85,
  profile_pictures: {
    common_url: null,
    web_url: null,
    android_url: null,
    ios_url: null,
    use_common: true,
  },
  active_avatar_url: null,
  student_details: {
    student_id: 'CL-STU-042189AB',
    student_name: 'Aarav Sharma',
    apaar_id_masked: '9293 **** ****',
    institute_roll_no: 'D-2024-001',
    institution_id: 'INST-0421',
    institution_name: 'Vidya Vikas Institute of Technology',
    programme_name: 'B.Tech Computer Science & Engineering',
    department: 'Department of Computer Science & Engineering',
    class_section: 'Class 3rd Year - Section A',
    academic_year: '2024-25',
    current_semester: 'Semester 5',
    admission_quota: 'MERIT',
    attendance_percentage: 92.4,
    cumulative_cgpa: 8.75,
    guardian_name: 'Sunita Sharma',
    guardian_relationship: 'Mother / Legal Guardian',
    guardian_phone_masked: '+91 98**** **12',
    verified_credentials_count: 3,
    achievements: [
      'First Class with Distinction (Semesters 1-4)',
      "Dean's Honour Roll - Academic Year 2023-24",
    ],
  },
}

const mockSessions = [
  {
    session_id: 'SESS-CURR-01',
    ip_address: '127.0.0.1',
    device: 'Web Browser (Desktop) - Active Session',
    last_active_at: '2024-11-01T00:00:00Z',
    is_current: true,
  },
]

describe('ProfilePage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.get.mockImplementation((url) => {
      if (url === '/profile/me') {
        return Promise.resolve({ data: mockProfile })
      }
      if (url === '/profile/sessions') {
        return Promise.resolve({ data: mockSessions })
      }
      return Promise.reject(new Error('Unknown url'))
    })
  })

  it('renders profile summary header and role information', async () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider value={{ user: { full_name: 'Aarav Sharma' }, role: 'student' }}>
          <ProfilePage />
        </AuthContext.Provider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Aarav Sharma')).toBeInTheDocument()
      expect(screen.getByText('DEMO-STUDENT-01')).toBeInTheDocument()
      expect(screen.getByText('85%')).toBeInTheDocument()
      expect(screen.getByText('Academic Record & Identity')).toBeInTheDocument()
      expect(screen.getByText('92.4%')).toBeInTheDocument()
      expect(screen.getByText('8.75 / 10.0')).toBeInTheDocument()
    })
  })

  it('switches to email management tab and requests verification code', async () => {
    api.post.mockResolvedValueOnce({
      data: {
        status: 'pending_verification',
        message: 'A 6-digit verification code has been issued.',
        demo_verification_code: '654321',
      },
    })

    render(
      <MemoryRouter>
        <AuthContext.Provider value={{ user: { full_name: 'Aarav Sharma' }, role: 'student' }}>
          <ProfilePage />
        </AuthContext.Provider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Email Management')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Email Management'))

    expect(screen.getByText('Personal Email Address')).toBeInTheDocument()
    expect(screen.getByText('Institution-Issued Email Address')).toBeInTheDocument()

    const sendCodeBtns = screen.getAllByText('Send Code')
    fireEvent.click(sendCodeBtns[0])

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/profile/email', {
        email_type: 'personal',
        email: 'student.demo@example.com',
      })
    })
  })

  it('switches to active device sessions tab', async () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider value={{ user: { full_name: 'Aarav Sharma' }, role: 'student' }}>
          <ProfilePage />
        </AuthContext.Provider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Active Sessions')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Active Sessions'))

    await waitFor(() => {
      expect(screen.getByText('Web Browser (Desktop) - Active Session')).toBeInTheDocument()
      expect(screen.getByText('Current Session')).toBeInTheDocument()
    })
  })
})
