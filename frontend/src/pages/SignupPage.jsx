import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import ThemeToggle from '../components/common/ThemeToggle'
import LanguageSwitcher from '../components/common/LanguageSwitcher'
import { api, errorMessage } from '../services/api'

const ROLES = [
  { id: 'student', label: 'Student', desc: 'Access your APAAR ID, timetable & credentials' },
  { id: 'parent', label: 'Parent / Guardian', desc: 'Track child attendance & exam performance' },
  { id: 'teacher', label: 'Teacher / Faculty', desc: 'Mark period roll-call & submit assessments' },
  { id: 'institution_admin', label: 'Institution Admin', desc: 'Manage programmes, intake & compliance' },
]

export default function SignupPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  const [selectedRole, setSelectedRole] = useState('student')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [agreeTerms, setAgreeTerms] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccessMessage('')

    if (!fullName.trim()) {
      setError('Please provide your full legal name.')
      return
    }
    if (!email.trim() || !email.includes('@')) {
      setError('Please provide a valid institutional or personal e-mail address.')
      return
    }
    if (!password || password.length < 8) {
      setError('Password must contain at least 8 characters.')
      return
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (!agreeTerms) {
      setError('You must agree to the Terms of Service and Privacy Policy to proceed.')
      return
    }

    setIsSubmitting(true)

    try {
      const response = await api.post('/auth/register', {
        email: email.trim().toLowerCase(),
        password,
        full_name: fullName.trim(),
        role: selectedRole,
        identifier: identifier.trim() || undefined,
      })
      const data = response.data
      const message = data.message || 'Account created successfully! Redirecting to sign in...'
      setSuccessMessage(message)
      setTimeout(() => {
        navigate('/login', {
          state: {
            registeredEmail: email.trim().toLowerCase(),
            registeredRole: data.role,
            notice: message,
          },
        })
      }, 1200)
    } catch (err) {
      setError(errorMessage(err, 'Unable to complete registration. Please try again.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-canvas">
      {/* Left Column: Visual Inspiration & Platform Identity */}
      <section className="hidden lg:flex flex-col justify-between bg-brand-deep text-white p-10 lg:p-14 border-r border-line">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-white p-2.5 shadow-xs border border-line">
            <img
              src="/brand/chhatralekha-logo.png"
              alt="ChhatraLekha - Authenticate, Verify, Empower"
              className="w-[200px] h-auto block"
            />
          </div>
          <span className="rounded-full bg-accent/20 border border-accent/40 text-accent-strong px-3 py-1 text-xs font-bold uppercase tracking-wider">
            Public Pilot
          </span>
        </div>

        <div className="max-w-xl space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold text-white/90">
            <span className="h-2 w-2 rounded-full bg-accent" aria-hidden="true" />
            National Multilingual Academic Platform
          </div>

          <h1 className="m-0 text-white text-3xl xl:text-4xl font-black leading-tight tracking-tight">
            Create Your Verifiable Academic Identity
          </h1>

          <p className="m-0 text-white/85 text-base leading-relaxed">
            Join students, parents, faculty, and educational institutions across India. Access your tamper-evident academic records, track attendance in real time, and share credentials with full privacy control.
          </p>

          <div className="grid gap-3 pt-2">
            <div className="flex items-start gap-3 p-3.5 rounded-lg bg-white/10 border border-white/15">
              <div className="mt-0.5 rounded bg-accent/20 p-1.5 text-accent">
                <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <h2 className="text-sm font-bold text-white m-0">Zero Personal Data Exposure</h2>
                <p className="text-xs text-white/75 m-0 mt-0.5 leading-relaxed">
                  Cryptographically signed tokens mask your 12-digit APAAR ID and personal identifiers on all public verification links.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3.5 rounded-lg bg-white/10 border border-white/15">
              <div className="mt-0.5 rounded bg-accent/20 p-1.5 text-accent">
                <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <div>
                <h2 className="text-sm font-bold text-white m-0">22 Scheduled Indian Languages</h2>
                <p className="text-xs text-white/75 m-0 mt-0.5 leading-relaxed">
                  Navigate seamlessly in Hindi, Odia, Bengali, Tamil, Telugu, Marathi, and your preferred mother tongue with voice assistance.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3.5 rounded-lg bg-white/10 border border-white/15">
              <div className="mt-0.5 rounded bg-accent/20 p-1.5 text-accent">
                <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <h2 className="text-sm font-bold text-white m-0">Live Timetable &amp; Attendance</h2>
                <p className="text-xs text-white/75 m-0 mt-0.5 leading-relaxed">
                  Daily period roll-call synced between instructors, guardians, and students without paper circulars.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-white/20 text-xs text-white/60">
          Educational Demonstration Sandbox. Strictly follows Digital Personal Data Protection (DPDP) Act principles.
        </div>
      </section>

      {/* Right Column: Clean Registration Form */}
      <section className="flex items-center justify-center p-6 sm:p-10">
        <div className="card w-full max-w-lg p-7 sm:p-9 shadow-xs">
          <div className="flex items-center justify-between gap-3 mb-6">
            <Link to="/" className="rounded bg-white p-1 border border-line lg:hidden no-underline">
              <img
                src="/brand/chhatralekha-logo.png"
                alt="ChhatraLekha"
                className="w-[120px] h-auto block"
              />
            </Link>
            <div className="hidden lg:block">
              <span className="text-xs font-bold uppercase tracking-wider text-muted">
                Registration
              </span>
            </div>
            <div className="flex items-center gap-2">
              <ThemeToggle variant="surface" />
              <LanguageSwitcher variant="surface" />
            </div>
          </div>

          <h2 className="m-0 text-2xl font-black text-brand-text">
            Get Started with ChhatraLekha
          </h2>
          <p className="m-0 mt-1 mb-6 text-sm text-muted">
            Create your account to access student credentials, timetables, and academic operations.
          </p>

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <div>
              <span className="label">Select Your Role</span>
              <div className="grid grid-cols-2 gap-2">
                {ROLES.map((r) => (
                  <button
                    key={r.id}
                    type="button"
                    onClick={() => setSelectedRole(r.id)}
                    className={`p-2.5 rounded border text-start cursor-pointer transition-colors ${
                      selectedRole === r.id
                        ? 'border-brand bg-brand/10 text-brand font-bold'
                        : 'border-line bg-surface text-ink hover:bg-surface-2'
                    }`}
                  >
                    <div className="text-xs font-bold">{r.label}</div>
                    <div className="text-[10px] text-muted line-clamp-1 mt-0.5">{r.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="label" htmlFor="fullName">
                Full Legal Name
              </label>
              <input
                id="fullName"
                className="input"
                type="text"
                autoComplete="name"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Aarav Sharma"
              />
            </div>

            <div>
              <label className="label" htmlFor="email">
                E-mail address
              </label>
              <input
                id="email"
                className="input"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@institution.edu.in or personal email"
              />
            </div>

            <div>
              <label className="label" htmlFor="identifier">
                {selectedRole === 'student' ? 'Roll Number / APAAR ID (Optional)' : 'Institution / Department Name (Optional)'}
              </label>
              <input
                id="identifier"
                className="input"
                type="text"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder={selectedRole === 'student' ? 'e.g. CS-2024-042' : 'e.g. Vidya Vikas Institute of Technology'}
              />
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="label" htmlFor="password">
                  Password
                </label>
                <div className="relative">
                  <input
                    id="password"
                    className="input pr-14"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Min 8 characters"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((p) => !p)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    className="absolute right-2 top-1/2 -translate-y-1/2 px-1.5 py-0.5 text-xs font-semibold text-muted hover:text-ink cursor-pointer focus-visible:outline-none"
                  >
                    {showPassword ? 'Hide' : 'Show'}
                  </button>
                </div>
              </div>

              <div>
                <label className="label" htmlFor="confirmPassword">
                  Confirm Password
                </label>
                <div className="relative">
                  <input
                    id="confirmPassword"
                    className="input pr-14"
                    type={showConfirmPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword((p) => !p)}
                    aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                    className="absolute right-2 top-1/2 -translate-y-1/2 px-1.5 py-0.5 text-xs font-semibold text-muted hover:text-ink cursor-pointer focus-visible:outline-none"
                  >
                    {showConfirmPassword ? 'Hide' : 'Show'}
                  </button>
                </div>
              </div>
            </div>

            <div className="pt-1">
              <label className="flex items-start gap-2.5 text-xs text-muted cursor-pointer">
                <input
                  id="agreeTerms"
                  type="checkbox"
                  checked={agreeTerms}
                  onChange={(e) => setAgreeTerms(e.target.checked)}
                  className="mt-0.5 rounded border-line text-brand focus:ring-brand"
                />
                <span>
                  I agree to the{' '}
                  <Link to="/terms" target="_blank" className="text-brand font-semibold underline">
                    Terms of Service
                  </Link>{' '}
                  and{' '}
                  <Link to="/privacy" target="_blank" className="text-brand font-semibold underline">
                    Privacy Policy
                  </Link>
                  , and understand that ChhatraLekha handles academic records under strict data privacy protocols.
                </span>
              </label>
            </div>

            {error && (
              <p role="alert" className="mt-3 mb-0 text-sm text-crimson">
                {error}
              </p>
            )}

            {successMessage && (
              <p role="status" className="mt-3 mb-0 text-sm text-emerald font-semibold">
                {successMessage}
              </p>
            )}

            <button
              type="submit"
              className="btn btn-navy w-full mt-4"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Creating Account...' : 'Complete Registration'}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-line text-center text-xs text-muted">
            Already have an account?{' '}
            <Link to="/login" className="text-brand font-bold underline">
              Sign In
            </Link>
          </div>

          <div className="mt-4 text-center">
            <Link
              to="/"
              className="text-xs text-muted hover:text-ink inline-flex items-center gap-1 no-underline"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span>Back to ChhatraLekha Overview</span>
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}

