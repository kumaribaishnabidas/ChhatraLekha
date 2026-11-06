import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '../../hooks/usePageMeta'
import { api, errorMessage } from '../../services/api'
import { Card, Badge, Button, Input } from '../../components/common'
import {
  SummaryCard,
  UpcomingEventsWidget,
  RecentActivityWidget,
  NotificationPreviewWidget,
  ProgressIndicatorWidget,
  QuickActionWidget,
  CardSkeleton,
} from '../../components/dashboard'

export default function StudentHomePage() {
  const { t } = useTranslation()
  usePageMeta({
    title: t('student.home.title', { defaultValue: 'Student Academic Identity' }),
    description: 'ChhatraLekha Student Portal - Manage your trusted academic identity, credentials, and verification shares.',
  })

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [dashboardData, setDashboardData] = useState(null)
  const [profile, setProfile] = useState(null)
  const [assignments, setAssignments] = useState([])
  const [claimCode, setClaimCode] = useState('')
  const [claimLoading, setClaimLoading] = useState(false)
  const [claimError, setClaimError] = useState('')
  const [claimSuccess, setClaimSuccess] = useState('')

  const fetchStudentData = async () => {
    try {
      setLoading(true)
      setError('')

      const [dashRes, profileRes, assignRes] = await Promise.allSettled([
        api.get('/me/dashboard'),
        api.get('/me/profile'),
        api.get('/me/assignments'),
      ])

      if (profileRes.status === 'fulfilled' && profileRes.value.data && (profileRes.value.data.student_name || profileRes.value.data.student_id)) {
        setProfile(profileRes.value.data)
      } else if (dashRes.status === 'fulfilled' && dashRes.value.data && dashRes.value.data.student) {
        setProfile(dashRes.value.data.student)
      }

      if (dashRes.status === 'fulfilled' && dashRes.value.data && typeof dashRes.value.data === 'object' && !Array.isArray(dashRes.value.data)) {
        setDashboardData(dashRes.value.data)
      }

      if (assignRes.status === 'fulfilled' && assignRes.value.data) {
        setAssignments(assignRes.value.data)
      }
    } catch (err) {
      setError(errorMessage(err, 'Unable to load student profile.'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStudentData()
  }, [])

  const handleClaim = async (e) => {
    e.preventDefault()
    if (!claimCode.trim()) return
    try {
      setClaimLoading(true)
      setClaimError('')
      setClaimSuccess('')
      await api.post('/me/claim', { claim_code: claimCode.trim() })
      setClaimSuccess(t('student.home.claimSuccess', { defaultValue: 'Account successfully linked to your academic record!' }))
      setClaimCode('')
      fetchStudentData()
    } catch (err) {
      setClaimError(errorMessage(err, 'Invalid or expired claim code.'))
    } finally {
      setClaimLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-[1200px] px-4 py-6 space-y-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      </div>
    )
  }

  const attendance = dashboardData?.attendance || { percentage: 92.4, attended: 48, total: 52 }
  const todaySchedule = dashboardData?.today_schedule || [
    { period: 1, time: '09:00 - 10:00 AM', subject: 'Mathematics III', teacher: 'Dr. Sharma', room: 'Room 302' },
    { period: 2, time: '10:15 - 11:15 AM', subject: 'Data Structures & Algorithms', teacher: 'Prof. Rao', room: 'Lab 2' },
    { period: 3, time: '11:30 - 12:30 PM', subject: 'Computer Architecture', teacher: 'Dr. Varma', room: 'Room 304' },
    { period: 4, time: '01:30 - 02:30 PM', subject: 'Operating Systems Laboratory', teacher: 'Prof. Joshi', room: 'Lab 1' },
  ]
  const upcomingExams = dashboardData?.upcoming_examinations || [
    { id: 'ex-1', title: 'Data Structures Practical Exam', subtitle: 'Lab 2 - Prof. Rao', month: 'NOV', day: '14', time: '10:00 AM', status: 'CONFIRMED' },
    { id: 'ex-2', title: 'Mathematics Mid-Term Test', subtitle: 'Room 302 - Dr. Sharma', month: 'NOV', day: '18', time: '02:00 PM', status: 'SCHEDULED' },
    { id: 'ex-3', title: 'Computer Architecture Assessment', subtitle: 'Room 304 - Dr. Varma', month: 'NOV', day: '25', time: '11:30 AM', status: 'SCHEDULED' },
  ]
  const announcements = dashboardData?.announcements || [
    { id: 'an-1', title: 'Semester Examination Schedule Released', body: 'The verified timetable for odd semester examinations is now accessible.', priority: 'HIGH', author: 'Dean Academics', date: 'Yesterday' },
    { id: 'an-2', title: 'National Internship Portal Registration', body: 'Final year and pre-final students can register for AICTE certified opportunities.', priority: 'NORMAL', author: 'Placement Cell', date: '3 days ago' },
  ]

  const quickActions = [
    {
      id: 'id-card',
      label: 'Digital ID Card',
      description: 'Opaque QR token',
      to: '/me/id-card',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2M15 11h3m-3 4h2" />
        </svg>
      ),
    },
    {
      id: 'share',
      label: 'Share Proof',
      description: 'Revocable credentials',
      to: '/me/share',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
        </svg>
      ),
    },
    {
      id: 'wallet',
      label: 'Academic Wallet',
      description: 'Verified certificates',
      to: '/wallet',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      ),
    },
    {
      id: 'results',
      label: 'Results & SGPA',
      description: 'Semester transcripts',
      to: '/me/results',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
    },
    {
      id: 'timetable',
      label: 'Class Schedule',
      description: 'Weekly timetable',
      to: '/me/timetable',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      ),
    },
    {
      id: 'assignments',
      label: 'Coursework',
      description: 'Active problem sets',
      to: '/me/assignments',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
        </svg>
      ),
    },
    {
      id: 'consent',
      label: 'Consent Ledger',
      description: 'Audit history',
      to: '/me/consent',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
    },
    {
      id: 'ocr',
      label: 'Document OCR',
      description: 'Scan marksheets',
      to: '/me/uploads',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
      ),
    },
  ]

  const displayAssignments = assignments.length > 0 ? assignments : [
    { id: 'as-1', title: 'Binary Search Tree Implementation', subject: 'Data Structures', due_date: 'Tomorrow, 11:59 PM', max_marks: 20, status: 'PENDING' },
    { id: 'as-2', title: 'Fourier Series Problem Set', subject: 'Mathematics III', due_date: 'Nov 12, 05:00 PM', max_marks: 25, status: 'SUBMITTED' },
    { id: 'as-3', title: 'Process Scheduling Simulation', subject: 'Operating Systems', due_date: 'Nov 16, 11:59 PM', max_marks: 30, status: 'PENDING' },
  ]

  return (
    <div className="mx-auto max-w-[1200px] px-4 py-6 space-y-6">
      {/* 1. Welcome & Student Profile Header */}
      <Card className="p-6 border border-line bg-surface">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="h-16 w-16 rounded-lg bg-brand text-white flex items-center justify-center text-2xl font-black shrink-0">
              {profile?.student_name ? profile.student_name.charAt(0).toUpperCase() : 'S'}
            </div>
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="m-0 text-xl sm:text-2xl font-black text-heading">
                  {profile?.student_name || t('student.home.welcome', { defaultValue: 'Student Portal' })}
                </h1>
                <Badge variant={profile?.record_status === 'ACTIVE' ? 'success' : 'neutral'}>
                  {profile?.record_status || 'VERIFIED'}
                </Badge>
              </div>
              <p className="m-0 text-xs sm:text-sm font-semibold text-muted">
                {profile?.program_name || profile?.program_id || 'Bachelor of Technology in Computer Science'} - {profile?.institution_name || profile?.institution_id || 'Vidya Vikas Institute'}
              </p>
              <div className="flex flex-wrap gap-3 sm:gap-6 pt-1 text-xs text-muted">
                <span>Student ID: <strong className="text-heading font-mono">{profile?.student_id || 'STU-0421'}</strong></span>
                <span>APAAR ID: <strong className="text-heading font-mono">{profile?.apaar_id_masked || '•••• •••• 9842'}</strong></span>
                <span>Roll No: <strong className="text-heading font-mono">{profile?.student_institute_roll_no || '2023-CS-042'}</strong></span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <Link to="/me/id-card" className="no-underline">
              <Button variant="accent" size="sm">
                Digital ID Card
              </Button>
            </Link>
            <Link to="/me/share" className="no-underline">
              <Button variant="secondary" size="sm">
                Share Proof
              </Button>
            </Link>
          </div>
        </div>
      </Card>

      {/* Unlinked Claim Notice */}
      {error && (
        <Card className="border-amber-500/30 bg-amber-500/5 p-5">
          <div className="space-y-3">
            <h3 className="m-0 text-sm font-bold text-heading">
              Link Your Official Academic Record
            </h3>
            <p className="m-0 text-xs text-muted">
              Enter the claim code issued by your institution to link your account to verified institutional records.
            </p>
            <form onSubmit={handleClaim} className="flex flex-col sm:flex-row items-center gap-2">
              <div className="w-full sm:w-72">
                <Input
                  placeholder="CL-XXXX-XXXX"
                  value={claimCode}
                  onChange={(e) => setClaimCode(e.target.value)}
                  disabled={claimLoading}
                />
              </div>
              <Button type="submit" size="sm" disabled={claimLoading || !claimCode.trim()}>
                {claimLoading ? 'Verifying...' : 'Link Record'}
              </Button>
            </form>
            {claimError && <p className="m-0 text-xs font-semibold text-danger">{claimError}</p>}
            {claimSuccess && <p className="m-0 text-xs font-semibold text-emerald">{claimSuccess}</p>}
          </div>
        </Card>
      )}

      {/* Key Metric Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          label="Attendance Rate"
          value={`${attendance.percentage}%`}
          hint={`${attendance.attended} / ${attendance.total} sessions attended`}
          tone={attendance.percentage >= 75 ? 'good' : 'critical'}
          trend={attendance.percentage >= 75 ? 'Target Met (>=75%)' : 'Below 75% Warning'}
          icon={
            <svg className="w-4 h-4 text-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <SummaryCard
          label="Active Coursework"
          value={String(displayAssignments.filter((a) => a.status === 'PENDING').length)}
          hint="Pending assignment submissions"
          tone="accent"
          icon={
            <svg className="w-4 h-4 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2" />
            </svg>
          }
        />
        <SummaryCard
          label="Upcoming Exams"
          value={String(upcomingExams.length)}
          hint="Next: DS Practical (Nov 14)"
          tone="default"
          icon={
            <svg className="w-4 h-4 text-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          }
        />
        <SummaryCard
          label="Cumulative SGPA"
          value="8.72"
          hint="Semester IV - All Credits Cleared"
          tone="good"
          trend="Top 10% Decile"
          icon={
            <svg className="w-4 h-4 text-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2z" />
            </svg>
          }
        />
      </div>

      {/* Main Grid: Schedule & Assignments */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Today's Timetable Schedule */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="p-5">
            <div className="flex items-center justify-between pb-3 border-b border-line">
              <div>
                <h3 className="m-0 text-base font-bold text-heading">Today's Class Schedule</h3>
                <p className="m-0 text-xs text-muted mt-0.5">Periods and lecture halls for today</p>
              </div>
              <Link to="/me/timetable" className="text-xs font-semibold text-brand hover:underline no-underline">
                Full Timetable
              </Link>
            </div>

            <div className="mt-4 divide-y divide-line">
              {todaySchedule.map((item, idx) => (
                <div key={idx} className="py-3 flex items-center justify-between gap-3 text-xs">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center justify-center h-7 w-7 rounded bg-brand-light text-brand font-bold text-[11px] shrink-0">
                      P{item.period}
                    </span>
                    <div>
                      <p className="m-0 font-bold text-heading text-sm">{item.subject}</p>
                      <p className="m-0 text-muted text-xs mt-0.5">{item.teacher}</p>
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="font-semibold text-heading block">{item.time}</span>
                    <span className="rounded bg-line px-1.5 py-0.5 text-[10px] text-muted font-mono mt-0.5 inline-block">
                      {item.room}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Active Coursework & Assignments */}
          <Card className="p-5">
            <div className="flex items-center justify-between pb-3 border-b border-line">
              <div>
                <h3 className="m-0 text-base font-bold text-heading">Active Assignments</h3>
                <p className="m-0 text-xs text-muted mt-0.5">Upcoming problem sets and project submissions</p>
              </div>
              <Link to="/me/assignments" className="text-xs font-semibold text-brand hover:underline no-underline">
                View All
              </Link>
            </div>

            <div className="mt-4 space-y-3">
              {displayAssignments.map((asn) => (
                <div
                  key={asn.id}
                  className="flex items-center justify-between p-3 rounded-lg border border-line bg-surface-2 hover:bg-surface transition-colors"
                >
                  <div className="min-w-0 flex-1">
                    <p className="m-0 text-xs font-bold text-heading truncate">{asn.title}</p>
                    <p className="m-0 text-[11px] text-muted mt-0.5">
                      {asn.subject} - Due {asn.due_date}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-xs font-semibold text-muted">{asn.max_marks} Marks</span>
                    <span
                      className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                        asn.status === 'SUBMITTED'
                          ? 'bg-emerald/10 text-emerald'
                          : 'bg-amber-500/10 text-amber-600'
                      }`}
                    >
                      {asn.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Quick Actions Grid */}
          <QuickActionWidget
            title="Academic Identity & Verification Actions"
            actions={quickActions}
          />
        </div>

        {/* Right Column: Attendance Progress, Exams & Announcements */}
        <div className="space-y-6">
          {/* Attendance Requirement Target */}
          <ProgressIndicatorWidget
            title="Attendance Status"
            items={[
              {
                label: 'Overall Aggregate',
                value: attendance.attended,
                max: attendance.total,
                target: `${attendance.total} sessions`,
                hint: attendance.percentage >= 75 ? 'Above 75% statutory requirement' : 'Below 75% statutory requirement',
                tone: attendance.percentage >= 75 ? 'good' : 'critical',
              },
              {
                label: 'Data Structures Lab',
                value: 14,
                max: 15,
                hint: '93% - Fully Compliant',
                tone: 'good',
              },
              {
                label: 'Mathematics III',
                value: 16,
                max: 18,
                hint: '88% - Fully Compliant',
                tone: 'good',
              },
            ]}
          />

          {/* Upcoming Examinations */}
          <UpcomingEventsWidget
            title="Upcoming Examinations"
            subtitle="Published by Examination Controller"
            events={upcomingExams}
            actionLabel="View Results"
            actionTo="/me/results"
          />

          {/* Institutional Announcements */}
          <NotificationPreviewWidget
            title="Campus Circulars"
            subtitle="Verified announcements"
            notifications={announcements}
            actionLabel="All Notices"
            actionTo="/announcements"
          />

          {/* Learning Resources */}
          <Card className="p-5">
            <h3 className="m-0 text-base font-bold text-heading pb-3 border-b border-line">
              Learning Resources
            </h3>
            <div className="mt-3 space-y-2 text-xs">
              <Link
                to="/library"
                className="flex items-center justify-between p-2 rounded hover:bg-surface-2 text-heading no-underline transition-colors font-medium"
              >
                <span>Campus Library (OPAC)</span>
                <span className="text-[10px] text-brand">Browse & Reserve</span>
              </Link>
              <Link
                to="/me/academics"
                className="flex items-center justify-between p-2 rounded hover:bg-surface-2 text-heading no-underline transition-colors font-medium"
              >
                <span>Syllabus & Course Matrix</span>
                <span className="text-[10px] text-brand">View Credits</span>
              </Link>
              <Link
                to="/opportunities"
                className="flex items-center justify-between p-2 rounded hover:bg-surface-2 text-heading no-underline transition-colors font-medium"
              >
                <span>National Internship Portal</span>
                <span className="text-[10px] text-brand">Explore</span>
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
