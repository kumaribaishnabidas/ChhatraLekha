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

export default function SchoolDashboardPage() {
  const { t } = useTranslation()
  const { user } = useAuth()
  usePageMeta({
    title: 'School Administration Dashboard - ChhatraLekha',
    description: 'School principal and administrative management portal for classes, teachers, student attendance and admissions.',
  })

  const [loading, setLoading] = useState(true)
  const [summary, setSummary] = useState(null)
  const [reviewTasks, setReviewTasks] = useState([])
  const [joinRequests, setJoinRequests] = useState([])
  const [message, setMessage] = useState('')

  const instId = user?.institution_id || 'INST-0421'

  const loadSchoolData = async () => {
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
        // Fallback demo summary
        setSummary({
          institution_id: instId,
          institution_name: 'Delhi Public Model School',
          total_enrolled_students: 840,
          total_sanctioned_seats: 900,
          utilisation_rate: 93.3,
          total_faculty_count: 48,
          programmes_count: 12,
          attendance_rate: 94.6,
          pending_join_requests_count: 4,
          pending_review_tasks_count: 2,
        })
      }

      if (taskRes.status === 'fulfilled' && taskRes.value.data) {
        setReviewTasks(taskRes.value.data)
      }
      if (joinRes.status === 'fulfilled' && joinRes.value.data) {
        setJoinRequests(joinRes.value.data)
      }
    } catch (err) {
      // Handled through fallbacks
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSchoolData()
  }, [instId])

  const classCohorts = [
    { grade: 'Class 10', sections: 'A, B, C', enrolled: 120, sanctioned: 120, boys: 62, girls: 58, classTeacher: 'Dr. Sharma' },
    { grade: 'Class 9', sections: 'A, B, C', enrolled: 115, sanctioned: 120, boys: 59, girls: 56, classTeacher: 'Mrs. Verma' },
    { grade: 'Class 8', sections: 'A, B', enrolled: 78, sanctioned: 80, boys: 40, girls: 38, classTeacher: 'Mr. Gupta' },
    { grade: 'Class 7', sections: 'A, B', enrolled: 76, sanctioned: 80, boys: 39, girls: 37, classTeacher: 'Mrs. Sen' },
    { grade: 'Primary (1-5)', sections: '10 Sections', enrolled: 451, sanctioned: 500, boys: 231, girls: 220, classTeacher: 'Junior Wing Head' },
  ]

  const upcomingEvents = [
    {
      id: 'sch-ev1',
      title: 'Periodic Assessment II Examination',
      subtitle: 'Grades 6 to 10 - Centralized hall schedule',
      month: 'NOV',
      day: '17',
      time: '09:00 AM - 12:00 PM',
      location: 'Secondary Wing',
      status: 'SCHEDULED',
    },
    {
      id: 'sch-ev2',
      title: 'Annual Sports & Athletic Meet',
      subtitle: 'Inter-house athletic finals',
      month: 'DEC',
      day: '04',
      time: '08:30 AM onwards',
      location: 'Main Oval Ground',
      status: 'PLANNED',
    },
  ]

  const announcements = [
    {
      id: 'sch-an1',
      title: 'Admissions Open for Academic Session 2026-27',
      body: 'Online registration for nursery and Grade 1 admissions opens next Monday. Notification dispatched to portal.',
      priority: 'HIGH',
      author: 'Principal Office',
      date: 'Yesterday',
    },
    {
      id: 'sch-an2',
      title: 'State Education Board Compliance Submission',
      body: 'Verified student strength and staff roster uploaded to the national registry.',
      priority: 'NORMAL',
      author: 'Administrative Officer',
      date: '4 days ago',
    },
  ]

  const quickActions = [
    {
      id: 'admit-student',
      label: 'New Admission',
      description: 'Enrol student record',
      to: '/students',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
        </svg>
      ),
    },
    {
      id: 'issue-tc',
      label: 'Transfer Certificate',
      description: 'Issue verified TC',
      onClick: () => setMessage('Transfer Certificate workflow opened.'),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      id: 'publish-notice',
      label: 'Publish Notice',
      description: 'Broadcast to parents & staff',
      to: '/announcements',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
        </svg>
      ),
    },
    {
      id: 'attendance-register',
      label: 'Daily Roll Call',
      description: 'Review cohort attendance',
      to: '/teacher',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      id: 'compliance-report',
      label: 'Board Reports',
      description: 'CBSE & State exports',
      to: '/reports',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      id: 'import-csv',
      label: 'Bulk Data Upload',
      description: 'Import student roster',
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
          title="School Administration Dashboard"
          description="Institutional overview of grade cohorts, staff assignments, daily attendance and admissions management."
        />
        <div className="flex items-center gap-2">
          <Link to="/students" className="no-underline">
            <Button variant="primary" size="sm">
              Student Register
            </Button>
          </Link>
          <Link to="/reports" className="no-underline">
            <Button variant="secondary" size="sm">
              Generate Reports
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
          label="Total Enrolment"
          value={String(summary?.total_enrolled_students || 840)}
          hint={`${summary?.total_sanctioned_seats || 900} sanctioned capacity (${summary?.utilisation_rate || 93.3}% capacity)`}
          tone="good"
          icon={
            <svg className="w-4 h-4 text-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          }
        />
        <SummaryCard
          label="Teaching Staff"
          value={String(summary?.total_faculty_count || 48)}
          hint="Assigned faculty & coordinators"
          tone="default"
          icon={
            <svg className="w-4 h-4 text-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          }
        />
        <SummaryCard
          label="Daily Attendance Rate"
          value={`${summary?.attendance_rate || 94.6}%`}
          hint="Today's aggregate across all grades"
          tone="good"
          trend="Above 90% Target"
          icon={
            <svg className="w-4 h-4 text-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <SummaryCard
          label="Pending Review Tasks"
          value={String(summary?.pending_review_tasks_count || reviewTasks.length)}
          hint="Admission & correction audits"
          tone={summary?.pending_review_tasks_count > 0 ? 'warning' : 'default'}
          icon={
            <svg className="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          }
        />
      </div>

      {/* Main Grid: Cohort Breakdown & Quick Workflows */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left 2 Cols: Grade-wise Enrolment Table & Quick Actions */}
        <div className="lg:col-span-2 space-y-6">
          {/* Grade / Section Enrolment Table */}
          <Card className="p-5">
            <div className="flex items-center justify-between pb-3 border-b border-line">
              <div>
                <h3 className="m-0 text-base font-bold text-heading">Grade Cohort & Section Register</h3>
                <p className="m-0 text-xs text-muted mt-0.5">Enrolment distribution by grade and gender</p>
              </div>
              <Link to="/students" className="text-xs font-semibold text-brand hover:underline no-underline">
                Full Register
              </Link>
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-surface-2 border-b border-line">
                    <th className="py-2.5 px-3 font-bold text-muted uppercase">Grade</th>
                    <th className="py-2.5 px-3 font-bold text-muted uppercase">Sections</th>
                    <th className="py-2.5 px-3 font-bold text-muted uppercase">Enrolled / Cap</th>
                    <th className="py-2.5 px-3 font-bold text-muted uppercase">Boys / Girls</th>
                    <th className="py-2.5 px-3 font-bold text-muted uppercase">Class Teacher</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {classCohorts.map((row, idx) => (
                    <tr key={idx} className="hover:bg-surface-2/60 transition-colors">
                      <td className="py-2.5 px-3 font-bold text-heading">{row.grade}</td>
                      <td className="py-2.5 px-3 text-muted">{row.sections}</td>
                      <td className="py-2.5 px-3 font-semibold text-heading">
                        {row.enrolled} / {row.sanctioned}
                      </td>
                      <td className="py-2.5 px-3 text-muted">
                        {row.boys} B / {row.girls} G
                      </td>
                      <td className="py-2.5 px-3 font-medium text-heading">{row.classTeacher}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Admissions & Transfer Certificate Card */}
          <Card className="p-5">
            <div className="flex items-center justify-between pb-3 border-b border-line">
              <div>
                <h3 className="m-0 text-base font-bold text-heading">Admissions & Transfer Certificates (TC)</h3>
                <p className="m-0 text-xs text-muted mt-0.5">Workflow for new enrolments and statutory school leaver documentation</p>
              </div>
              <span className="rounded-full bg-emerald/10 text-emerald text-[10px] font-bold px-2 py-0.5">
                Active Session
              </span>
            </div>

            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-lg border border-line bg-surface-2 space-y-1">
                <span className="text-muted font-semibold uppercase text-[10px]">Pending Admissions</span>
                <p className="m-0 text-xl font-black text-heading">14 Applications</p>
                <p className="m-0 text-[11px] text-muted">Awaiting document verification and fee clearance.</p>
                <div className="pt-2">
                  <Link to="/students" className="text-brand font-bold text-xs hover:underline no-underline">
                    Process Applications &rarr;
                  </Link>
                </div>
              </div>

              <div className="p-3 rounded-lg border border-line bg-surface-2 space-y-1">
                <span className="text-muted font-semibold uppercase text-[10px]">Issued TC This Term</span>
                <p className="m-0 text-xl font-black text-heading">6 Certificates</p>
                <p className="m-0 text-[11px] text-muted">Cryptographically verified opaque QR tokens printed.</p>
                <div className="pt-2">
                  <button
                    type="button"
                    onClick={() => setMessage('Transfer certificate issuance dialogue initialized.')}
                    className="text-brand font-bold text-xs hover:underline bg-transparent border-0 p-0 cursor-pointer"
                  >
                    Generate New TC &rarr;
                  </button>
                </div>
              </div>
            </div>
          </Card>

          {/* Quick Actions */}
          <QuickActionWidget
            title="School Administrative Actions"
            actions={quickActions}
          />
        </div>

        {/* Right Column: Calendar, Notices & Compliance */}
        <div className="space-y-6">
          {/* Academic Calendar Events */}
          <UpcomingEventsWidget
            title="Academic Calendar"
            subtitle="Important school dates & milestones"
            events={upcomingEvents}
            actionLabel="Full Calendar"
            actionTo="/academic"
          />

          {/* Capacity Progress */}
          <ProgressIndicatorWidget
            title="Sanctioned Seat Utilisation"
            items={[
              {
                label: 'Secondary Wing (Classes 8-10)',
                value: 313,
                max: 320,
                hint: '97.8% Capacity Utilised',
                tone: 'good',
              },
              {
                label: 'Middle Wing (Classes 6-7)',
                value: 154,
                max: 160,
                hint: '96.2% Capacity Utilised',
                tone: 'good',
              },
              {
                label: 'Primary Wing (Classes 1-5)',
                value: 451,
                max: 500,
                hint: '90.2% Capacity Utilised',
                tone: 'good',
              },
            ]}
          />

          {/* School Announcements */}
          <NotificationPreviewWidget
            title="School Circulars"
            subtitle="Campus and board directives"
            notifications={announcements}
            actionLabel="Manage Circulars"
            actionTo="/announcements"
          />

          {/* Administrative Compliance Checklist */}
          <Card className="p-5">
            <h3 className="m-0 text-base font-bold text-heading pb-3 border-b border-line">
              Statutory Board Compliance
            </h3>
            <div className="mt-3 space-y-2 text-xs">
              <div className="flex items-center justify-between text-muted">
                <span>Teacher-Student Ratio (1:25)</span>
                <span className="font-bold text-emerald">Compliant (1:17.5)</span>
              </div>
              <div className="flex items-center justify-between text-muted">
                <span>APAAR ID Seeding Rate</span>
                <span className="font-bold text-emerald">96.8% Seeded</span>
              </div>
              <div className="flex items-center justify-between text-muted">
                <span>Fire & Safety Clearance</span>
                <span className="font-bold text-emerald">Valid until 2027</span>
              </div>
              <div className="flex items-center justify-between text-muted">
                <span>Quarterly Attendance Audit</span>
                <span className="font-bold text-brand">Filed</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
