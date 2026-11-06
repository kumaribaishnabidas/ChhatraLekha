import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import AttendancePage from '../pages/AttendancePage'

// Mock useAuth
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      user_id: 'USR-TEACHER-01',
      name: 'Prof. Rajesh Kumar',
      role: 'school_admin',
      institution_id: 'INST-0421',
      apaar_id: '992100000001',
    },
    role: 'school_admin',
    can: vi.fn(() => true),
  }),
}))

// Mock api
vi.mock('../services/api', () => ({
  api: {
    get: vi.fn((url) => {
      if (url.includes('/attendance/teacher-classes')) {
        return Promise.resolve({
          data: [
            {
              class_id: 'CLS-10A',
              target_label: 'Class 10 Section A',
              subject_name: 'Mathematics',
              subject_id: 'SUB-MATH',
            },
          ],
        })
      }
      if (url.includes('/attendance/roster')) {
        return Promise.resolve({
          data: [
            {
              student_id: 'STU-001',
              student_name: 'Aarav Patel',
              roll_number: '101',
              section: 'A',
              recent_attendance_rate: 96.0,
            },
            {
              student_id: 'STU-002',
              student_name: 'Diya Sen',
              roll_number: '102',
              section: 'A',
              recent_attendance_rate: 94.5,
            },
          ],
        })
      }
      if (url.includes('/attendance/policy')) {
        return Promise.resolve({
          data: {
            institution_id: 'INST-0421',
            mode: 'DAILY',
            working_days: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
            periods_per_day: 7,
            minimum_attendance_percentage: 75.0,
            late_arrival_threshold_minutes: 15,
            early_departure_threshold_minutes: 15,
            consecutive_absent_alert_threshold: 3,
            allowed_statuses: ['PRESENT', 'ABSENT', 'LATE', 'EXCUSED', 'ON_LEAVE', 'HALF_DAY'],
          },
        })
      }
      if (url.includes('/attendance/reports/summary')) {
        return Promise.resolve({
          data: {
            institution_id: 'INST-0421',
            period_start: '2025-06-01',
            period_end: '2026-05-31',
            total_sessions: 64,
            average_attendance_percentage: 92.4,
            class_summaries: [
              {
                class_id: 'CLS-10A',
                class_label: 'Class 10 Section A',
                total_sessions: 32,
                attendance_percentage: 94.2,
              },
            ],
            defaulters_count: 2,
            daily_trends: [],
          },
        })
      }
      if (url.includes('/attendance/corrections')) {
        return Promise.resolve({
          data: [
            {
              id: 'CORR-001',
              institution_id: 'INST-0421',
              session_id: 'ATT-001',
              student_id: 'STU-001',
              student_name: 'Aarav Patel',
              target_id: 'CLS-10A',
              session_date: '2026-03-01',
              previous_status: 'ABSENT',
              requested_status: 'EXCUSED',
              reason: 'Medical certificate verified',
              requested_by: 'TEA-01',
              requested_by_name: 'Prof. Kumar',
              requested_at: '2026-03-02T10:00:00Z',
              status: 'PENDING',
            },
          ],
        })
      }
      if (url.includes('/attendance/my-summary')) {
        return Promise.resolve({
          data: {
            student_id: '992100000001',
            total_sessions: 40,
            present_sessions: 38,
            absent_sessions: 2,
            late_sessions: 1,
            excused_sessions: 1,
            attendance_rate: 95.0,
            minimum_required: 75.0,
            is_compliant: true,
            subject_wise: [
              {
                subject_name: 'Mathematics',
                total_classes: 20,
                attended_classes: 19,
                percentage: 95.0,
              },
            ],
            recent_records: [
              {
                session_date: '2026-03-01',
                status: 'PRESENT',
                target_label: 'Class 10A',
                subject_name: 'Mathematics',
              },
            ],
            excused_absences: [],
          },
        })
      }
      return Promise.resolve({ data: [] })
    }),
    post: vi.fn((url, body) => {
      if (url.includes('/attendance/sessions')) {
        return Promise.resolve({
          data: {
            session_id: 'ATT-NEW-01',
            ...body,
          },
        })
      }
      if (url.includes('/review')) {
        return Promise.resolve({
          data: {
            id: 'CORR-001',
            status: body.decision === 'APPROVE' ? 'APPROVED' : 'REJECTED',
            previous_status: 'ABSENT',
            requested_status: 'EXCUSED',
          },
        })
      }
      if (url.includes('/corrections')) {
        return Promise.resolve({
          data: {
            id: 'CORR-NEW-01',
            ...body,
            status: 'PENDING',
          },
        })
      }
      if (url.includes('/policy')) {
        return Promise.resolve({
          data: {
            ...body,
            institution_id: 'INST-0421',
          },
        })
      }
      return Promise.resolve({ data: {} })
    }),
  },
}))

