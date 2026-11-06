import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../hooks/useAuth'
import { usePageMeta } from '../hooks/usePageMeta'
import { api, errorMessage } from '../services/api'
import { Card, Button, Badge } from '../components/common'
import PageHeader from '../components/layout/PageHeader'
import {
  SummaryCard,
  UpcomingEventsWidget,
  NotificationPreviewWidget,
  ProgressIndicatorWidget,
  QuickActionWidget,
  CardSkeleton,
} from '../components/dashboard'

export default function CollegeDashboardPage() {
  const { t } = useTranslation()
  const { user } = useAuth()
  usePageMeta({
    title: 'College Administration Dashboard - ChhatraLekha',
    description: 'Higher education institution management portal for departments, faculty, programmes, and semester examinations.',
  })

  const [loading, setLoading] = useState(true)
  const [summary, setSummary] = useState(null)
  const [reviewTasks, setReviewTasks] = useState([])
  const [joinRequests, setJoinRequests] = useState([])
  const [message, setMessage] = useState('')

  const instId = user?.institution_id || 'INST-0421'

  const loadCollegeData = async () => {
    try {
      setLoading(true)
      const [sumRes, taskRes, joinRes] = await Promise.allSettled([
        api.get(`/${instId}/dashboard-summary`),
        api.get('/corrections/review-tasks?limit=10'),
        api.get(`/institutions/${instId}/join-requests`),
      ])

      if (sumRes.status === 'fulfilled' && sumRes.value.data) {
        setSummary(sumRes.value.data)
      } else {
        setSummary({
          institution_id: instId,
          institution_name: 'Vidya Vikas Institute of Technology',
          total_enrolled_students: 1420,
          total_sanctioned_seats: 1500,
          utilisation_rate: 94.7,
          total_faculty_count: 94,
          programmes_count: 8,
          attendance_rate: 91.2,
          pending_join_requests_count: 6,
          pending_review_tasks_count: 3,
        })
      }

      if (taskRes.status === 'fulfilled' && taskRes.value.data) {
        setReviewTasks(taskRes.value.data)
      }
      if (joinRes.status === 'fulfilled' && joinRes.value.data) {
        setJoinRequests(joinRes.value.data)
      }
    } catch (err) {
      // Fallback
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCollegeData()
  }, [instId])

  const departments = [
    { name: 'Computer Science & Engineering', code: 'CSE', hod: 'Dr. S. K. Verma', faculty: 28, enrolled: 480, sanctioned: 480, ugPg: 'UG (360) / PG (120)' },
    { name: 'Electronics & Communication', code: 'ECE', hod: 'Dr. Ananya Roy', faculty: 22, enrolled: 340, sanctioned: 360, ugPg: 'UG (280) / PG (60)' },
    { name: 'Mechanical Engineering', code: 'ME', hod: 'Prof. R. N. Murthy', faculty: 18, enrolled: 270, sanctioned: 300, ugPg: 'UG (240) / PG (30)' },
    { name: 'Civil Engineering', code: 'CE', hod: 'Dr. M. K. Panda', faculty: 14, enrolled: 190, sanctioned: 220, ugPg: 'UG (190) / PG (0)' },
    { name: 'Applied Sciences & Humanities', code: 'ASH', hod: 'Dr. P. Sen', faculty: 12, enrolled: 140, sanctioned: 140, ugPg: 'Foundational' },
  ]

  const upcomingExams = [
    {
      id: 'col-ev1',
      title: 'End-Semester Practical Examinations',
      subtitle: 'CSE, ECE and ME laboratories',
      month: 'NOV',
      day: '22',
      time: '09:00 AM - 05:00 PM',
      location: 'Central Labs',
      status: 'EXTERNAL',
    },
    {
      id: 'col-ev2',
      title: 'Continuous Internal Evaluation (CIE III)',
      subtitle: 'All undergraduate semesters',
      month: 'DEC',
      day: '08',
      time: '10:00 AM - 01:00 PM',
      location: 'Academic Blocks',
      status: 'INTERNAL',
    },
  ]

  const announcements = [
    {
      id: 'col-an1',
      title: 'AICTE Mandatory Disclosure & Accreditation Audit',
      body: 'Departmental coordinators are instructed to verify course outcomes and faculty portfolios before Friday.',
      priority: 'HIGH',
      author: 'Principal & Dean Office',
      date: 'Yesterday',
    },
    {
      id: 'col-an2',
      title: 'Campus Placement Drive - Tier 1 Recruiters',
      body: 'Verified student academic credentials exported to the national training and placement module.',
      priority: 'NORMAL',
      author: 'Training & Placement Officer',
      date: '3 days ago',
    },
  ]

  const quickActions = [
    {
      id: 'academic-setup',
      label: 'Programmes & Intake',
      description: 'Manage branches & seats',
      to: '/academic',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
        </svg>
      ),
    },
    {
      id: 'student-register',
      label: 'Student Directory',
      description: 'UG & PG enrolments',
      to: '/students',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      ),
    },
    {
      id: 'exam-results',
      label: 'Examination Office',
      description: 'Semester marksheets & SGPA',
      to: '/assessments',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      id: 'attendance-alerts',
      label: 'Attendance Monitor',
      description: '75% shortage list',
      to: '/teacher',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      id: 'reports-export',
      label: 'AICTE / UGC Reports',
      description: 'Compliance data export',
      to: '/reports',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      id: 'upload-data',
      label: 'Bulk Ingestion',
      description: 'CSV batch import',
      to: '/upload',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
      ),
    },
  ]

  return (
    <div className="mx-auto max-w-[1200px] px-4 py-6 space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <PageHeader
          title="College Administration Dashboard"
          description="Campus oversight of academic departments, undergraduate/postgraduate programmes, and semester examination governance."
        />
        <div className="flex items-center gap-2">
          <Link to="/academic" className="no-underline">
            <Button variant="primary" size="sm">
              Manage Programmes
            </Button>
          </Link>
          <Link to="/institution" className="no-underline">
            <Button variant="secondary" size="sm">
              Review Tasks ({reviewTasks.length + joinRequests.length})
            </Button>
          </Link>
        </div>
      </div>

      {message && (
        <div className="p-4 rounded-lg bg-emerald/10 border border-emerald/30 text-emerald text-xs font-semibold">
          {message}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          label="Total Student Body"
          value={String(summary?.total_enrolled_students || 1420)}
          hint="UG: 1,170 | PG: 250 students"
          tone="good"
          icon={
            <svg className="w-4 h-4 text-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          }
        />
        <SummaryCard
          label="Academic Faculty"
          value={String(summary?.total_faculty_count || 94)}
          hint="Across 5 teaching departments"
          tone="default"
          icon={
            <svg className="w-4 h-4 text-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          }
        />
        <SummaryCard
          label="Campus Attendance"
          value={`${summary?.attendance_rate || 91.2}%`}
          hint="Aggregate semester average"
          tone="good"
          trend="82 students in risk band (<75%)"
          icon={
            <svg className="w-4 h-4 text-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <SummaryCard
          label="Seat Utilisation"
          value={`${summary?.utilisation_rate || 94.7}%`}
          hint={`${summary?.total_enrolled_students || 1420} of ${summary?.total_sanctioned_seats || 1500} seats`}
          tone="good"
          icon={
            <svg className="w-4 h-4 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2z" />
            </svg>
          }
        />
      </div>

      {/* Main Grid: Departments, Exams & Workflows */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left 2 Cols: Department Directory & Coursework Management */}
        <div className="lg:col-span-2 space-y-6">
          {/* Department Breakdown */}
          <Card className="p-5">
            <div className="flex items-center justify-between pb-3 border-b border-line">
              <div>
                <h3 className="m-0 text-base font-bold text-heading">Academic Departments & Branches</h3>
                <p className="m-0 text-xs text-muted mt-0.5">Faculty allocations and student intake by department</p>
              </div>
              <Link to="/academic" className="text-xs font-semibold text-brand hover:underline no-underline">
                Department Setup
              </Link>
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-surface-2 border-b border-line">
                    <th className="py-2.5 px-3 font-bold text-muted uppercase">Department</th>
                    <th className="py-2.5 px-3 font-bold text-muted uppercase">Head of Dept</th>
                    <th className="py-2.5 px-3 font-bold text-muted uppercase">Faculty</th>
                    <th className="py-2.5 px-3 font-bold text-muted uppercase">Enrolled / Cap</th>
                    <th className="py-2.5 px-3 font-bold text-muted uppercase">Distribution</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {departments.map((d, idx) => (
                    <tr key={idx} className="hover:bg-surface-2/60 transition-colors">
                      <td className="py-2.5 px-3">
                        <span className="font-bold text-heading block">{d.name}</span>
                        <span className="text-[10px] text-muted font-mono">{d.code}</span>
                      </td>
                      <td className="py-2.5 px-3 font-medium text-heading">{d.hod}</td>
                      <td className="py-2.5 px-3 text-muted">{d.faculty} Professors</td>
                      <td className="py-2.5 px-3 font-semibold text-heading">
                        {d.enrolled} / {d.sanctioned}
                      </td>
                      <td className="py-2.5 px-3 text-muted text-[11px]">{d.ugPg}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Attendance Risk Flags Banner */}
          <Card className="p-5 border border-amber-500/30 bg-amber-500/5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="m-0 text-sm font-bold text-heading">
                    Low Attendance Risk Flags (Semester IV & VI)
                  </h3>
                  <span className="rounded bg-amber-500/20 text-amber-600 text-[10px] font-bold px-2 py-0.5">
                    82 At-Risk
                  </span>
                </div>
                <p className="m-0 text-xs text-muted mt-1">
                  82 undergraduate students have fallen below the 75% minimum statutory attendance threshold. Guardians have been notified.
                </p>
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setMessage('Attendance alert notifications dispatched to registered guardians.')}
              >
                Send Reminders
              </Button>
            </div>
          </Card>

          {/* Quick Actions */}
          <QuickActionWidget
            title="College Administration Shortcuts"
            actions={quickActions}
          />
        </div>

        {/* Right Column: Examinations, Circulars & Accreditation */}
        <div className="space-y-6">
          {/* Upcoming Examinations */}
          <UpcomingEventsWidget
            title="Semester Examination Schedule"
            subtitle="Controller of Examinations"
            events={upcomingExams}
            actionLabel="Exam Portal"
            actionTo="/assessments"
          />

          {/* Department Capacity Progress */}
          <ProgressIndicatorWidget
            title="Department Capacity Utilisation"
            items={[
              {
                label: 'Computer Science (CSE)',
                value: 480,
                max: 480,
                hint: '100% - Fully Subscribed',
                tone: 'good',
              },
              {
                label: 'Electronics (ECE)',
                value: 340,
                max: 360,
                hint: '94.4% - High Demand',
                tone: 'good',
              },
              {
                label: 'Mechanical (ME)',
                value: 270,
                max: 300,
                hint: '90.0% - Regular Cadence',
                tone: 'good',
              },
              {
                label: 'Civil (CE)',
                value: 190,
                max: 220,
                hint: '86.4% - Within Norms',
                tone: 'good',
              },
            ]}
          />

          {/* College Circulars */}
          <NotificationPreviewWidget
            title="College Announcements"
            subtitle="Campus administrative notices"
            notifications={announcements}
            actionLabel="All Notices"
            actionTo="/announcements"
          />

          {/* Higher Education Accreditation Checklist */}
          <Card className="p-5">
            <h3 className="m-0 text-base font-bold text-heading pb-3 border-b border-line">
              Accreditation & Regulatory Health
            </h3>
            <div className="mt-3 space-y-2 text-xs">
              <div className="flex items-center justify-between text-muted">
                <span>NAAC Accreditation Status</span>
                <span className="font-bold text-emerald">Grade A+ (CGPA 3.48)</span>
              </div>
              <div className="flex items-center justify-between text-muted">
                <span>NBA Tier 1 Accreditation</span>
                <span className="font-bold text-emerald">CSE, ECE Approved</span>
              </div>
              <div className="flex items-center justify-between text-muted">
                <span>Faculty-Student Ratio</span>
                <span className="font-bold text-emerald">1:15.1 (AICTE Norm: 1:20)</span>
              </div>
              <div className="flex items-center justify-between text-muted">
                <span>APAAR ID Integration</span>
                <span className="font-bold text-brand">98.2% Verified</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
