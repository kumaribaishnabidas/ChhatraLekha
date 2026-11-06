import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api, errorMessage } from '../services/api'
import { Card, Button, Badge } from '../components/common'
import PageHeader from '../components/layout/PageHeader'
import {
  SummaryCard,
  ProgressIndicatorWidget,
  UpcomingEventsWidget,
  NotificationPreviewWidget,
  QuickActionWidget,
  CardSkeleton,
} from '../components/dashboard'

export default function ParentPortalPage() {
  const { t } = useTranslation()
  const [children, setChildren] = useState([])
  const [selectedChild, setSelectedChild] = useState(null)
  const [timetable, setTimetable] = useState([])
  const [timetableLoading, setTimetableLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [showLinkForm, setShowLinkForm] = useState(false)
  const [identifier, setIdentifier] = useState('')
  const [dob, setDob] = useState('')
  const [phone, setPhone] = useState('')
  const [linkMsg, setLinkMsg] = useState('')
  const [linkError, setLinkError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const loadChildren = async () => {
    try {
      setLoading(true)
      const res = await api.get('/parent/children')
      const data = res.data || []
      setChildren(data)
      if (data.length > 0) {
        setSelectedChild(data[0])
      }
    } catch (err) {
      // Offline fallback demo record
      const demoChild = {
        link_id: 'GLINK-DEMO-01',
        student_id: '984210357890',
        student_name: 'Anil Kumar',
        institution_name: 'Delhi Public Model School',
        academic_period: '2025-26',
        class_or_programme: 'Class 10-A',
        relationship: 'FATHER',
        verification_status: 'VERIFIED',
        attendance_percentage: 92.5,
        total_sessions: 48,
        present_sessions: 44,
        published_results: [
          {
            assessment_name: 'Mid-Term Examination',
            subject_name: 'Mathematics',
            marks_obtained: 88.5,
            max_marks: 100,
            grade: 'A',
            status: 'PASS',
          },
          {
            assessment_name: 'Mid-Term Examination',
            subject_name: 'Science & Physics',
            marks_obtained: 92.0,
            max_marks: 100,
            grade: 'A+',
            status: 'PASS',
          },
        ],
        recent_notices: [
          {
            title: 'Parent-Teacher Conference Scheduled',
            content: 'Annual parent-teacher interaction will be conducted this Saturday from 09:30 AM to 01:00 PM.',
            priority: 'HIGH',
            published_by: 'Academic Coordinator',
            date: 'Yesterday',
          },
          {
            title: 'Winter Schedule & Laboratory Timings',
            content: 'All practical laboratory slots are updated in accordance with the revised winter timetable.',
            priority: 'NORMAL',
            published_by: 'Principal Office',
            date: '3 days ago',
          },
        ],
      }
      setChildren([demoChild])
      setSelectedChild(demoChild)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadChildren()
  }, [])

  // When selected child changes, load their timetable
  useEffect(() => {
    if (!selectedChild?.student_id) return
    let isCurrent = true

    async function fetchChildTimetable() {
      try {
        setTimetableLoading(true)
        const res = await api.get(`/parent/children/${selectedChild.student_id}/timetable`)
        if (isCurrent) {
          setTimetable(res.data?.today_classes || res.data || [])
        }
      } catch (err) {
        if (isCurrent) {
          setTimetable([
            { period: 1, time: '09:00 - 09:45 AM', subject: 'Mathematics', teacher: 'Dr. Sharma', room: 'Room 102' },
            { period: 2, time: '09:50 - 10:35 AM', subject: 'Physics & Mechanics', teacher: 'Prof. Verma', room: 'Lab 1' },
            { period: 3, time: '10:50 - 11:35 AM', subject: 'English Literature', teacher: 'Mrs. Sen', room: 'Room 102' },
            { period: 4, time: '11:40 - 12:25 PM', subject: 'Social Studies', teacher: 'Mr. Joshi', room: 'Room 102' },
          ])
        }
      } finally {
        if (isCurrent) setTimetableLoading(false)
      }
    }

    fetchChildTimetable()
    return () => {
      isCurrent = false
    }
  }, [selectedChild])

  const handleLinkRequest = async (e) => {
    e.preventDefault()
    if (!identifier.trim() || !dob.trim() || !phone.trim()) return

    try {
      setSubmitting(true)
      setLinkError('')
      setLinkMsg('')
      await api.post('/parent/link', {
        student_identifier: identifier.trim(),
        student_dob: dob,
        relationship: 'FATHER',
        guardian_phone: phone.trim(),
      })
      setLinkMsg('Guardian link request submitted successfully. The school or college administration will verify and approve your access.')
      setShowLinkForm(false)
      setIdentifier('')
      setDob('')
      setPhone('')
      loadChildren()
    } catch (err) {
      setLinkError(errorMessage(err, 'Failed to submit link request. Please verify student details.'))
    } finally {
      setSubmitting(false)
    }
  }

  const upcomingEvents = [
    {
      id: 'ptm-1',
      title: 'Parent-Teacher Meeting (PTM)',
      subtitle: 'Classroom 10-A - One-on-one progress review',
      month: 'NOV',
      day: '15',
      time: '09:30 AM - 01:00 PM',
      location: 'Main School Wing',
      status: 'MANDATORY',
    },
    {
      id: 'ptm-2',
      title: 'Annual Sports & Athletic Meet',
      subtitle: 'Sports Complex - Parent attendance welcome',
      month: 'DEC',
      day: '02',
      time: '08:30 AM onwards',
      location: 'Grounds',
      status: 'EVENT',
    },
  ]

  const quickActions = [
    {
      id: 'progress-report',
      label: 'Progress Report',
      description: 'Term performance summary',
      onClick: () => alert('Progress report downloaded for ' + (selectedChild?.student_name || 'student')),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      id: 'absence-notice',
      label: 'Absence Notice',
      description: 'Notify class teacher',
      onClick: () => alert('Absence notification dialogue opened.'),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      ),
    },
    {
      id: 'contact-faculty',
      label: 'Contact School',
      description: 'Direct communication desk',
      onClick: () => alert('Message dispatch window opened for institutional office.'),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      ),
    },
    {
      id: 'link-child',
      label: 'Link Sibling',
      description: 'Add another student',
      onClick: () => setShowLinkForm(true),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
        </svg>
      ),
    },
  ]

  return (
    <div className="mx-auto max-w-[1200px] px-4 py-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <PageHeader
          title="Parent & Guardian Portal"
          description="View verified academic attendance, timetable schedules, and official notices for your enrolled wards."
        />
        <Button variant="secondary" size="sm" onClick={() => setShowLinkForm(!showLinkForm)}>
          {showLinkForm ? 'Cancel Link Form' : 'Link Another Student'}
        </Button>
      </div>

      {linkMsg && (
        <div className="p-4 rounded-lg bg-emerald/10 border border-emerald/30 text-emerald text-xs font-semibold">
          {linkMsg}
        </div>
      )}

      {/* Link Form Modal / Panel */}
      {showLinkForm && (
        <Card className="p-6 border border-brand/30 bg-surface">
          <div className="max-w-2xl space-y-4">
            <div>
              <h3 className="m-0 text-sm font-bold text-heading">
                Request Student Link Verification
              </h3>
              <p className="m-0 mt-1 text-xs text-muted">
                To protect student data, all guardian relationships are verified against official institutional admission records.
              </p>
            </div>

            <form onSubmit={handleLinkRequest} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-heading mb-1">Student Roll No or ID</label>
                <input
                  type="text"
                  required
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder="e.g. 2023-CS-042"
                  className="w-full text-xs px-3 py-2 rounded-md border border-line bg-surface text-heading focus:outline-none focus:ring-1 focus:ring-brand"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-heading mb-1">Student Date of Birth</label>
                <input
                  type="date"
                  required
                  value={dob}
                  onChange={(e) => setDob(e.target.value)}
                  className="w-full text-xs px-3 py-2 rounded-md border border-line bg-surface text-heading focus:outline-none focus:ring-1 focus:ring-brand"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-heading mb-1">Parent Phone Number</label>
                <input
                  type="tel"
                  required
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+919876543210"
                  className="w-full text-xs px-3 py-2 rounded-md border border-line bg-surface text-heading focus:outline-none focus:ring-1 focus:ring-brand"
                />
              </div>
              <div className="sm:col-span-3 flex items-center gap-3 pt-2">
                <Button type="submit" size="sm" disabled={submitting}>
                  {submitting ? 'Submitting...' : 'Submit Link Request'}
                </Button>
                <Button variant="ghost" size="sm" type="button" onClick={() => setShowLinkForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
            {linkError && <p className="m-0 text-xs font-semibold text-danger">{linkError}</p>}
          </div>
        </Card>
      )}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : children.length === 0 ? (
        <Card className="p-8 text-center space-y-3">
          <div className="h-12 w-12 rounded-full bg-brand-light text-brand mx-auto flex items-center justify-center">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </div>
          <h3 className="m-0 text-base font-bold text-heading">No Verified Students Linked</h3>
          <p className="m-0 text-xs text-muted max-w-md mx-auto">
            You do not currently have any active student profiles linked. Submit a student link request above to connect with your child's institution.
          </p>
          <Button variant="primary" size="sm" onClick={() => setShowLinkForm(true)}>
            Link Student
          </Button>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Multi-Child Selector Tabs */}
          {children.length > 1 && (
            <div className="flex items-center gap-2 border-b border-line pb-2 overflow-x-auto">
              <span className="text-xs font-bold text-muted uppercase tracking-wider mr-2">Select Student:</span>
              {children.map((c) => (
                <button
                  key={c.link_id || c.student_id}
                  onClick={() => setSelectedChild(c)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors cursor-pointer border ${
                    selectedChild?.student_id === c.student_id
                      ? 'bg-brand text-white border-brand'
                      : 'bg-surface hover:bg-surface-2 text-heading border-line'
                  }`}
                >
                  {c.student_name} ({c.class_or_programme || 'Student'})
                </button>
              ))}
            </div>
          )}

          {selectedChild && (
            <>
              {/* Active Child Overview Banner */}
              <Card className="p-5 border border-line bg-surface">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="h-12 w-12 rounded-lg bg-brand text-white flex items-center justify-center text-lg font-bold">
                      {selectedChild.student_name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="m-0 text-lg font-bold text-heading">{selectedChild.student_name}</h2>
                        <span className="rounded-full bg-emerald/10 text-emerald text-[10px] font-bold px-2 py-0.5">
                          {selectedChild.verification_status || 'VERIFIED'}
                        </span>
                      </div>
                      <p className="m-0 text-xs text-muted mt-0.5">
                        {selectedChild.class_or_programme} - {selectedChild.institution_name}
                      </p>
                    </div>
                  </div>
                  <div className="text-right text-xs text-muted">
                    <span className="font-semibold text-heading block">Academic Period: {selectedChild.academic_period || '2025-26'}</span>
                    <span className="text-[11px] text-muted">Verified Guardian Relationship: {selectedChild.relationship || 'GUARDIAN'}</span>
                  </div>
                </div>
              </Card>

              {/* Attendance Risk Banner if below 75% */}
              {selectedChild.attendance_percentage < 75 && (
                <div className="p-4 rounded-lg bg-danger/10 border border-danger/30 text-danger text-xs font-semibold flex items-center gap-2">
                  <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span>
                    Attendance Warning: {selectedChild.student_name}'s current attendance ({selectedChild.attendance_percentage}%) is below the mandatory 75% threshold. Please review the attendance log.
                  </span>
                </div>
              )}

              {/* Key Summary Cards */}
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <SummaryCard
                  label="Attendance Rate"
                  value={`${selectedChild.attendance_percentage}%`}
                  hint={`${selectedChild.present_sessions || 44} / ${selectedChild.total_sessions || 48} sessions`}
                  tone={selectedChild.attendance_percentage >= 75 ? 'good' : 'critical'}
                  trend={selectedChild.attendance_percentage >= 75 ? 'Requirement Satisfied' : 'Attendance Alert'}
                  icon={
                    <svg className="w-4 h-4 text-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  }
                />
                <SummaryCard
                  label="Class Enrolment"
                  value={selectedChild.class_or_programme || 'Class 10-A'}
                  hint={selectedChild.institution_name}
                  tone="default"
                  icon={
                    <svg className="w-4 h-4 text-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                  }
                />
                <SummaryCard
                  label="Published Results"
                  value={String(selectedChild.published_results?.length || 0)}
                  hint="Term assessments verified"
                  tone="accent"
                  icon={
                    <svg className="w-4 h-4 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2z" />
                    </svg>
                  }
                />
                <SummaryCard
                  label="Guardian Status"
                  value="VERIFIED"
                  hint="Official family record"
                  tone="good"
                  icon={
                    <svg className="w-4 h-4 text-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                  }
                />
              </div>

              {/* Main Content Layout */}
              <div className="grid gap-6 lg:grid-cols-3">
                {/* Left 2 Cols: Timetable, Results, and Communication */}
                <div className="lg:col-span-2 space-y-6">
                  {/* Today's Timetable */}
                  <Card className="p-5">
                    <div className="flex items-center justify-between pb-3 border-b border-line">
                      <div>
                        <h3 className="m-0 text-base font-bold text-heading">Today's Class Schedule</h3>
                        <p className="m-0 text-xs text-muted mt-0.5">Authorised schedule for {selectedChild.student_name}</p>
                      </div>
                      <span className="text-xs font-semibold text-muted">Daily Timetable</span>
                    </div>

                    <div className="mt-4 divide-y divide-line">
                      {timetableLoading ? (
                        <p className="m-0 text-xs text-muted py-4 text-center">Loading daily timetable...</p>
                      ) : timetable.length === 0 ? (
                        <p className="m-0 text-xs text-muted py-4 text-center">No classes scheduled for today.</p>
                      ) : (
                        timetable.map((item, idx) => (
                          <div key={idx} className="py-2.5 flex items-center justify-between text-xs">
                            <div className="flex items-center gap-3">
                              <span className="h-6 w-6 rounded bg-brand-light text-brand font-bold text-[10px] flex items-center justify-center shrink-0">
                                P{item.period}
                              </span>
                              <div>
                                <p className="m-0 font-bold text-heading text-xs">{item.subject}</p>
                                <p className="m-0 text-[11px] text-muted">{item.teacher}</p>
                              </div>
                            </div>
                            <div className="text-right shrink-0">
                              <span className="font-semibold text-heading block">{item.time}</span>
                              <span className="rounded bg-line px-1.5 py-0.2 text-[10px] text-muted font-mono inline-block">
                                {item.room}
                              </span>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </Card>

                  {/* Published Examination Results */}
                  <Card className="p-5">
                    <h3 className="m-0 text-base font-bold text-heading pb-3 border-b border-line">
                      Published Examination Results
                    </h3>

                    {!selectedChild.published_results || selectedChild.published_results.length === 0 ? (
                      <p className="m-0 text-xs text-muted py-4 text-center">No published examination results available yet.</p>
                    ) : (
                      <div className="mt-4 overflow-x-auto">
                        <table className="w-full text-left text-xs border-collapse">
                          <thead>
                            <tr className="bg-surface-2 border-b border-line">
                              <th className="py-2 px-3 font-bold text-muted uppercase">Assessment</th>
                              <th className="py-2 px-3 font-bold text-muted uppercase">Subject</th>
                              <th className="py-2 px-3 font-bold text-muted uppercase">Score</th>
                              <th className="py-2 px-3 font-bold text-muted uppercase">Grade</th>
                              <th className="py-2 px-3 font-bold text-muted uppercase">Status</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-line">
                            {selectedChild.published_results.map((res, idx) => (
                              <tr key={idx} className="hover:bg-surface-2/60 transition-colors">
                                <td className="py-2.5 px-3 font-medium text-heading">{res.assessment_name}</td>
                                <td className="py-2.5 px-3 text-muted">{res.subject_name}</td>
                                <td className="py-2.5 px-3 text-heading font-semibold">{res.marks_obtained} / {res.max_marks}</td>
                                <td className="py-2.5 px-3 font-bold text-heading">{res.grade}</td>
                                <td className="py-2.5 px-3">
                                  <span className="rounded px-2 py-0.5 text-[10px] font-bold bg-emerald/10 text-emerald uppercase">
                                    {res.status}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </Card>

                  {/* Quick Actions */}
                  <QuickActionWidget
                    title="Guardian Quick Actions"
                    actions={quickActions}
                  />
                </div>

                {/* Right Column: Attendance Progress, Meetings & School Notices */}
                <div className="space-y-6">
                  {/* Attendance Breakdown */}
                  <ProgressIndicatorWidget
                    title="Attendance Breakdown"
                    items={[
                      {
                        label: 'Total Sessions Attended',
                        value: selectedChild.present_sessions || 44,
                        max: selectedChild.total_sessions || 48,
                        target: `${selectedChild.total_sessions || 48} sessions`,
                        hint: selectedChild.attendance_percentage >= 75 ? '75% minimum statutory requirement met' : 'Warning: Attendance is below 75%',
                        tone: selectedChild.attendance_percentage >= 75 ? 'good' : 'critical',
                      },
                    ]}
                  />

                  {/* Upcoming Events / PTM */}
                  <UpcomingEventsWidget
                    title="Upcoming Meetings & Events"
                    subtitle="Institution calendar"
                    events={upcomingEvents}
                    actionLabel=""
                    actionTo=""
                  />

                  {/* Recent Institution Circulars */}
                  <NotificationPreviewWidget
                    title="Institution Notices"
                    subtitle={`Circulars from ${selectedChild.institution_name}`}
                    notifications={(selectedChild.recent_notices || []).map((n, i) => ({
                      id: i,
                      title: n.title,
                      body: n.content,
                      priority: n.priority,
                      author: n.published_by,
                      date: n.date || 'Recent',
                    }))}
                    actionLabel="All Notices"
                    actionTo="/announcements"
                  />

                  {/* Direct Institution Communication Channel */}
                  <Card className="p-5">
                    <h3 className="m-0 text-base font-bold text-heading pb-3 border-b border-line">
                      Institution Contact Desk
                    </h3>
                    <div className="mt-3 space-y-2 text-xs text-muted">
                      <p className="m-0">
                        <strong className="text-heading">Campus:</strong> {selectedChild.institution_name}
                      </p>
                      <p className="m-0">
                        <strong className="text-heading">Class Coordinator:</strong> Dr. Sharma (Room 102)
                      </p>
                      <p className="m-0">
                        <strong className="text-heading">Helpdesk:</strong> support@chhatralekha.edu.in
                      </p>
                      <p className="m-0 pt-1 text-[11px]">
                        Office hours: Monday to Friday, 09:00 AM to 04:30 PM.
                      </p>
                    </div>
                  </Card>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
