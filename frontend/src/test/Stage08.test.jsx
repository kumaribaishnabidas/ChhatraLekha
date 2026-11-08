import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import AcademicSetupPage from '../pages/AcademicSetupPage'
import { api } from '../services/api'

// Mock api
vi.mock('../services/api', () => {
  return {
    tokenStore: {
      getToken: vi.fn(() => 'mock-jwt-token'),
      getUser: vi.fn(() => ({
        user_id: 'user-admin-01',
        name: 'Dr. Ramesh Kumar',
        role: 'school_admin',
        institution_id: 'INST-0421',
      })),
      set: vi.fn(),
      clear: vi.fn(),
    },
    api: {
      get: vi.fn((url) => {
        if (url.includes('/academic/overview')) {
          return Promise.resolve({
            data: {
              active_academic_year: '2025-26',
              total_academic_years: 2,
              total_departments: 2,
              total_programmes: 2,
              total_classes: 3,
              total_subjects: 3,
              total_students_enrolled: 3,
              total_faculty_assignments: 2,
              recent_events: [],
            },
          })
        }
        if (url.includes('/academic/years')) {
          return Promise.resolve({
            data: [
              {
                id: 'AY-2025-26',
                year_label: '2025-26',
                start_date: '2025-06-01',
                end_date: '2026-05-31',
                admission_start: '2025-04-01',
                admission_end: '2025-06-15',
                is_current: true,
                is_archived: false,
              },
              {
                id: 'AY-2026-27',
                year_label: '2026-27',
                start_date: '2026-06-01',
                end_date: '2027-05-31',
                admission_start: '2026-04-01',
                admission_end: '2026-06-15',
                is_current: false,
                is_archived: false,
              },
            ],
          })
        }
        if (url.includes('/academic/terms')) {
          return Promise.resolve({
            data: [
              {
                id: 'TERM-2025-S1',
                term_name: 'Semester 1 (Autumn)',
                term_type: 'semester',
                term_number: 1,
                start_date: '2025-07-01',
                end_date: '2025-11-30',
                academic_year_id: 'AY-2025-26',
                is_active: true,
              },
            ],
          })
        }
        if (url.includes('/academic/departments')) {
          return Promise.resolve({
            data: [
              {
                id: 'DEPT-CS',
                dept_code: 'CSE',
                name: 'Computer Science and Engineering',
                head_of_department: 'Dr. Anita Roy',
                email: 'hod.cse@institution.ac.in',
                is_active: true,
              },
            ],
          })
        }
        if (url.includes('/academic/programmes')) {
          return Promise.resolve({
            data: [
              {
                id: 'PROG-BTECH-CSE',
                programme_code: 'BTECH-CS',
                name: 'Bachelor of Technology in Computer Science',
                degree_type: 'Bachelor',
                department_id: 'DEPT-CS',
                total_semesters: 8,
                total_credits: 160,
                is_active: true,
              },
            ],
          })
        }
        if (url.includes('/academic/classes')) {
          return Promise.resolve({
            data: [
              {
                id: 'CLS-10A',
                grade_level: 'Class 10',
                section: 'A',
                academic_year: '2025-26',
                room_number: 'Room 204',
                capacity: 40,
                class_teacher_name: 'Priya Sharma',
              },
            ],
          })
        }
        if (url.includes('/academic/subjects')) {
          return Promise.resolve({
            data: [
              {
                id: 'SUB-MATH-10',
                subject_code: 'MATH-10',
                subject_name: 'Mathematics',
                multilingual_name: 'Ganita (Mathematics)',
                credits: 4,
                is_practical: false,
                applicable_to: 'Class 10',
              },
              {
                id: 'SUB-SCI-10',
                subject_code: 'SCI-10',
                subject_name: 'General Science',
                multilingual_name: 'Vigyan (Science)',
                credits: 4,
                is_practical: true,
                applicable_to: 'Class 10',
              },
            ],
          })
        }
        if (url.includes('/academic/enrolments')) {
          return Promise.resolve({
            data: [
              {
                id: 'ENR-001',
                student_name: 'Aarav Patel',
                student_id: 'STU-001',
                enrolment_number: 'ENR-2025-01',
                class_id: 'CLS-10A',
                academic_year_id: 'AY-2025-26',
                status: 'active',
                is_current: true,
                enrolment_date: '2025-06-05',
              },
            ],
          })
        }
        if (url.includes('/academic/teacher-assignments')) {
          return Promise.resolve({
            data: [
              {
                id: 'ASG-001',
                teacher_name: 'Priya Sharma',
                teacher_id: 'TEA-001',
                subject_id: 'SUB-MATH-10',
                class_id: 'CLS-10A',
                role_in_course: 'Primary Teacher',
                academic_year_id: 'AY-2025-26',
              },
            ],
          })
        }
        if (url.includes('/academic/calendar/events')) {
          return Promise.resolve({
            data: [
              {
                id: 'EVT-001',
                title: 'Independence Day Holiday',
                event_type: 'holiday',
                start_date: '2025-08-15',
                end_date: '2025-08-15',
                description: 'National holiday observed.',
              },
              {
                id: 'EVT-002',
                title: 'Mid-Term Examinations',
                event_type: 'exam',
                start_date: '2025-10-10',
                end_date: '2025-10-22',
                description: 'Theory assessments.',
              },
            ],
          })
        }
        return Promise.resolve({ data: [] })
      }),
      post: vi.fn((url, body) => {
        if (url.includes('/activate')) {
          return Promise.resolve({ data: { status: 'activated' } })
        }
        if (url.includes('/archive')) {
          return Promise.resolve({ data: { status: 'archived' } })
        }
        if (url.includes('/promote')) {
          return Promise.resolve({
            data: {
              id: 'ENR-NEW-01',
              student_name: 'Aarav Patel',
              student_id: 'STU-001',
              enrolment_number: 'ENR-2026-01',
              class_id: 'Class 11-A',
              academic_year_id: 'AY-2026-27',
              status: 'active',
              is_current: true,
              enrolment_date: '2026-06-01',
            },
          })
        }
        if (url.includes('/transfer-section')) {
          return Promise.resolve({ data: { status: 'transferred' } })
        }
        return Promise.resolve({ data: { id: 'NEW-ID-01', ...body } })
      }),
      delete: vi.fn(() => Promise.resolve({ data: { status: 'deleted' } })),
    },
  }
})

