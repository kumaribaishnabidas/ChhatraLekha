import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { Card, Button } from '../components/common'

export default function EarlyAccessPage() {
  usePageMeta({
    title: 'Early Access & Institutional Pilot',
    description: 'Register your school or college for early access and pilot onboarding on the ChhatraLekha unified education platform.',
    canonical: '/early-access',
  })

  const navigate = useNavigate()
  const [form, setForm] = useState({
    contactName: '',
    workEmail: '',
    phone: '',
    institutionName: '',
    institutionKind: 'SCHOOL',
    state: '',
    district: '',
    studentCount: '100-500',
    notes: '',
  })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!form.contactName.trim() || !form.workEmail.trim() || !form.institutionName.trim() || !form.state.trim()) {
      setError('Please provide your name, official email, institution name, and state.')
      return
    }
    setError('')
    setSubmitting(true)

    setTimeout(() => {
      setSubmitting(false)
      navigate('/thank-you', {
        state: {
          name: form.contactName,
          email: form.workEmail,
          message: `Your early pilot application for ${form.institutionName} has been recorded. Our team will review your application within 2 business days.`,
        },
      })
    }, 600)
  }

  return (
    <div className="mx-auto max-w-[900px] px-5 py-12 space-y-10">
      <div className="space-y-3">
        <div className="inline-flex items-center gap-2 rounded-full border border-accent/40 bg-accent/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-accent-strong">
          <span className="h-2 w-2 rounded-full bg-accent" aria-hidden="true" />
          Public Benefit Pilot Program
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-brand tracking-tight m-0">
          Request Early Pilot Access
        </h1>
        <p className="text-base sm:text-lg text-muted max-w-2xl leading-relaxed m-0">
          ChhatraLekha is expanding to partner schools, polytechnics, and colleges across India. Join our controlled pilot with zero licensing costs, zero advertising, and full data sovereignty.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2">
          <form onSubmit={handleSubmit} className="border border-line rounded-lg bg-surface p-6 sm:p-8 space-y-5 shadow-sm">
            {error && (
              <div role="alert" className="p-3.5 rounded border border-danger/40 bg-danger-surface text-danger-strong text-sm">
                {error}
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="contactName" className="block text-xs font-bold uppercase tracking-wider text-muted mb-1">
                  Contact Name <span className="text-danger-strong">*</span>
                </label>
                <input
                  id="contactName"
                  type="text"
                  required
                  value={form.contactName}
                  onChange={(e) => setForm({ ...form, contactName: e.target.value })}
                  className="w-full px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-brand text-sm"
                  placeholder="Principal / Administrator Name"
                />
              </div>

              <div>
                <label htmlFor="workEmail" className="block text-xs font-bold uppercase tracking-wider text-muted mb-1">
                  Official Email <span className="text-danger-strong">*</span>
                </label>
                <input
                  id="workEmail"
                  type="email"
                  required
                  value={form.workEmail}
                  onChange={(e) => setForm({ ...form, workEmail: e.target.value })}
                  className="w-full px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-brand text-sm"
                  placeholder="admin@school.ac.in"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="phone" className="block text-xs font-bold uppercase tracking-wider text-muted mb-1">
                  Phone (Optional)
                </label>
                <input
                  id="phone"
                  type="tel"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  className="w-full px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-brand text-sm"
                  placeholder="+91 98765 43210"
                />
              </div>

              <div>
                <label htmlFor="institutionKind" className="block text-xs font-bold uppercase tracking-wider text-muted mb-1">
                  Institution Kind <span className="text-danger-strong">*</span>
                </label>
                <select
                  id="institutionKind"
                  value={form.institutionKind}
                  onChange={(e) => setForm({ ...form, institutionKind: e.target.value })}
                  className="w-full px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-brand text-sm"
                >
                  <option value="SCHOOL">K-12 School</option>
                  <option value="SENIOR_SECONDARY_SCHOOL">Senior Secondary School (Grades 11-12)</option>
                  <option value="COLLEGE">Higher Education College</option>
                  <option value="POLYTECHNIC">Polytechnic / ITI</option>
                  <option value="UNIVERSITY">University / Autonomous Institute</option>
                </select>
              </div>
            </div>

            <div>
              <label htmlFor="institutionName" className="block text-xs font-bold uppercase tracking-wider text-muted mb-1">
                Institution Name <span className="text-danger-strong">*</span>
              </label>
              <input
                id="institutionName"
                type="text"
                required
                value={form.institutionName}
                onChange={(e) => setForm({ ...form, institutionName: e.target.value })}
                className="w-full px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-brand text-sm"
                placeholder="Delhi Public School or Govt Model College"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label htmlFor="state" className="block text-xs font-bold uppercase tracking-wider text-muted mb-1">
                  State / UT <span className="text-danger-strong">*</span>
                </label>
                <input
                  id="state"
                  type="text"
                  required
                  value={form.state}
                  onChange={(e) => setForm({ ...form, state: e.target.value })}
                  className="w-full px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-brand text-sm"
                  placeholder="e.g. Maharashtra"
                />
              </div>

              <div>
                <label htmlFor="district" className="block text-xs font-bold uppercase tracking-wider text-muted mb-1">
                  District
                </label>
                <input
                  id="district"
                  type="text"
                  value={form.district}
                  onChange={(e) => setForm({ ...form, district: e.target.value })}
                  className="w-full px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-brand text-sm"
                  placeholder="e.g. Pune"
                />
              </div>

              <div>
                <label htmlFor="studentCount" className="block text-xs font-bold uppercase tracking-wider text-muted mb-1">
                  Enrolment Size
                </label>
                <select
                  id="studentCount"
                  value={form.studentCount}
                  onChange={(e) => setForm({ ...form, studentCount: e.target.value })}
                  className="w-full px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-brand text-sm"
                >
                  <option value="under-100">Under 100 students</option>
                  <option value="100-500">100 - 500 students</option>
                  <option value="500-2000">500 - 2,000 students</option>
                  <option value="2000-plus">2,000+ students</option>
                </select>
              </div>
            </div>

            <div>
              <label htmlFor="notes" className="block text-xs font-bold uppercase tracking-wider text-muted mb-1">
                Special Requirements or Questions
              </label>
              <textarea
                id="notes"
                rows={3}
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                className="w-full px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-brand text-sm"
                placeholder="Mention specific workflows such as transfer certificates, attendance, or offline mobile sync."
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              disabled={submitting}
              className="w-full py-3"
            >
              {submitting ? 'Submitting Application...' : 'Apply for Early Pilot Access'}
            </Button>
            <p className="m-0 text-center text-xs text-muted">
              By submitting, you agree to our{' '}
              <Link to="/privacy" className="text-brand underline hover:text-brand-deep">Privacy Policy</Link> and{' '}
              <Link to="/terms" className="text-brand underline hover:text-brand-deep">Terms of Service</Link>.
            </p>
          </form>
        </div>

        <div className="space-y-6">
          <Card className="p-5 space-y-3 bg-surface-2">
            <h2 className="text-sm font-bold uppercase tracking-wider text-brand m-0">Pilot Commitments</h2>
            <ul className="text-xs text-muted space-y-2 pl-4 list-disc m-0 leading-relaxed">
              <li><strong>Zero Cost:</strong> No license fees, onboarding charges, or hidden recurring costs.</li>
              <li><strong>Data Sovereignty:</strong> Complete tenant isolation; student records are never sold or used for advertising.</li>
              <li><strong>Dedicated Guidance:</strong> Step-by-step assistance with CSV intake, academic year setup, and credential distribution.</li>
              <li><strong>Offline Resilience:</strong> Android mobile app support for rural campus connectivity and field verification.</li>
            </ul>
          </Card>

          <Card className="p-5 space-y-2 bg-surface-2">
            <h2 className="text-sm font-bold uppercase tracking-wider text-brand m-0">Direct Coordinator</h2>
            <p className="text-xs text-muted m-0 leading-relaxed">
              Have an urgent question regarding state board affiliation or university deployment?
            </p>
            <p className="text-xs font-mono text-brand font-semibold m-0 pt-1">
              pilot@chhatralekha.in
            </p>
          </Card>
        </div>
      </div>
    </div>
  )
}

