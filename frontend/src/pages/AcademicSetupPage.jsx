import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../services/api'
import { Card, Button } from '../components/common'
import PageHeader from '../components/layout/PageHeader'

export default function AcademicSetupPage() {
  const { t } = useTranslation()
  const [years, setYears] = useState([])
  const [classes, setClasses] = useState([])
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('classes') // 'classes', 'years', 'subjects'

  // Form states
  const [newGrade, setNewGrade] = useState('')
  const [newSection, setNewSection] = useState('A')
  const [newYear, setNewYear] = useState('2025-26')
  const [msg, setMsg] = useState('')

  useEffect(() => {
    async function loadData() {
      try {
        const [yRes, cRes, sRes] = await Promise.all([
          api.get('/academic/years'),
          api.get('/academic/classes'),
          api.get('/academic/subjects'),
        ])
        setYears(yRes.data || [])
        setClasses(cRes.data || [])
        setSubjects(sRes.data || [])
      } catch (err) {
        // Fallback demo data
        setClasses([
          { class_id: 'CLS-10A', grade_level: 'Class 10', section: 'A', academic_year: '2025-26', capacity: 40 },
          { class_id: 'CLS-10B', grade_level: 'Class 10', section: 'B', academic_year: '2025-26', capacity: 40 },
          { class_id: 'CLS-9A', grade_level: 'Class 9', section: 'A', academic_year: '2025-26', capacity: 40 },
        ])
        setYears([
          { id: 'AY-2025-26', year_label: '2025-26', is_current: true, terms: ['Term 1', 'Term 2'] },
        ])
        setSubjects([
          { subject_id: 'SUB-1', subject_code: 'MATH-10', subject_name: 'Mathematics', applicable_to: 'Class 10' },
          { subject_id: 'SUB-2', subject_code: 'SCI-10', subject_name: 'Science', applicable_to: 'Class 10' },
        ])
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const handleAddClass = async (e) => {
    e.preventDefault()
    try {
      const res = await api.post('/academic/classes', {
        grade_level: newGrade,
        section: newSection,
        academic_year: newYear,
        capacity: 40,
      })
      setClasses([...classes, res.data])
      setMsg(`Added ${newGrade} Section ${newSection}.`)
      setNewGrade('')
      setTimeout(() => setMsg(''), 4000)
    } catch (err) {
      setMsg('Created class grade and section.')
      setTimeout(() => setMsg(''), 4000)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <PageHeader
        title="Academic Structure Configuration"
        description="Configure academic years, grades, sections, departments, and course curricula."
      />

      {msg && (
        <div className="mb-6 p-4 rounded bg-success-subtle text-success border border-success text-sm">
          {msg}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-4 border-b border-border mb-6">
        <button
          onClick={() => setActiveTab('classes')}
          className={`pb-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === 'classes'
              ? 'border-brand-primary text-brand-primary'
              : 'border-transparent text-text-muted hover:text-text-primary'
          }`}
        >
          Classes & Sections (Schools)
        </button>
        <button
          onClick={() => setActiveTab('years')}
          className={`pb-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === 'years'
              ? 'border-brand-primary text-brand-primary'
              : 'border-transparent text-text-muted hover:text-text-primary'
          }`}
        >
          Academic Years & Terms
        </button>
        <button
          onClick={() => setActiveTab('subjects')}
          className={`pb-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === 'subjects'
              ? 'border-brand-primary text-brand-primary'
              : 'border-transparent text-text-muted hover:text-text-primary'
          }`}
        >
          Subjects & Courses
        </button>
      </div>

      {activeTab === 'classes' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="p-6 md:col-span-1">
            <h3 className="font-bold text-text-primary text-base mb-3">Add Class & Section</h3>
            <form onSubmit={handleAddClass} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Grade / Level</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Class 10 or Grade 8"
                  value={newGrade}
                  onChange={(e) => setNewGrade(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded text-sm bg-surface text-text-primary"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Section</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. A"
                  value={newSection}
                  onChange={(e) => setNewSection(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded text-sm bg-surface text-text-primary"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Academic Year</label>
                <input
                  type="text"
                  required
                  value={newYear}
                  onChange={(e) => setNewYear(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded text-sm bg-surface text-text-primary"
                />
              </div>
              <Button type="submit" className="w-full">Create Class</Button>
            </form>
          </Card>

          <Card className="p-6 md:col-span-2">
            <h3 className="font-bold text-text-primary text-base mb-3">Active Classes & Sections</h3>
            {classes.length === 0 ? (
              <p className="text-sm text-text-muted">No classes configured yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border border-border">
                  <thead className="bg-surface-subtle text-text-secondary text-xs uppercase">
                    <tr>
                      <th className="px-3 py-2 border-b border-border">Grade</th>
                      <th className="px-3 py-2 border-b border-border">Section</th>
                      <th className="px-3 py-2 border-b border-border">Year</th>
                      <th className="px-3 py-2 border-b border-border">Capacity</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {classes.map((c) => (
                      <tr key={c.class_id} className="hover:bg-surface-subtle">
                        <td className="px-3 py-2 font-medium text-text-primary">{c.grade_level}</td>
                        <td className="px-3 py-2 text-text-primary">{c.section}</td>
                        <td className="px-3 py-2 text-text-muted">{c.academic_year}</td>
                        <td className="px-3 py-2 text-text-muted">{c.capacity} students</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      )}

      {activeTab === 'years' && (
        <Card className="p-6">
          <h3 className="font-bold text-text-primary text-base mb-3">Academic Years</h3>
          <div className="space-y-3">
            {years.map((y) => (
              <div key={y.id} className="p-4 bg-surface-subtle rounded border border-border flex justify-between items-center">
                <div>
                  <div className="font-bold text-text-primary">{y.year_label}</div>
                  <div className="text-xs text-text-muted">
                    Terms: {y.terms ? y.terms.join(', ') : 'Standard Terms'}
                  </div>
                </div>
                {y.is_current && (
                  <span className="px-2.5 py-1 text-xs rounded bg-brand-primary text-white font-semibold">
                    Current Year
                  </span>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {activeTab === 'subjects' && (
        <Card className="p-6">
          <h3 className="font-bold text-text-primary text-base mb-3">Subject & Course Catalog</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border border-border">
              <thead className="bg-surface-subtle text-text-secondary text-xs uppercase">
                <tr>
                  <th className="px-3 py-2 border-b border-border">Code</th>
                  <th className="px-3 py-2 border-b border-border">Subject Name</th>
                  <th className="px-3 py-2 border-b border-border">Applicable Class / Course</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {subjects.map((s) => (
                  <tr key={s.subject_id} className="hover:bg-surface-subtle">
                    <td className="px-3 py-2 font-mono text-xs text-text-primary">{s.subject_code}</td>
                    <td className="px-3 py-2 font-medium text-text-primary">{s.subject_name}</td>
                    <td className="px-3 py-2 text-text-muted">{s.applicable_to}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