describe('Stage 0.9: Attendance Management System Frontend', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders Teacher Roll Call tab with class roster and batch toggles', async () => {
    render(
      <BrowserRouter>
        <AttendancePage />
      </BrowserRouter>,
    )

    expect(
      screen.getByRole('heading', { name: /Attendance Management System/i }),
    ).toBeInTheDocument()

    // Assert roster loaded
    await waitFor(() => {
      expect(screen.getByText('Aarav Patel')).toBeInTheDocument()
      expect(screen.getByText('Diya Sen')).toBeInTheDocument()
      expect(screen.getByText('Mark All Present')).toBeInTheDocument()
      expect(screen.getByText('Mark All Absent')).toBeInTheDocument()
    })

    // Click Mark All Absent
    const markAbsentBtn = screen.getByRole('button', { name: /Mark All Absent/i })
    fireEvent.click(markAbsentBtn)

    // Submit Attendance Session
    const submitBtn = screen.getByRole('button', { name: /Submit Attendance Session/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(
        screen.getByText(/Attendance recorded successfully/i),
      ).toBeInTheDocument()
    })
  })

  it('navigates to Overview & Analytics tab and verifies attendance rate and defaulters', async () => {
    render(
      <BrowserRouter>
        <AttendancePage />
      </BrowserRouter>,
    )

    const analyticsTab = screen.getByRole('button', { name: /Overview & Analytics/i })
    fireEvent.click(analyticsTab)

    await waitFor(() => {
      expect(screen.getByText('Class-wise Attendance Distribution')).toBeInTheDocument()
      expect(screen.getByText('92.4%')).toBeInTheDocument()
      expect(screen.getByText('Class 10 Section A')).toBeInTheDocument()
    })
  })

  it('navigates to Corrections Queue and tests administrator approval', async () => {
    render(
      <BrowserRouter>
        <AttendancePage />
      </BrowserRouter>,
    )

    const corrTab = screen.getByRole('button', { name: /Corrections Queue/i })
    fireEvent.click(corrTab)

    await waitFor(() => {
      expect(screen.getByText('Attendance Corrections & Audit Queue')).toBeInTheDocument()
      expect(screen.getByText('Medical certificate verified')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Approve' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Reject' })).toBeInTheDocument()
    })

    // Click Approve
    const approveBtn = screen.getByRole('button', { name: 'Approve' })
    fireEvent.click(approveBtn)

    await waitFor(() => {
      expect(screen.getByText(/Correction request approved/i)).toBeInTheDocument()
    })
  })

  it('navigates to Attendance Policy tab and verifies 75% minimum statutory setting', async () => {
    render(
      <BrowserRouter>
        <AttendancePage />
      </BrowserRouter>,
    )

    const policyTab = screen.getByRole('button', { name: /Attendance Policy/i })
    fireEvent.click(policyTab)

    await waitFor(() => {
      expect(screen.getByText('Institution Attendance Policy Configuration')).toBeInTheDocument()
      expect(screen.getByText('Minimum Attendance Requirement (%)')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Save Policy Configuration' })).toBeInTheDocument()
    })
  })

  it('navigates to Reports & CSV Export and triggers export action', async () => {
    render(
      <BrowserRouter>
        <AttendancePage />
      </BrowserRouter>,
    )

    const reportsTab = screen.getByRole('button', { name: /Reports & CSV Export/i })
    fireEvent.click(reportsTab)

    await waitFor(() => {
      expect(screen.getByText('Attendance Reports & Official CSV Export')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Export Attendance CSV' })).toBeInTheDocument()
    })

    const exportBtn = screen.getByRole('button', { name: 'Export Attendance CSV' })
    fireEvent.click(exportBtn)

    await waitFor(() => {
      expect(screen.getByText(/Attendance CSV report downloaded/i)).toBeInTheDocument()
    })
  })
})