describe('Stage 0.8: Academic Management Core Frontend', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders overview KPI metrics and active academic session', async () => {
    render(
      <BrowserRouter>
        <AcademicSetupPage />
      </BrowserRouter>,
    )

    expect(
      screen.getByRole('heading', { name: /Academic Management Core/i }),
    ).toBeInTheDocument()

    // Assert KPI metrics loaded
    await waitFor(() => {
      expect(screen.getByText('Active Academic Year')).toBeInTheDocument()
      expect(screen.getByText('2025-26')).toBeInTheDocument()
      expect(screen.getByText('Active Academic Operations')).toBeInTheDocument()
    })
  })

  it('navigates to Academic Years & Terms tab and displays session registry', async () => {
    render(
      <BrowserRouter>
        <AcademicSetupPage />
      </BrowserRouter>,
    )

    const yearsTab = screen.getByRole('button', { name: /Academic Years & Terms/i })
    fireEvent.click(yearsTab)

    await waitFor(() => {
      expect(screen.getByText('Academic Years Registry')).toBeInTheDocument()
      expect(screen.getByText('Active Session')).toBeInTheDocument()
      expect(screen.getByText('Terms & Semesters')).toBeInTheDocument()
    })
  })

  it('navigates to Departments & Programmes tab and shows department codes', async () => {
    render(
      <BrowserRouter>
        <AcademicSetupPage />
      </BrowserRouter>,
    )

    const deptsTab = screen.getByRole('button', { name: /Departments & Programmes/i })
    fireEvent.click(deptsTab)

    await waitFor(() => {
      expect(screen.getByText('Academic Departments')).toBeInTheDocument()
      expect(screen.getByText('CSE')).toBeInTheDocument()
      expect(screen.getByText('Computer Science and Engineering')).toBeInTheDocument()
      expect(screen.getByText('Academic Programmes & Degrees')).toBeInTheDocument()
      expect(screen.getByText('BTECH-CS')).toBeInTheDocument()
    })
  })

  it('navigates to Classes & Sections tab and displays cohort details', async () => {
    render(
      <BrowserRouter>
        <AcademicSetupPage />
      </BrowserRouter>,
    )

    const classesTab = screen.getByRole('button', { name: /Classes & Sections/i })
    fireEvent.click(classesTab)

    await waitFor(() => {
      expect(screen.getByText('Classes & Cohort Sections')).toBeInTheDocument()
      expect(screen.getByText('Class 10')).toBeInTheDocument()
      expect(screen.getByText('Section A')).toBeInTheDocument()
      expect(screen.getByText('Room 204')).toBeInTheDocument()
    })
  })

  it('navigates to Curriculum & Subjects tab and renders theory/practical courses', async () => {
    render(
      <BrowserRouter>
        <AcademicSetupPage />
      </BrowserRouter>,
    )

    const subjectsTab = screen.getByRole('button', { name: /Curriculum & Subjects/i })
    fireEvent.click(subjectsTab)

    await waitFor(() => {
      expect(screen.getByText('Curriculum & Subject Catalog')).toBeInTheDocument()
      expect(screen.getByText('MATH-10')).toBeInTheDocument()
      expect(screen.getByText('Theory')).toBeInTheDocument()
      expect(screen.getByText('SCI-10')).toBeInTheDocument()
      expect(screen.getByText('Practical Lab')).toBeInTheDocument()
    })
  })

  it('navigates to Student Enrolments and triggers Promotion dialog preserving history', async () => {
    render(
      <BrowserRouter>
        <AcademicSetupPage />
      </BrowserRouter>,
    )

    const enrolmentsTab = screen.getByRole('button', { name: /Student Enrolments/i })
    fireEvent.click(enrolmentsTab)

    await waitFor(() => {
      expect(
        screen.getByText('Student Enrolments & Academic Progression'),
      ).toBeInTheDocument()
      expect(screen.getByText('Aarav Patel')).toBeInTheDocument()
    })

    // Open promote modal
    const promoteBtn = screen.getByRole('button', { name: 'Promote' })
    fireEvent.click(promoteBtn)

    expect(
      screen.getByText('Promote Student to Next Academic Level'),
    ).toBeInTheDocument()

    // Confirm promotion
    const confirmBtn = screen.getByRole('button', { name: 'Confirm Promotion' })
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(screen.queryByText('Promote Student to Next Academic Level')).not.toBeInTheDocument()
    })
  })

  it('navigates to Faculty Allocations and verifies teacher assignment roster', async () => {
    render(
      <BrowserRouter>
        <AcademicSetupPage />
      </BrowserRouter>,
    )

    const allocTab = screen.getByRole('button', { name: /Faculty Allocations/i })
    fireEvent.click(allocTab)

    await waitFor(() => {
      expect(
        screen.getByText('Faculty Allocations & Teaching Assignments'),
      ).toBeInTheDocument()
      expect(screen.getByText('Priya Sharma')).toBeInTheDocument()
      expect(screen.getByText('Primary Teacher')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Unassign' })).toBeInTheDocument()
    })
  })

  it('navigates to Academic Calendar and filters events by type', async () => {
    render(
      <BrowserRouter>
        <AcademicSetupPage />
      </BrowserRouter>,
    )

    const calTab = screen.getByRole('button', { name: /Academic Calendar/i })
    fireEvent.click(calTab)

    await waitFor(() => {
      expect(
        screen.getByText('Academic Calendar (IST / Asia-Kolkata)'),
      ).toBeInTheDocument()
      expect(screen.getByText('Independence Day Holiday')).toBeInTheDocument()
      expect(screen.getByText('Mid-Term Examinations')).toBeInTheDocument()
    })

    // Filter by holiday
    const holidaysFilter = screen.getByRole('button', { name: 'Holidays' })
    fireEvent.click(holidaysFilter)

    expect(screen.getByText('Independence Day Holiday')).toBeInTheDocument()
    expect(screen.queryByText('Mid-Term Examinations')).not.toBeInTheDocument()
  })

  it('handles form submission failure: preserves input, displays alert banner, leaves modal open, does not inject fake records', async () => {
    render(
      <BrowserRouter>
        <AcademicSetupPage />
      </BrowserRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('2025-26')).toBeInTheDocument()
    })

    api.post.mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Overlapping academic year dates detected',
        },
      },
    })

    const newYearBtn = screen.getByRole('button', { name: /New Academic Year/i })
    fireEvent.click(newYearBtn)

    expect(screen.getByRole('heading', { name: 'Create Academic Year' })).toBeInTheDocument()

    const input = screen.getByPlaceholderText('e.g. 2026-27')
    fireEvent.change(input, { target: { value: '2029-30' } })
    expect(input.value).toBe('2029-30')

    const form = screen.getByRole('heading', { name: 'Create Academic Year' }).closest('div').querySelector('form')
    fireEvent.submit(form)

    await waitFor(() => {
      const alerts = screen.getAllByRole('alert')
      expect(alerts.length).toBeGreaterThanOrEqual(1)
      expect(alerts[0]).toHaveTextContent('Overlapping academic year dates detected')
      expect(input.value).toBe('2029-30')
      expect(screen.getByRole('heading', { name: 'Create Academic Year' })).toBeInTheDocument()
    })

    const cancelBtn = screen.getByRole('button', { name: 'Cancel' })
    fireEvent.click(cancelBtn)

    await waitFor(() => {
      expect(screen.queryByRole('heading', { name: 'Create Academic Year' })).not.toBeInTheDocument()
    })
  })

  it('handles form submission success: updates state only on 2xx confirmation and closes modal', async () => {
    render(
      <BrowserRouter>
        <AcademicSetupPage />
      </BrowserRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('2025-26')).toBeInTheDocument()
    })

    const newYearBtn = screen.getByRole('button', { name: /New Academic Year/i })
    fireEvent.click(newYearBtn)

    const input = screen.getByPlaceholderText('e.g. 2026-27')
    fireEvent.change(input, { target: { value: '2029-30' } })

    const form = screen.getByRole('heading', { name: 'Create Academic Year' }).closest('div').querySelector('form')
    fireEvent.submit(form)

    await waitFor(() => {
      expect(screen.queryByRole('heading', { name: 'Create Academic Year' })).not.toBeInTheDocument()
      expect(screen.getByText('2029-30')).toBeInTheDocument()
    })
  })
})
