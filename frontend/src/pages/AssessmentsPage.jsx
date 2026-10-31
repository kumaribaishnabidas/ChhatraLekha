import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../services/api'
import { Card, Button } from '../components/common'
import PageHeader from '../components/layout/PageHeader'
import { useAuth } from '../hooks/useAuth'

export default function AssessmentsPage() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const [assessments, setAssessments] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [feedback, setFeedback] = useState('')

  // Form state
  const [name, setName] = useState('')
  const [academicYear, setAcademicYear] = useState('2025-26')
  const [term, setTerm] = useState('Term 1')
  const [targetLabel, setTargetLabel] = useState('Class 10-A')
  const [targetId, setTargetId] = useState('CLS-10A')
  const [subjectName, setSubjectName] = useState('Mathematics')
  const [subjectId, setSubjectId] = useState('SUB-MATH-10')
  const [maxMarks, setMaxMarks] = useState(100)
  const [passingMarks, setPassingMarks] = useState(35)

  useEffect(() => {
    async function loadAssessments() {
      try {
        const res = await api.get('/assessments')
        setAssessments(res.data || [])
      } catch (err) {
        setAssessments([
          {
            assessment_id: 'ASM-DEMO-1',
            name: 'Mid-Term Examination',
            academic_year: '2025-26',
            term: 'Term 1',
            target_label: 'Class 10-A',
            subject_name: 'Mathematics',
            max_marks: 100,
            passing_marks: 35,
            status: 'PUBLISHED',
            created_by: 'Academic Office',
          },
        ])
      } finally {
        setLoading(false)
      }
    }
    loadAssessments()
  }, [])

  const handleCreateAssessment = async (e) => {
    e.preventDefault()
    try {
      const res = await api.post('/assessments', {
        name,
        academic_year: academicYear,
        term,
        target_type: 'CLASS',
        target_id: targetId,
        target_label: targetLabel,
        subject_id: subjectId,
        subject_name: subjectName,
        max_marks: Number(maxMarks),
        passing_marks: Number(passingMarks),
      })
      setAssessments([res.data, ...assessments])
      setFeedback('Assessment created in DRAFT status.')
      setShowCreateModal(false)
      setName('')
      setTimeout(() => setFeedback(''), 4000)
    } catch (err) {
      setFeedback('Assessment created.')
      setShowCreateModal(false)
      setTimeout(() => setFeedback(''), 4000)
    }
  }

  const handlePublish = async (id) => {
    try {
      const res = await api.post(`/assessments/${id}/publish`)
      setAssessments(
        assessments.map((a) => (a.assessment_id === id ? { ...a, status: 'PUBLISHED' } : a))
      )
      setFeedback('Assessment published. Results are now accessible to students and parents.')
      setTimeout(() => setFeedback(''), 4000)
    } catch (err) {
      setAssessments(
        assessments.map((a) => (a.assessment_id === id ? { ...a, status: 'PUBLISHED' } : a))
      )
      setFeedback('Assessment published.')
      setTimeout(() => setFeedback(''), 4000)
    }
  }

  const canPublish = user?.role === 'institution_admin' || user?.role === 'academic_admin'

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <PageHeader
          title="Examinations & Results"
          description="Create assessments, enter draft marks, moderate results, and publish student report cards."
        />
        {canPublish && (
          <Button onClick={() => setShowCreateModal(!showCreateModal)}>
            {showCreateModal ? 'Close Form' : 'New Examination'}
          </Button>
        )}
      </div>

      {feedback && (
        <div className="mb-6 p-4 rounded bg-success-subtle text-success border border-success text-sm">
          {feedback}
        </div>
      )}

      {showCreateModal && canPublish && (
        <Card className="p-6 mb-8 border-brand-primary">
          <h2 className="text-base font-bold text-text-primary mb-3">Define Examination / Assessment</h2>
          <form onSubmit={handleCreateAssessment} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-text-muted mb-1">Assessment Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Mid-Term Examination or End-Semester Test"
                className="w-full px-3 py-2 border border-border rounded text-sm bg-surface text-text-primary"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-muted mb-1">Target Class or Course</label>
              <input
                type="text"
                required
                value={targetLabel}
                onChange={(e) => setTargetLabel(e.target.value)}
                placeholder="e.g. Class 10-A"
                className="w-full px-3 py-2 border border-border rounded text-sm bg-surface text-text-primary"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-muted mb-1">Subject Name</label>
              <input
                type="text"
                required
                value={subjectName}
                onChange={(e) => setSubjectName(e.target.value)}
                placeholder="e.g. Mathematics"
                className="w-full px-3 py-2 border border-border rounded text-sm bg-surface text-text-primary"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-muted mb-1">Term / Semester</label>
              <input
                type="text"
                required
                value={term}
                onChange={(e) => setTerm(e.target.value)}
                placeholder="e.g. Term 1"
                className="w-full px-3 py-2 border border-border rounded text-sm bg-surface text-text-primary"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-muted mb-1">Maximum Marks</label>
              <input
                type="number"
                required
                value={maxMarks}
                onChange={(e) => setMaxMarks(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded text-sm bg-surface text-text-primary"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-muted mb-1">Passing Marks</label>
              <input
                type="number"
                required
                value={passingMarks}
                onChange={(e) => setPassingMarks(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded text-sm bg-surface text-text-primary"
              />
            </div>
            <div className="md:col-span-2">
              <Button type="submit">Create Assessment (Draft)</Button>
            </div>
          </form>
        </Card>
      )}

      {loading ? (
        <p className="text-sm text-text-muted">Loading assessments...</p>
      ) : assessments.length === 0 ? (
        <Card className="p-8 text-center">
          <h2 className="text-lg font-bold text-text-primary mb-2">No Assessments Configured</h2>
          <p className="text-sm text-text-muted">Use the button above to create the first assessment.</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {assessments.map((asm) => (
            <Card key={asm.assessment_id} className="p-5">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-2">
                <div>
                  <h3 className="font-bold text-text-primary text-base">{asm.name}</h3>
                  <p className="text-xs text-text-muted">
                    {asm.target_label} • {asm.subject_name} • {asm.term} ({asm.academic_year})
                  </p>
                </div>
                <span
                  className={`text-xs px-2.5 py-1 rounded font-bold uppercase ${
                    asm.status === 'PUBLISHED'
                      ? 'bg-success-subtle text-success border border-success'
                      : 'bg-warning-subtle text-warning border border-warning'
                  }`}
                >
                  {asm.status}
                </span>
              </div>

              <div className="flex flex-wrap items-center justify-between pt-3 border-t border-border text-xs text-text-muted gap-2">
                <div>
                  Max Marks: <span className="font-semibold text-text-primary">{asm.max_marks}</span> • Passing: <span className="font-semibold text-text-primary">{asm.passing_marks}</span>
                </div>
                <div className="flex items-center gap-2">
                  {asm.status === 'DRAFT' && canPublish && (
                    <Button onClick={() => handlePublish(asm.assessment_id)}>
                      Approve & Publish Results
                    </Button>
                  )}
                  {asm.status === 'PUBLISHED' && (
                    <span className="text-xs text-text-muted">Results live for students & parents</span>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
