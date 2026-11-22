import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { api } from '../services/api'
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

  it('renders authentic empty state when unassigned teacher has zero classes', async () => {
    // Override teacher-classes to return empty array
    const originalGet = api.get
    api.get = vi.fn((url) => {
      if (url.includes('/attendance/teacher-classes')) {
        return Promise.resolve({ data: [] })
      }
      return originalGet(url)
    })

    render(
      <BrowserRouter>
        <AttendancePage />
      </BrowserRouter>,
    )

    await waitFor(() => {
      expect(screen.queryByText('CLS-10A')).not.toBeInTheDocument()
      expect(screen.queryByText('CLS-10B')).not.toBeInTheDocument()
    })

    api.get = originalGet
  })

  it('displays authentic error message when session submission fails', async () => {
    const originalPost = api.post
    api.post = vi.fn((url, body) => {
      if (url.includes('/attendance/sessions')) {
        return Promise.reject({
          response: {
            status: 409,
            data: { detail: 'Attendance session already submitted for this class today.' },
          },
        })
      }
      return originalPost(url, body)
    })

    render(
      <BrowserRouter>
        <AttendancePage />
      </BrowserRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('Aarav Patel')).toBeInTheDocument()
    })

    const submitBtn = screen.getByRole('button', { name: /Submit Attendance Session/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(
        screen.getByText(/Attendance already submitted for Class 10 Section A on/i),
      ).toBeInTheDocument()
    })

    api.post = originalPost
  })

  it('renders authentic empty state in Overview & Analytics when no sessions exist', async () => {
    const originalGet = api.get
    api.get = vi.fn((url) => {
      if (url.includes('/attendance/reports/summary')) {
        return Promise.resolve({
          data: {
            institution_id: 'INST-0421',
            period_start: '2025-06-01',
            period_end: '2026-05-31',
            total_sessions: 0,
            average_attendance_percentage: 0.0,
            class_summaries: [],
            defaulters_count: 0,
            daily_trends: [],
          },
        })
      }
      return originalGet(url)
    })

    render(
      <BrowserRouter>
        <AttendancePage />
      </BrowserRouter>,
    )

    const analyticsTab = screen.getByRole('button', { name: /Overview & Analytics/i })
    fireEvent.click(analyticsTab)

    await waitFor(() => {
      expect(screen.getByText('No class attendance summaries recorded yet.')).toBeInTheDocument()
      expect(screen.queryByText('CLS-9A')).not.toBeInTheDocument()
    })

    api.get = originalGet
  })

  it('handles CSV export failure gracefully with error notification and resets loading state', async () => {
    const originalGet = api.get
    api.get = vi.fn((url, config) => {
      if (url.includes('/attendance/reports/export-csv')) {
        return Promise.reject({
          response: {
            status: 403,
            data: { detail: 'Export forbidden: administrative role required.' },
          },
        })
      }
      return originalGet(url, config)
    })

    render(
      <BrowserRouter>
        <AttendancePage />
      </BrowserRouter>,
    )

    const reportsTab = screen.getByRole('button', { name: /Reports & CSV Export/i })
    fireEvent.click(reportsTab)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Export Attendance CSV' })).toBeInTheDocument()
    })

    const exportBtn = screen.getByRole('button', { name: 'Export Attendance CSV' })
    fireEvent.click(exportBtn)

    await waitFor(() => {
      expect(screen.getByText('Export forbidden: administrative role required.')).toBeInTheDocument()
      expect(screen.queryByText(/Attendance CSV report downloaded/i)).not.toBeInTheDocument()
    })

    // Confirm button returned to idle and enabled
    expect(screen.getByRole('button', { name: 'Export Attendance CSV' })).not.toBeDisabled()

    api.get = originalGet
  })

  it('propagates valid session ID in attendance correction request and validates payload', async () => {
    render(
      <BrowserRouter>
        <AttendancePage />
      </BrowserRouter>,
    )

    // Wait for roster to load
    await waitFor(() => {
      expect(screen.getByText('Aarav Patel')).toBeInTheDocument()
    })

    // Click "Request Correction" on the first roster student (STU-001)
    const correctionButtons = screen.getAllByRole('button', { name: 'Request Correction' })
    expect(correctionButtons.length).toBeGreaterThan(0)
    fireEvent.click(correctionButtons[0])

    // Verify modal appears
    await waitFor(() => {
      expect(screen.getByText('Request Attendance Correction')).toBeInTheDocument()
    })

    const sessionIdInput = screen.getByLabelText(/Session ID/i)
    const form = sessionIdInput.closest('form')

    // 1. Submit with empty session ID -> triggers validation error and does NOT call api.post
    fireEvent.change(sessionIdInput, { target: { value: '' } })
    fireEvent.submit(form)

    await waitFor(() => {
      expect(screen.getByText('Session ID is required for attendance correction.')).toBeInTheDocument()
    })
    expect(api.post).not.toHaveBeenCalledWith(
      '/attendance/corrections',
      expect.anything(),
    )

    // 2. Fill valid session ID and justification
    fireEvent.change(sessionIdInput, { target: { value: 'ATT-SESSION-2026-0310' } })
    const reasonInput = screen.getByPlaceholderText(/Verified medical certificate submitted/i)
    fireEvent.change(reasonInput, { target: { value: 'Verified medical leave approved' } })

    fireEvent.submit(form)

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        '/attendance/corrections',
        expect.objectContaining({
          session_id: 'ATT-SESSION-2026-0310',
          student_id: 'STU-001',
          requested_status: 'EXCUSED',
          reason: 'Verified medical leave approved',
        }),
      )
    })

    // Explicitly verify the old hardcoded ATT-PREV was never sent
    expect(api.post).not.toHaveBeenCalledWith(
      '/attendance/corrections',
      expect.objectContaining({ session_id: 'ATT-PREV' }),
    )

    // Modal closes on success
    await waitFor(() => {
      expect(screen.queryByText('Request Attendance Correction')).not.toBeInTheDocument()
    })
  })

  it('Fix 1: captures session ID on submit, propagates to correction modal, and invalidates on class/date switch', async () => {
    const originalPost = api.post
    api.post = vi.fn((url, body) => {
      if (url.includes('/attendance/sessions')) {
        return Promise.resolve({
          data: {
            session_id: 'ATT-CAPTURED-999',
            ...body,
          },
        })
      }
      return originalPost(url, body)
    })

    render(
      <BrowserRouter>
        <AttendancePage />
      </BrowserRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('Aarav Patel')).toBeInTheDocument()
    })

    // 1. Submit session
    const submitBtn = screen.getByRole('button', { name: /Submit Attendance Session/i })
    fireEvent.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText(/Attendance recorded successfully/i)).toBeInTheDocument()
    })

    // 2. Open correction modal for first student
    const correctionButtons = screen.getAllByRole('button', { name: 'Request Correction' })
    fireEvent.click(correctionButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Request Attendance Correction')).toBeInTheDocument()
    })

    // Propagated session ID is ATT-CAPTURED-999
    const sessionInput = screen.getByLabelText(/Session ID/i)
    expect(sessionInput.value).toBe('ATT-CAPTURED-999')

    // Close modal
    const cancelBtn = screen.getByRole('button', { name: 'Cancel' })
    fireEvent.click(cancelBtn)

    // 3. Switch date to invalidate stale session
    const dateInput = screen.getByLabelText(/Attendance Date/i)
    fireEvent.change(dateInput, { target: { value: '2026-03-25' } })

    // Open correction modal again
    const correctionButtonsAfter = screen.getAllByRole('button', { name: 'Request Correction' })
    fireEvent.click(correctionButtonsAfter[0])

    await waitFor(() => {
      expect(screen.getByText('Request Attendance Correction')).toBeInTheDocument()
    })

    // Stale session ID must not be reused
    const sessionInputAfter = screen.getByLabelText(/Session ID/i)
    expect(sessionInputAfter.value).not.toBe('ATT-CAPTURED-999')
    expect(sessionInputAfter.value).toBe('')

    // 4. Missing session ID validation prevents submission
    const form = sessionInputAfter.closest('form')
    fireEvent.submit(form)

    await waitFor(() => {
      expect(screen.getByText('Session ID is required for attendance correction.')).toBeInTheDocument()
    })

    api.post = originalPost
  })

  it('Fix 6: displays genuine zeroes for attendance statistics without synthetic defaults', async () => {
    const originalGet = api.get
    api.get = vi.fn((url) => {
      if (url.includes('/attendance/reports/summary')) {
        return Promise.resolve({
          data: {
            institution_id: 'INST-0421',
            total_sessions: 0,
            average_attendance_percentage: 0.0,
            class_summaries: [],
            defaulters_count: 0,
            daily_trends: [],
          },
        })
      }
      return originalGet(url)
    })

    render(
      <BrowserRouter>
        <AttendancePage />
      </BrowserRouter>,
    )

    const analyticsTab = screen.getByRole('button', { name: /Overview & Analytics/i })
    fireEvent.click(analyticsTab)

    await waitFor(() => {
      expect(screen.getByText('0.0%')).toBeInTheDocument()
      expect(screen.getAllByText('0').length).toBeGreaterThanOrEqual(2)
      // Verify synthetic numbers are gone
      expect(screen.queryByText('92.4%')).not.toBeInTheDocument()
      expect(screen.queryByText('64')).not.toBeInTheDocument()
      expect(screen.queryByText('Above 75% target')).not.toBeInTheDocument()
      expect(screen.getByText('Below 75% target')).toBeInTheDocument()
    })

    api.get = originalGet
  })

  it('Fix 6: displays clean unavailable state fallback when report data is null or fails', async () => {
    const originalGet = api.get
    api.get = vi.fn((url) => {
      if (url.includes('/attendance/reports/summary')) {
        return Promise.reject(new Error('Network error'))
      }
      return originalGet(url)
    })

    render(
      <BrowserRouter>
        <AttendancePage />
      </BrowserRouter>,
    )

    const analyticsTab = screen.getByRole('button', { name: /Overview & Analytics/i })
    fireEvent.click(analyticsTab)

    await waitFor(() => {
      expect(screen.getAllByText('--').length).toBeGreaterThanOrEqual(2)
      expect(screen.queryByText('92.4%')).not.toBeInTheDocument()
      expect(screen.queryByText('64')).not.toBeInTheDocument()
      expect(screen.queryByText('Above 75% target')).not.toBeInTheDocument()
    })

    api.get = originalGet
  })
})

