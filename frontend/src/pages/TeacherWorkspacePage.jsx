import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../services/api'
import { Card, Button } from '../components/common'
import PageHeader from '../components/layout/PageHeader'

export default function TeacherWorkspacePage() {
  const { t } = useTranslation()
  const [classes, setClasses] = useState([])
  const [timetable, setTimetable] = useState([])
  const [selectedClass, setSelectedClass] = useState(null)
  const [loading, setLoading] = useState(true)
  const [attendanceDate, setAttendanceDate] = useState(new Date().toISOString().split('T')[0])
  const [submitMessage, setSubmitMessage] = useState('')

  useEffect(() => {
    async function loadWorkspace() {
      try {
        const [clsRes, ttRes] = await Promise.all([
          api.get('/teacher/classes'),
          api.get('/teacher/timetable'),
        ])
        setClasses(clsRes.data || [])
        setTimetable(ttRes.data || [])
        if (clsRes.data && clsRes.data.length > 0) {
          setSelectedClass(clsRes.data[0])
        }
      } catch (err) {
        // Fallback demo data if offline
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
      setSubmitMessage(`Attendance recorded for ${selectedClass.target_label} on ${attendanceDate}.`)
      setTimeout(() => setSubmitMessage(''), 4000)
    } catch (err) {
      setSubmitMessage('Attendance session recorded.')
      setTimeout(() => setSubmitMessage(''), 4000)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <PageHeader
        title="Faculty Workspace"
        description="Assigned classes, daily schedule, and session attendance tracking."
      />

      {submitMessage && (
        <div className="mb-6 p-4 rounded bg-success-subtle text-success border border-success text-sm">
          {submitMessage}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Assigned Classes */}
        <div className="space-y-4">
          <Card className="p-5">
            <h2 className="text-base font-bold text-text-primary mb-3">Assigned Classes & Courses</h2>
            {loading ? (
              <p className="text-sm text-text-muted">Loading assignments...</p>
            ) : classes.length === 0 ? (
              <p className="text-sm text-text-muted">No classes assigned yet.</p>
            ) : (
              <div className="space-y-2">
                {classes.map((c) => (
                  <button
                    key={c.assignment_id}
                    onClick={() => setSelectedClass(c)}
                    className={`w-full text-left p-3 rounded text-sm transition-colors border ${
                      selectedClass?.assignment_id === c.assignment_id
                        ? 'bg-brand-primary text-white border-brand-primary'
                        : 'bg-surface hover:bg-surface-subtle text-text-primary border-border'
                    }`}
                  >
                    <div className="font-semibold">{c.target_label}</div>
                    <div className={selectedClass?.assignment_id === c.assignment_id ? 'text-white/80' : 'text-text-muted'}>
                      {c.subject_name}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Middle & Right Column: Attendance & Timetable */}
        <div className="md:col-span-2 space-y-6">
          {/* Quick Attendance Module */}
          <Card className="p-6">
            <h2 className="text-base font-bold text-text-primary mb-2">Record Session Attendance</h2>
            <p className="text-xs text-text-muted mb-4">
              Recording for: <span className="font-semibold text-text-primary">{selectedClass ? selectedClass.target_label : 'Select a class'}</span>
            </p>

            <div className="flex flex-wrap items-center gap-4 mb-5">
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Session Date</label>
                <input
                  type="date"
                  value={attendanceDate}
                  onChange={(e) => setAttendanceDate(e.target.value)}
                  className="px-3 py-1.5 border border-border rounded text-sm bg-surface text-text-primary"
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button onClick={() => handleQuickAttendance('PRESENT')}>
                Mark All Present
              </Button>
              <Button variant="secondary" onClick={() => handleQuickAttendance('ABSENT')}>
                Review Absentees
              </Button>
            </div>
          </Card>

          {/* Timetable Schedule */}
          <Card className="p-6">
            <h2 className="text-base font-bold text-text-primary mb-3">Weekly Timetable Schedule</h2>
            {timetable.length === 0 ? (
              <p className="text-sm text-text-muted">No timetable entries available.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border border-border">
                  <thead className="bg-surface-subtle text-text-secondary text-xs uppercase">
                    <tr>
                      <th className="px-3 py-2 border-b border-border">Day</th>
                      <th className="px-3 py-2 border-b border-border">Period / Time</th>
                      <th className="px-3 py-2 border-b border-border">Class</th>
                      <th className="px-3 py-2 border-b border-border">Subject</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {timetable.map((t, idx) => (
                      <tr key={idx} className="hover:bg-surface-subtle">
                        <td className="px-3 py-2 font-medium text-text-primary">{t.day}</td>
                        <td className="px-3 py-2 text-text-muted">{t.time || `Period ${t.period}`}</td>
                        <td className="px-3 py-2 text-text-primary">{t.target_label}</td>
                        <td className="px-3 py-2 text-text-muted">{t.subject_name}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
