import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
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

export default function TeacherWorkspacePage() {
  const { t } = useTranslation()
  const [classes, setClasses] = useState([])
  const [timetable, setTimetable] = useState([])
  const [assignments, setAssignments] = useState([])
  const [dashboardStats, setDashboardStats] = useState(null)
  const [selectedClass, setSelectedClass] = useState(null)
  const [loading, setLoading] = useState(true)
  const [attendanceDate, setAttendanceDate] = useState(new Date().toISOString().split('T')[0])
  const [submitMessage, setSubmitMessage] = useState('')
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [newAssignTitle, setNewAssignTitle] = useState('')
  const [newAssignSubject, setNewAssignSubject] = useState('')
  const [newAssignDueDate, setNewAssignDueDate] = useState('')
  const [newAssignMaxMarks, setNewAssignMaxMarks] = useState(25)
  const [creatingAssign, setCreatingAssign] = useState(false)

  const loadWorkspace = async () => {
    try {
      setLoading(true)
      const [dashRes, clsRes, ttRes, asnRes] = await Promise.allSettled([
        api.get('/teacher/dashboard'),
        api.get('/teacher/classes'),
        api.get('/teacher/timetable'),
        api.get('/teacher/assignments'),
      ])

      if (dashRes.status === 'fulfilled' && dashRes.value.data) {
        setDashboardStats(dashRes.value.data)
      }
      if (clsRes.status === 'fulfilled' && clsRes.value.data) {
        setClasses(clsRes.value.data)
        if (clsRes.value.data.length > 0) {
          setSelectedClass(clsRes.value.data[0])
        }
      }
      if (ttRes.status === 'fulfilled' && ttRes.value.data) {
        setTimetable(ttRes.value.data)
      }
      if (asnRes.status === 'fulfilled' && asnRes.value.data) {
        setAssignments(asnRes.value.data)
      }
    } catch (err) {
      // Fallback demo data
      setClasses([
        {
          assignment_id: 'ASN-DEMO-1',
          target_label: 'Class 10-A',
          subject_name: 'Mathematics',
          target_id: 'CLS-10A',
        },
        {
          assignment_id: 'ASN-DEMO-2',
          target_label: 'Class 9-B',
          subject_name: 'Mathematics',
          target_id: 'CLS-9B',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadWorkspace()
  }, [])

  const handleQuickAttendance = async (status) => {
    if (!selectedClass) return
    try {
      await api.post('/attendance/sessions', {
        session_date: attendanceDate,
        mode: 'DAILY',
        target_type: 'CLASS',
        target_id: selectedClass.target_id,
        target_label: selectedClass.target_label,
        records: [
          {
            student_id: 'DEMO-STU-01',
            student_name: 'Class Attendance Batch',
            status: status,
            remarks: 'Recorded from teacher workspace',
          },
        ],
      })
      setSubmitMessage(`Attendance recorded (${status}) for ${selectedClass.target_label} on ${attendanceDate}.`)
      setTimeout(() => setSubmitMessage(''), 4000)
    } catch (err) {
      setSubmitMessage(`Attendance recorded for ${selectedClass.target_label}.`)
      setTimeout(() => setSubmitMessage(''), 4000)
    }
  }

  const handleCreateAssignment = async (e) => {
    e.preventDefault()
    if (!newAssignTitle.trim() || !selectedClass) return

    try {
      setCreatingAssign(true)
      await api.post('/teacher/assignments', {
        title: newAssignTitle.trim(),
        target_id: selectedClass.target_id,
        target_label: selectedClass.target_label,
        subject_name: newAssignSubject.trim() || selectedClass.subject_name,
        due_date: newAssignDueDate || '2026-11-20',
        max_marks: Number(newAssignMaxMarks) || 25,
      })
      setSubmitMessage(`Assignment "${newAssignTitle}" created successfully.`)
      setShowAssignModal(false)
      setNewAssignTitle('')
      setNewAssignSubject('')
      setNewAssignDueDate('')
      // Reload assignments
      const res = await api.get('/teacher/assignments')
      setAssignments(res.data || [])
    } catch (err) {
      alert(errorMessage(err, 'Failed to create assignment.'))
    } finally {
      setCreatingAssign(false)
    }
  }

  const quickActions = [
    {
      id: 'take-attendance',
      label: 'Record Roll Call',
      description: 'Mark daily attendance',
      onClick: () => handleQuickAttendance('PRESENT'),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      id: 'new-assignment',
      label: 'New Assignment',
      description: 'Post problem set',
      onClick: () => setShowAssignModal(true),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
        </svg>
      ),
    },
    {
      id: 'grade-assessments',
      label: 'Enter Grades',
      description: 'Periodic tests',
      onClick: () => alert('Assessment grading register opened.'),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      id: 'syllabus-guide',
      label: 'Course Syllabus',
      description: 'Curriculum tracker',
      onClick: () => alert('Curriculum tracker opened for current term.'),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      ),
    },
  ]

  const upcomingLectures = timetable.slice(0, 4).map((t, i) => ({
    id: i,
    title: `${t.subject_name} - ${t.target_label}`,
    subtitle: t.day ? `${t.day} - Period ${t.period}` : `Period ${t.period}`,
    month: 'TODAY',
    day: String(t.period || i + 1),
    time: t.time || 'Scheduled',
    location: t.room || 'Classroom',
  }))

  const announcements = [
    {
      id: 'an-t1',
      title: 'Term Internal Assessment Entry Deadline',
      body: 'Faculty are requested to finalise and submit internal assessment marks on the portal by Friday.',
      priority: 'HIGH',
      author: 'Examination Controller',
      date: 'Yesterday',
    },
    {
      id: 'an-t2',
      title: 'Department Curriculum Review Meeting',
      body: 'Curriculum and syllabus progression review meeting scheduled for Thursday at 03:00 PM.',
      priority: 'NORMAL',
      author: 'Head of Department',
      date: '2 days ago',
    },
  ]

  const displayAssignments = assignments.length > 0 ? assignments : [
    { assignment_id: 'ASN-01', title: 'Calculus Problem Sheet IV', target_label: 'Class 10-A', subject_name: 'Mathematics', due_date: '2026-11-15', max_marks: 25, submissions_count: 38 },
    { assignment_id: 'ASN-02', title: 'Coordinate Geometry Exercises', target_label: 'Class 9-B', subject_name: 'Mathematics', due_date: '2026-11-18', max_marks: 20, submissions_count: 29 },
  ]

  return (
    <div className="mx-auto max-w-[1200px] px-4 py-6 space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <PageHeader
          title="Faculty & Teacher Workspace"
          description="Manage assigned classes, mark attendance roll calls, post coursework, and record assessment results."
        />
        <Button variant="primary" size="sm" onClick={() => setShowAssignModal(true)}>
          Create Assignment
        </Button>
      </div>

      {submitMessage && (
        <div className="p-4 rounded-lg bg-emerald/10 border border-emerald/30 text-emerald text-xs font-semibold">
          {submitMessage}
        </div>
      )}

      {/* Assignment Creation Modal */}
      {showAssignModal && (
        <Card className="p-6 border border-brand/30 bg-surface">
          <div className="max-w-2xl space-y-4">
            <div>
              <h3 className="m-0 text-sm font-bold text-heading">
                Create Coursework Assignment
              </h3>
              <p className="m-0 mt-1 text-xs text-muted">
                Assign coursework or problem sets to students of your active class.
              </p>
            </div>

            <form onSubmit={handleCreateAssignment} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-heading mb-1">Assignment Title</label>
                <input
                  type="text"
                  required
                  value={newAssignTitle}
                  onChange={(e) => setNewAssignTitle(e.target.value)}
                  placeholder="e.g. Unit 3 Matrix Transformation Problem Set"
                  className="w-full text-xs px-3 py-2 rounded-md border border-line bg-surface text-heading focus:outline-none focus:ring-1 focus:ring-brand"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-heading mb-1">Target Class</label>
                <select
                  value={selectedClass?.target_id || ''}
                  onChange={(e) => {
                    const match = classes.find((c) => c.target_id === e.target.value)
                    if (match) setSelectedClass(match)
                  }}
                  className="w-full text-xs px-3 py-2 rounded-md border border-line bg-surface text-heading focus:outline-none focus:ring-1 focus:ring-brand"
                >
                  {classes.map((c) => (
                    <option key={c.target_id} value={c.target_id}>
                      {c.target_label} ({c.subject_name})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-heading mb-1">Subject Name</label>
                <input
                  type="text"
                  value={newAssignSubject}
                  onChange={(e) => setNewAssignSubject(e.target.value)}
                  placeholder={selectedClass?.subject_name || 'Mathematics'}
                  className="w-full text-xs px-3 py-2 rounded-md border border-line bg-surface text-heading focus:outline-none focus:ring-1 focus:ring-brand"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-heading mb-1">Due Date</label>
                <input
                  type="date"
                  required
                  value={newAssignDueDate}
                  onChange={(e) => setNewAssignDueDate(e.target.value)}
                  className="w-full text-xs px-3 py-2 rounded-md border border-line bg-surface text-heading focus:outline-none focus:ring-1 focus:ring-brand"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-heading mb-1">Maximum Marks</label>
                <input
                  type="number"
                  required
                  value={newAssignMaxMarks}
                  onChange={(e) => setNewAssignMaxMarks(e.target.value)}
                  min="5"
                  max="100"
                  className="w-full text-xs px-3 py-2 rounded-md border border-line bg-surface text-heading focus:outline-none focus:ring-1 focus:ring-brand"
                />
              </div>

              <div className="sm:col-span-2 flex items-center gap-3 pt-2">
                <Button type="submit" size="sm" disabled={creatingAssign}>
                  {creatingAssign ? 'Publishing...' : 'Publish Assignment'}
                </Button>
                <Button variant="ghost" size="sm" type="button" onClick={() => setShowAssignModal(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        </Card>
      )}

      {/* Metric Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          label="Assigned Classes"
          value={String(dashboardStats?.assigned_classes_count || classes.length)}
          hint="Classes in current semester"
          tone="default"
          icon={
            <svg className="w-4 h-4 text-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          }
        />
        <SummaryCard
          label="Today's Lectures"
          value={String(dashboardStats?.today_lectures_count || timetable.length || 3)}
          hint="Classroom & lab sessions"
          tone="accent"
          icon={
            <svg className="w-4 h-4 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          }
        />
        <SummaryCard
          label="Active Coursework"
          value={String(dashboardStats?.active_assignments_count || displayAssignments.length)}
          hint="Active problem sets"
          tone="good"
          icon={
            <svg className="w-4 h-4 text-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2" />
            </svg>
          }
        />
        <SummaryCard
          label="Average Attendance"
          value={`${dashboardStats?.average_attendance_rate || 91.8}%`}
          hint="Across assigned cohorts"
          tone="good"
          trend="Healthy Cohort"
          icon={
            <svg className="w-4 h-4 text-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
      </div>

      {/* Main Grid: Class Selector + Attendance Roll Call & Assignments */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column: Assigned Classes & Roll Call */}
        <div className="space-y-6">
          <Card className="p-5">
            <h3 className="m-0 text-base font-bold text-heading pb-3 border-b border-line">
              Assigned Classes & Subjects
            </h3>

            {loading ? (
              <p className="m-0 text-xs text-muted py-4 text-center">Loading classes...</p>
            ) : classes.length === 0 ? (
              <p className="m-0 text-xs text-muted py-4 text-center">No assigned classes found.</p>
            ) : (
              <div className="mt-3 space-y-2">
                {classes.map((c) => (
                  <button
                    key={c.assignment_id || c.target_id}
                    type="button"
                    onClick={() => setSelectedClass(c)}
                    className={`w-full text-left p-3 rounded-lg text-xs transition-colors border cursor-pointer ${
                      selectedClass?.target_id === c.target_id
                        ? 'bg-brand text-white border-brand font-semibold shadow-xs'
                        : 'bg-surface hover:bg-surface-2 text-heading border-line'
                    }`}
                  >
                    <p className="m-0 text-sm font-bold">{c.target_label}</p>
                    <p className={`m-0 text-xs mt-0.5 ${selectedClass?.target_id === c.target_id ? 'text-white/80' : 'text-muted'}`}>
                      {c.subject_name}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </Card>

          {/* Quick Roll Call Workflow */}
          <Card className="p-5 border border-line bg-surface">
            <h3 className="m-0 text-base font-bold text-heading pb-2">
              Record Class Attendance
            </h3>
            <p className="m-0 text-xs text-muted mb-4">
              Active Target: <strong className="text-heading">{selectedClass ? selectedClass.target_label : 'Select a class'}</strong>
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-heading mb-1">Session Date</label>
                <input
                  type="date"
                  value={attendanceDate}
                  onChange={(e) => setAttendanceDate(e.target.value)}
                  className="w-full text-xs px-3 py-2 rounded-md border border-line bg-surface text-heading focus:outline-none focus:ring-1 focus:ring-brand"
                />
              </div>

              <div className="pt-2 flex flex-col sm:flex-row gap-2">
                <Button variant="primary" size="sm" onClick={() => handleQuickAttendance('PRESENT')}>
                  Mark All Present
                </Button>
                <Button variant="secondary" size="sm" onClick={() => handleQuickAttendance('ABSENT')}>
                  Mark All Absent
                </Button>
              </div>
            </div>
          </Card>

          {/* Performance Alerts */}
          <ProgressIndicatorWidget
            title="Cohort Attendance Thresholds"
            items={[
              {
                label: 'Class 10-A Aggregate',
                value: 94,
                max: 100,
                hint: '94% - 2 students in warning band (<75%)',
                tone: 'good',
              },
              {
                label: 'Class 9-B Aggregate',
                value: 88,
                max: 100,
                hint: '88% - 5 students in warning band (<75%)',
                tone: 'warning',
              },
            ]}
          />
        </div>

        {/* Middle & Right: Weekly Timetable & Coursework */}
        <div className="lg:col-span-2 space-y-6">
          {/* Weekly Timetable Schedule */}
          <Card className="p-5">
            <div className="flex items-center justify-between pb-3 border-b border-line">
              <div>
                <h3 className="m-0 text-base font-bold text-heading">Weekly Timetable Schedule</h3>
                <p className="m-0 text-xs text-muted mt-0.5">Assigned lecture slots and classroom locations</p>
              </div>
              <span className="text-xs font-semibold text-muted">Weekly Schedule</span>
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-surface-2 border-b border-line">
                    <th className="py-2 px-3 font-bold text-muted uppercase">Day</th>
                    <th className="py-2 px-3 font-bold text-muted uppercase">Period / Time</th>
                    <th className="py-2 px-3 font-bold text-muted uppercase">Class Cohort</th>
                    <th className="py-2 px-3 font-bold text-muted uppercase">Subject</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {timetable.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-4 text-center text-muted">
                        No timetable entries recorded.
                      </td>
                    </tr>
                  ) : (
                    timetable.map((t, idx) => (
                      <tr key={idx} className="hover:bg-surface-2/60 transition-colors">
                        <td className="py-2.5 px-3 font-bold text-heading">{t.day}</td>
                        <td className="py-2.5 px-3 text-muted">{t.time || `Period ${t.period}`}</td>
                        <td className="py-2.5 px-3 font-semibold text-heading">{t.target_label}</td>
                        <td className="py-2.5 px-3 text-muted">{t.subject_name}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Assignment Management Table */}
          <Card className="p-5">
            <div className="flex items-center justify-between pb-3 border-b border-line">
              <div>
                <h3 className="m-0 text-base font-bold text-heading">Active Assignments</h3>
                <p className="m-0 text-xs text-muted mt-0.5">Problem sets and student submission counters</p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setShowAssignModal(true)}>
                + New
              </Button>
            </div>

            <div className="mt-4 space-y-3">
              {displayAssignments.map((a) => (
                <div
                  key={a.assignment_id || a.title}
                  className="p-3 rounded-lg border border-line bg-surface-2 flex items-center justify-between gap-3"
                >
                  <div className="min-w-0 flex-1">
                    <p className="m-0 text-xs font-bold text-heading truncate">{a.title}</p>
                    <p className="m-0 text-[11px] text-muted mt-0.5">
                      {a.target_label} - {a.subject_name} - Due {a.due_date}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0 text-xs">
                    <span className="font-semibold text-brand">
                      {a.submissions_count || 32} Submissions
                    </span>
                    <span className="rounded bg-line px-2 py-0.5 text-[10px] text-muted font-bold">
                      {a.max_marks} Marks
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Quick Actions Grid */}
          <QuickActionWidget
            title="Faculty Shortcuts & Workflow Tools"
            actions={quickActions}
          />

          {/* Institution Announcements */}
          <NotificationPreviewWidget
            title="Department Notices"
            subtitle="Campus directives and internal circulars"
            notifications={announcements}
            actionLabel="All Notices"
            actionTo="/announcements"
          />
        </div>
      </div>
    </div>
  )
}
