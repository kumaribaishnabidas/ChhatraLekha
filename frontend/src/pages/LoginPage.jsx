import { useEffect, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import GoogleSignInButton from '../components/common/GoogleSignInButton'
import LanguageSwitcher from '../components/common/LanguageSwitcher'
import ThemeToggle from '../components/common/ThemeToggle'
import { useAuth } from '../hooks/useAuth'
import { api, errorMessage } from '../services/api'

const QUICK_DEMO_PERSONAS = [
  { role: 'student', label: 'Student', email: 'student.demo@example.com', target: '/me' },
  { role: 'parent', label: 'Parent', email: 'parent.demo@example.com', target: '/parent' },
  { role: 'teacher', label: 'Faculty', email: 'teacher.demo@example.com', target: '/teacher' },
  { role: 'school_admin', label: 'School Admin', email: 'schooladmin.demo@example.com', target: '/institution' },
  { role: 'college_admin', label: 'College Admin', email: 'collegeadmin.demo@example.com', target: '/institution' },
  { role: 'university_admin', label: 'Directorate', email: 'universityadmin.demo@example.com', target: '/dashboard' },
]

export default function LoginPage() {
  const { login, isAuthenticated, loading } = useAuth()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [googleEnabled, setGoogleEnabled] = useState(false)
  const [demoSigningIn, setDemoSigningIn] = useState(null)

  useEffect(() => {
    // If redirected from registration
    if (location.state?.registeredEmail) {
      setEmail(location.state.registeredEmail)
    }
    if (location.state?.notice) {
      setNotice(location.state.notice)
    }
  }, [location.state])

  useEffect(() => {
    // The backend tells the portal whether Google sign-in is configured.
    api
      .get('/auth/google/config')
      .then((response) => setGoogleEnabled(Boolean(response.data?.enabled)))
      .catch(() => setGoogleEnabled(false))
  }, [])

  useEffect(() => {
    // A failed Google sign-in comes back with the reason in the fragment.
    const fragment = window.location.hash.startsWith('#')
      ? window.location.hash.slice(1)
      : window.location.hash
    if (!fragment) return
    const params = new URLSearchParams(fragment)
    const failure = params.get('error')
    if (failure) {
      setError(failure)
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

  if (isAuthenticated) {
    return <Navigate to={location.state?.from || '/dashboard'} replace />
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setNotice('')
    try {
      const data = await login(email, password)
      const target =
        data.role === 'aicte_admin'
          ? '/dashboard'
          : data.role === 'student'
          ? '/me'
          : data.role === 'parent'
          ? '/parent'
          : data.role === 'teacher'
          ? '/teacher'
          : location.state?.from || '/dashboard'
      navigate(target, { replace: true })
    } catch (caught) {
      setError(errorMessage(caught, t('login.failed', 'Sign-in failed.'), t))
    }
  }

  const handleQuickDemo = async (persona) => {
    setError('')
    setNotice('')
    setDemoSigningIn(persona.role)
    try {
      // First attempt the dedicated secure demo-login endpoint
      const res = await api.post('/auth/demo-login', { role: persona.role }).catch(async () => {
        // Fallback to standard login with standard seed password
        return await api.post('/auth/login', {
          email: persona.email,
          password: 'Password@123',
        }).catch(async () => {
          return await api.post('/auth/login', {
            email: persona.email,
            password: 'ChhatraLekha2026!',
          })
        })
      })

      if (res?.data?.access_token) {
        login(res.data)
        navigate(persona.target, { replace: true })
      } else {
        navigate(persona.target)
      }
    } catch (caught) {
      setError(errorMessage(caught, 'Demo login unavailable. Please sign in with test credentials.', t))
    } finally {
      setDemoSigningIn(null)
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-canvas">
      {/* Left Column: Visual Education Identity & Trust Panel */}
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
            Verified Identity
          </span>
        </div>

        <div className="max-w-xl space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold text-white/90">
            <span className="h-2 w-2 rounded-full bg-accent" aria-hidden="true" />
            National Education Operations System
          </div>

          <h1 className="m-0 text-white text-3xl xl:text-4xl font-black leading-tight tracking-tight">
            {t('login.headline', 'One APAAR ID. One verifiable academic record.')}
          </h1>

          <p className="m-0 text-white/85 text-base leading-relaxed">
            {t(
              'login.description',
              'ChhatraLekha validates every enrolment as it is uploaded, detects regulatory breaches before they reach the national registry, and issues credentials that any employer can check with a signed, expiring, revocable token.',
            )}
          </p>

          <div className="grid gap-3 pt-2">
            <div className="flex items-center gap-3 p-3 rounded-lg bg-white/10 border border-white/15 text-sm">
              <span className="h-2 w-2 rounded-full bg-accent shrink-0" aria-hidden="true" />
              <span>{t('login.featureAnomaly', 'Ten-layer automated anomaly detection')}</span>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg bg-white/10 border border-white/15 text-sm">
              <span className="h-2 w-2 rounded-full bg-accent shrink-0" aria-hidden="true" />
              <span>{t('login.featureImpact', 'Change impact detection before a correction is applied')}</span>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg bg-white/10 border border-white/15 text-sm">
              <span className="h-2 w-2 rounded-full bg-accent shrink-0" aria-hidden="true" />
              <span>{t('login.featureToken', 'Opaque verification tokens - no raw APAAR ID in a URL')}</span>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg bg-white/10 border border-white/15 text-sm">
              <span className="h-2 w-2 rounded-full bg-accent shrink-0" aria-hidden="true" />
              <span>{t('login.featureConsent', 'Purpose-wise, revocable student consent')}</span>
            </div>
          </div>

          {/* Synthetic student card visual preview */}
          <div className="p-4 rounded-lg bg-white/10 border border-white/20 text-xs space-y-2">
            <div className="flex items-center justify-between text-white/70">
              <span className="font-bold uppercase tracking-wider text-[10px]">Academic Badge Mockup</span>
              <span className="text-accent font-semibold">2026-27 Active</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded bg-accent/30 text-accent font-bold flex items-center justify-center text-sm">
                AS
              </div>
              <div>
                <div className="font-bold text-white text-sm">Aarav Sharma</div>
                <div className="text-white/70">B.Tech Computer Science - Vidya Vikas Institute</div>
              </div>
            </div>
          </div>
        </div>

        <p className="m-0 text-xs text-white/60">
          {t('app.prototypeNotice', 'Synthetic demonstration data only. Verification is against this prototype database.')}
        </p>
      </section>

      {/* Right Column: Clean Form Container */}
      <section className="flex items-center justify-center p-6 sm:p-10">
        <div className="card w-full max-w-md p-7 sm:p-9 shadow-xs">
          <div className="flex items-center justify-between gap-3 mb-6">
            <Link to="/" className="rounded bg-white p-1 border border-line lg:hidden no-underline">
              <img
                src="/brand/chhatralekha-logo.png"
                alt="ChhatraLekha - Authenticate, Verify, Empower"
                className="w-[120px] h-auto block"
              />
            </Link>
            <div className="hidden lg:block">
              <span className="text-xs font-bold uppercase tracking-wider text-muted">
                Portal Authentication
              </span>
            </div>
            <div className="flex items-center gap-2">
              <ThemeToggle variant="surface" label={t('settings.theme.label', 'Theme')} />
              <LanguageSwitcher variant="surface" />
            </div>
          </div>

          <h2 className="m-0 text-2xl font-black text-brand-text">
            {t('login.title', 'Sign in')}
          </h2>
          <p className="m-0 mt-1 mb-5 text-sm text-muted">
            {t('login.lead', 'Use the account issued to you by the education authority or your institution.')}
          </p>

          {notice && (
            <div className="mb-4 p-3 rounded bg-success-surface border border-success/30 text-xs text-success-strong font-medium">
              {notice}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            <label className="label" htmlFor="email">
              {t('login.email', 'E-mail address')}
            </label>
            <input
              id="email"
              className="input"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder={t('login.emailPlaceholder', 'you@college.edu.in')}
            />

            <div className="mt-4 flex items-center justify-between">
              <label className="label m-0" htmlFor="password">
                {t('login.password', 'Password')}
              </label>
              <Link to="/contact" className="text-xs text-brand hover:underline font-semibold no-underline">
                Forgot password?
              </Link>
            </div>
            <div className="relative mt-1">
              <input
                id="password"
                className="input pr-16"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder={t('login.passwordPlaceholder', 'Your password')}
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                aria-label={showPassword ? t('login.hide', 'Hide') : t('login.show', 'Show')}
                className="absolute right-2 top-1/2 -translate-y-1/2 px-2 py-1 text-xs font-semibold text-muted hover:text-ink cursor-pointer focus-visible:outline-none"
              >
                {showPassword ? t('login.hide', 'Hide') : t('login.show', 'Show')}
              </button>
            </div>

            {error && (
              <p role="alert" className="mt-3 mb-0 text-sm text-crimson">
                {error}
              </p>
            )}

            <button
              type="submit"
              className="btn btn-navy w-full mt-5 font-bold"
              disabled={loading || Boolean(demoSigningIn)}
            >
              {loading ? t('login.signingIn', 'Signing in...') : t('login.signIn', 'Sign in')}
            </button>
          </form>

          {/* Quick Demo Persona Shortcuts */}
          <div className="mt-6 pt-5 border-t border-line">
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-xs font-bold uppercase tracking-wider text-brand-text">
                Explore Demo Personas
              </span>
              <span className="text-[10px] rounded bg-accent/15 text-accent-strong px-2 py-0.5 font-bold">
                1-Click Instant Login
              </span>
            </div>
            <p className="text-xs text-muted mb-3 m-0">
              Select a persona to test the portal with pre-loaded synthetic academic records:
            </p>
            <div className="grid grid-cols-3 gap-2">
              {QUICK_DEMO_PERSONAS.map((p) => (
                <button
                  key={p.role}
                  type="button"
                  onClick={() => handleQuickDemo(p)}
                  disabled={Boolean(demoSigningIn) || loading}
                  className="px-2 py-1.5 rounded border border-line bg-surface-2 hover:border-brand hover:bg-surface text-xs font-semibold text-ink text-center transition-colors cursor-pointer disabled:opacity-50"
                >
                  {demoSigningIn === p.role ? '...' : p.label}
                </button>
              ))}
            </div>
          </div>

          {googleEnabled && (
            <>
              <div className="my-5 flex items-center gap-3">
                <span className="h-px flex-1 bg-line" />
                <span className="text-[11px] font-bold uppercase tracking-widest text-muted">
                  {t('login.or', 'or')}
                </span>
                <span className="h-px flex-1 bg-line" />
              </div>
              <GoogleSignInButton />
              <p className="mt-2 mb-0 text-center text-[11px] text-muted">
                {t('login.googleRestricted', 'A first-time Google sign-in creates an account with the restricted verifier role.')}
              </p>
            </>
          )}

          <div className="mt-6 pt-5 border-t border-line text-center text-xs text-muted">
            Don't have an account yet?{' '}
            <Link to="/signup" className="text-brand font-bold underline">
              Sign up for early access
            </Link>
          </div>

          <div className="mt-3 text-center">
            <Link to="/" className="text-xs text-muted hover:text-ink no-underline inline-flex items-center gap-1">
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
