import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { api, tokenStore } from '../services/api'
import { AuthProvider } from '../hooks/useAuth'
import StudentHomePage from '../pages/student/StudentHomePage'
import ParentPortalPage from '../pages/ParentPortalPage'
import TeacherWorkspacePage from '../pages/TeacherWorkspacePage'
import SchoolDashboardPage from '../pages/SchoolDashboardPage'
import CollegeDashboardPage from '../pages/CollegeDashboardPage'
import UniversityDashboardPage from '../pages/UniversityDashboardPage'
import {
  Breadcrumbs,
  UserProfileMenu,
  SummaryCard,
  UpcomingEventsWidget,
  ProgressIndicatorWidget,
  DataTableWidget,
  QuickActionWidget,
} from '../components/dashboard'
import {
  NAVIGATION_GROUPS,
  ROLE_DEFAULT_NAVIGATIONS,
} from '../modules/navigation/NavigationConfig'

describe('Stage 0.6: Role-Based Dashboards & Core Navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    api.get = vi.fn().mockResolvedValue({ data: [] })
    api.post = vi.fn().mockResolvedValue({ data: {} })
    api.patch = vi.fn().mockResolvedValue({ data: {} })
  })

  describe('Core Navigation Configuration & Registry', () => {
    it('defines all required shared navigation groups', () => {
      const groupIds = NAVIGATION_GROUPS.map((g) => g.id)
      expect(groupIds).toContain('dashboard')
      expect(groupIds).toContain('profile')
      expect(groupIds).toContain('academics')
      expect(groupIds).toContain('attendance')
      expect(groupIds).toContain('timetable')
      expect(groupIds).toContain('assignments')
      expect(groupIds).toContain('examinations')
      expect(groupIds).toContain('results')
      expect(groupIds).toContain('announcements')
      expect(groupIds).toContain('notifications')
      expect(groupIds).toContain('documents')
      expect(groupIds).toContain('help')
      expect(groupIds).toContain('settings')
    })

    it('configures distinct navigation items for all 6 target roles', () => {
      expect(ROLE_DEFAULT_NAVIGATIONS.student).toBeDefined()
      expect(ROLE_DEFAULT_NAVIGATIONS.parent).toBeDefined()
      expect(ROLE_DEFAULT_NAVIGATIONS.teacher).toBeDefined()
      expect(ROLE_DEFAULT_NAVIGATIONS.school_admin).toBeDefined()
      expect(ROLE_DEFAULT_NAVIGATIONS.college_admin).toBeDefined()
      expect(ROLE_DEFAULT_NAVIGATIONS.university_admin).toBeDefined()

      // Verify Student routes
      const studentPaths = ROLE_DEFAULT_NAVIGATIONS.student.map((i) => i.to)
      expect(studentPaths).toContain('/me')
      expect(studentPaths).toContain('/me/attendance')
      expect(studentPaths).toContain('/me/timetable')
      expect(studentPaths).toContain('/me/assignments')

      // Verify Parent routes
      const parentPaths = ROLE_DEFAULT_NAVIGATIONS.parent.map((i) => i.to)
      expect(parentPaths).toContain('/parent')

      // Verify School Admin routes
      const schoolPaths = ROLE_DEFAULT_NAVIGATIONS.school_admin.map((i) => i.to)
      expect(schoolPaths).toContain('/school')

      // Verify College Admin routes
      const collegePaths = ROLE_DEFAULT_NAVIGATIONS.college_admin.map((i) => i.to)
      expect(collegePaths).toContain('/college')

      // Verify University Admin routes
      const univPaths = ROLE_DEFAULT_NAVIGATIONS.university_admin.map((i) => i.to)
      expect(univPaths).toContain('/university')
    })
  })

  describe('Reusable Dashboard Components', () => {
    it('renders SummaryCard with label, value, hint and tone', () => {
      render(
        <SummaryCard
          label="Attendance Rate"
          value="94.5%"
          hint="Above mandatory threshold"
          tone="good"
          trend="+2.1% from last month"
        />,
      )
      expect(screen.getByText('Attendance Rate')).toBeInTheDocument()
      expect(screen.getByText('94.5%')).toBeInTheDocument()
      expect(screen.getByText('Above mandatory threshold')).toBeInTheDocument()
      expect(screen.getByText('+2.1% from last month')).toBeInTheDocument()
    })

    it('renders UpcomingEventsWidget with event entries and action link', () => {
      const mockEvents = [
        {
          id: 'ev-1',
          title: 'Mathematics Examination',
          subtitle: 'Room 302',
          month: 'NOV',
          day: '15',
          time: '10:00 AM',
          location: 'Main Block',
        },
      ]
      render(
        <MemoryRouter>
          <UpcomingEventsWidget
            title="Upcoming Examinations"
            events={mockEvents}
            actionLabel="View All"
            actionTo="/assessments"
          />
        </MemoryRouter>,
      )
      expect(screen.getByText('Upcoming Examinations')).toBeInTheDocument()
      expect(screen.getByText('Mathematics Examination')).toBeInTheDocument()
      expect(screen.getByText('Room 302')).toBeInTheDocument()
      expect(screen.getByText('10:00 AM')).toBeInTheDocument()
    })

    it('renders ProgressIndicatorWidget with calculated percentage and accessible bar', () => {
      render(
        <ProgressIndicatorWidget
          title="Attendance Quota"
          items={[
            {
              label: 'Theory Classes',
              value: 45,
              max: 50,
              target: '50 sessions',
              hint: 'Compliant with 75% rule',
              tone: 'good',
            },
          ]}
        />,
      )
      expect(screen.getByText('Attendance Quota')).toBeInTheDocument()
      expect(screen.getByText('Theory Classes')).toBeInTheDocument()
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '90')
    })

    it('renders DataTableWidget with column headers and search filtering', () => {
      const columns = [
        { key: 'name', header: 'Student Name' },
        { key: 'roll', header: 'Roll Number' },
      ]
      const data = [
        { id: 1, name: 'Alice Smith', roll: 'CS-001' },
        { id: 2, name: 'Bob Jones', roll: 'CS-002' },
      ]
      render(
        <DataTableWidget
          title="Student Register"
          columns={columns}
          data={data}
          searchable={true}
        />,
      )
      expect(screen.getByText('Student Register')).toBeInTheDocument()
      expect(screen.getByText('Alice Smith')).toBeInTheDocument()
      expect(screen.getByText('Bob Jones')).toBeInTheDocument()

      const searchInput = screen.getByPlaceholderText('Search records...')
      fireEvent.change(searchInput, { target: { value: 'Alice' } })
      expect(screen.getByText('Alice Smith')).toBeInTheDocument()
      expect(screen.queryByText('Bob Jones')).not.toBeInTheDocument()
    })

    it('renders QuickActionWidget with interactive action triggers', () => {
      const handleAction = vi.fn()
      const actions = [
        {
          id: 'act-1',
          label: 'Record Roll Call',
          description: 'Mark attendance',
          onClick: handleAction,
          icon: <span data-testid="test-icon">icon</span>,
        },
      ]
      render(<QuickActionWidget title="Faculty Actions" actions={actions} />)
      expect(screen.getByText('Faculty Actions')).toBeInTheDocument()
      const button = screen.getByText('Record Roll Call')
      fireEvent.click(button)
      expect(handleAction).toHaveBeenCalledTimes(1)
    })

    it('renders dynamic Breadcrumbs mapped from route segments', () => {
      render(
        <MemoryRouter initialEntries={['/me/assignments']}>
          <Breadcrumbs />
        </MemoryRouter>,
      )
      expect(screen.getByText('Home')).toBeInTheDocument()
      expect(screen.getByText('Student Portal')).toBeInTheDocument()
      expect(screen.getByText('Assignments')).toBeInTheDocument()
    })

    it('renders UserProfileMenu with user initials and dropdown options', () => {
      const mockLogout = vi.fn()
      tokenStore.set({
        access_token: 'test-token',
        email: 'principal@school.edu.in',
        full_name: 'Dr. Ramesh Kumar',
        role: 'school_admin',
        institution_name: 'Delhi Public Model School',
      })
      render(
        <MemoryRouter>
          <AuthProvider>
            <UserProfileMenu onLogout={mockLogout} />
          </AuthProvider>
        </MemoryRouter>,
      )
      const menuTrigger = screen.getByLabelText('User account menu')
      expect(menuTrigger).toBeInTheDocument()
      fireEvent.click(menuTrigger)
      expect(screen.getAllByText('Dr. Ramesh Kumar')[0]).toBeInTheDocument()
      expect(screen.getAllByText('SCHOOL ADMIN')[0]).toBeInTheDocument()
    })
  })

  describe('Role-Specific Dashboards', () => {
    it('renders StudentHomePage with attendance metrics and timetable', async () => {
      api.get.mockImplementation((url) => {
        if (url === '/me/profile') {
          return Promise.resolve({
            data: {
              student_id: 'STU-9901',
              student_name: 'Pooja Verma',
              program_name: 'B.Tech Information Technology',
              institution_name: 'Vidya Vikas Institute',
              record_status: 'ACTIVE',
            },
          })
        }
        if (url === '/me/dashboard') {
          return Promise.resolve({
            data: {
              student: {
                student_id: 'STU-9901',
                student_name: 'Pooja Verma',
                program_name: 'B.Tech Information Technology',
                institution_name: 'Vidya Vikas Institute',
                record_status: 'ACTIVE',
              },
              attendance: { percentage: 94.2, attended: 48, total: 51 },
              today_schedule: [
                { period: 1, time: '09:00 - 10:00 AM', subject: 'Cloud Computing', teacher: 'Prof. Rao', room: 'Lab 3' },
              ],
              upcoming_examinations: [],
              announcements: [],
              active_assignments_count: 2,
            },
          })
        }
        return Promise.resolve({ data: [] })
      })

      render(
        <MemoryRouter>
          <AuthProvider>
            <StudentHomePage />
          </AuthProvider>
        </MemoryRouter>,
      )

      await waitFor(() => {
        expect(screen.getByText('Pooja Verma')).toBeInTheDocument()
      })
      expect(screen.getByText(/Attendance Rate/i)).toBeInTheDocument()
      expect(screen.getByText(/Cloud Computing/i)).toBeInTheDocument()
    })

    it('renders ParentPortalPage with child selector and verified timetable', async () => {
      api.get.mockImplementation((url) => {
        if (url === '/parent/children') {
          return Promise.resolve({
            data: [
              {
                link_id: 'GLINK-01',
                student_id: 'STU-CHILD-01',
                student_name: 'Aryan Sharma',
                institution_name: 'Delhi Model School',
                class_or_programme: 'Class 10-A',
                relationship: 'FATHER',
                verification_status: 'VERIFIED',
                attendance_percentage: 95.0,
                total_sessions: 40,
                present_sessions: 38,
                published_results: [],
                recent_notices: [],
              },
            ],
          })
        }
        if (url.includes('/parent/children/STU-CHILD-01/timetable')) {
          return Promise.resolve({
            data: [
              { period: 1, time: '09:00 - 09:45 AM', subject: 'Mathematics', teacher: 'Dr. Sharma', room: 'Room 102' },
            ],
          })
        }
        return Promise.resolve({ data: [] })
      })

      render(
        <MemoryRouter>
          <AuthProvider>
            <ParentPortalPage />
          </AuthProvider>
        </MemoryRouter>,
      )

      await waitFor(() => {
        expect(screen.getByText('Aryan Sharma')).toBeInTheDocument()
      })
      expect(screen.getByText('Class 10-A - Delhi Model School')).toBeInTheDocument()
      expect(screen.getByText(/Parent & Guardian Portal/i)).toBeInTheDocument()
    })

    it('renders TeacherWorkspacePage with assigned classes and roll call trigger', async () => {
      api.get.mockImplementation((url) => {
        if (url === '/teacher/dashboard') {
          return Promise.resolve({
            data: {
              assigned_classes_count: 3,
              today_lectures_count: 2,
              active_assignments_count: 4,
              average_attendance_rate: 93.5,
            },
          })
        }
        if (url === '/teacher/classes') {
          return Promise.resolve({
            data: [
              { target_id: 'CLS-10A', target_label: 'Class 10-A', subject_name: 'Physics' },
            ],
          })
        }
        if (url === '/teacher/timetable') {
          return Promise.resolve({
            data: [
              { day: 'Monday', period: 1, time: '09:00 AM', target_label: 'Class 10-A', subject_name: 'Physics', room: 'Lab 1' },
            ],
          })
        }
        if (url === '/teacher/assignments') {
          return Promise.resolve({
            data: [
              { assignment_id: 'ASN-1', title: 'Optics Problem Set', target_label: 'Class 10-A', subject_name: 'Physics', due_date: '2026-11-20', max_marks: 25, submissions_count: 28 },
            ],
          })
        }
        return Promise.resolve({ data: [] })
      })

      render(
        <MemoryRouter>
          <AuthProvider>
            <TeacherWorkspacePage />
          </AuthProvider>
        </MemoryRouter>,
      )

      await waitFor(() => {
        expect(screen.getAllByText('Class 10-A')[0]).toBeInTheDocument()
      })
      expect(screen.getByText('Record Class Attendance')).toBeInTheDocument()
      expect(screen.getByText('Optics Problem Set')).toBeInTheDocument()
    })

    it('renders SchoolDashboardPage with grade cohorts and admissions TC cards', async () => {
      api.get.mockImplementation((url) => {
        if (url.includes('/dashboard-summary')) {
          return Promise.resolve({
            data: {
              institution_id: 'INST-SCH-01',
              institution_name: 'St. Mary High School',
              total_enrolled_students: 840,
              total_sanctioned_seats: 900,
              utilisation_rate: 93.3,
              total_faculty_count: 48,
              programmes_count: 10,
              attendance_rate: 95.1,
              pending_join_requests_count: 3,
              pending_review_tasks_count: 2,
            },
          })
        }
        return Promise.resolve({ data: [] })
      })

      render(
        <MemoryRouter>
          <AuthProvider>
            <SchoolDashboardPage />
          </AuthProvider>
        </MemoryRouter>,
      )

      await waitFor(() => {
        expect(screen.getByText('School Administration Dashboard')).toBeInTheDocument()
      })
      expect(screen.getByText('Grade Cohort & Section Register')).toBeInTheDocument()
      expect(screen.getByText('Admissions & Transfer Certificates (TC)')).toBeInTheDocument()
      expect(screen.getByText('Statutory Board Compliance')).toBeInTheDocument()
    })

    it('renders CollegeDashboardPage with department allocations and risk flags', async () => {
      api.get.mockImplementation((url) => {
        if (url.includes('/dashboard-summary')) {
          return Promise.resolve({
            data: {
              institution_id: 'INST-COL-01',
              institution_name: 'City Engineering College',
              total_enrolled_students: 1420,
              total_sanctioned_seats: 1500,
              utilisation_rate: 94.7,
              total_faculty_count: 94,
              programmes_count: 8,
              attendance_rate: 91.5,
              pending_join_requests_count: 5,
              pending_review_tasks_count: 3,
            },
          })
        }
        return Promise.resolve({ data: [] })
      })

      render(
        <MemoryRouter>
          <AuthProvider>
            <CollegeDashboardPage />
          </AuthProvider>
        </MemoryRouter>,
      )

      await waitFor(() => {
        expect(screen.getByText('College Administration Dashboard')).toBeInTheDocument()
      })
      expect(screen.getByText('Academic Departments & Branches')).toBeInTheDocument()
      expect(screen.getByText('Accreditation & Regulatory Health')).toBeInTheDocument()
      expect(screen.getByText(/Low Attendance Risk Flags/i)).toBeInTheDocument()
    })

    it('renders UniversityDashboardPage with affiliated network and tenant isolation guarantee', async () => {
      api.get.mockImplementation((url) => {
        if (url === '/dashboard/national') {
          return Promise.resolve({
            data: {
              institution_count: 28,
              programme_count: 92,
              total_enrolled: 32000,
              total_sanctioned: 35000,
              utilisation_percent: 91.4,
              flagged_anomalies: 6,
              critical_anomalies: 0,
            },
          })
        }
        if (url === '/institutions') {
          return Promise.resolve({
            data: [
              { institution_id: 'INST-01', name: 'Metro Institute of Tech', category: 'COLLEGE', city: 'Delhi', approved_programmes: 8, total_enrolled: 2500, capacity: 2600, compliance_status: 'COMPLIANT' },
            ],
          })
        }
        return Promise.resolve({ data: [] })
      })

      render(
        <MemoryRouter>
          <AuthProvider>
            <UniversityDashboardPage />
          </AuthProvider>
        </MemoryRouter>,
      )

      await waitFor(() => {
        expect(screen.getByText('University & National Oversight Dashboard')).toBeInTheDocument()
      })
      // Verify Tenant Data Isolation notice is rendered
      expect(screen.getByText(/Tenant Data Isolation & Statutory Privacy Invariant/i)).toBeInTheDocument()
      expect(screen.getByText('Affiliated Institutions Network')).toBeInTheDocument()
      expect(screen.getByText('Metro Institute of Tech')).toBeInTheDocument()
    })
  })
})
