import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'
import { errorMessage } from '../services/api'

export default function LoginPage() {
  const { login, isAuthenticated, loading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  if (isAuthenticated) {
    return <Navigate to={location.state?.from || '/dashboard'} replace />
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    try {
      const data = await login(email, password)
      const target =
        data.role === 'aicte_admin' ? '/dashboard' : location.state?.from || '/dashboard'
      navigate(target, { replace: true })
    } catch (caught) {
      setError(errorMessage(caught, 'Sign-in failed.'))
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      <section className="hidden lg:flex flex-col justify-between bg-gradient-to-br from-navy via-mid-blue to-bright-blue text-white p-12">
        <div className="flex items-center gap-3">
          <img src="/brand/edusync-lockup.png" alt="EduSynC" className="h-11 w-auto" />
        </div>
        <div className="max-w-xl">
          <h1 className="m-0 text-white text-4xl leading-tight">
            One APAAR ID. One verifiable academic record.
          </h1>
          <p className="mt-4 text-white/85 leading-relaxed">
            EduSynC validates every enrolment as it is uploaded, detects the regulatory
            breaches before they reach the national registry, and issues credentials that
            any employer can verify offline.
          </p>
          <ul className="mt-6 pl-5 text-white/80 leading-loose">
            <li>Ten-layer automated anomaly detection</li>
            <li>Signed, offline-verifiable APAAR credentials</li>
            <li>Purpose-wise, revocable student consent</li>
            <li>A tamper-evident, hash-chained audit trail</li>
          </ul>
        </div>
        <p className="m-0 text-xs text-white/60">
          Synthetic demonstration data only. &copy; EduSynC.
        </p>
      </section>

      <section className="flex items-center justify-center p-6">
        <div className="card w-full max-w-md p-7">
          <div className="lg:hidden flex items-center gap-3 mb-6">
            <img src="/brand/edusync-wordmark.png" alt="EduSynC" className="h-9 w-auto" />
          </div>
          <h2 className="m-0 text-xl">Sign in</h2>
          <p className="m-0 mt-1 mb-5 text-sm text-muted">
            Use the account issued to you by the AICTE Directorate or your institution.
          </p>

          <form onSubmit={handleSubmit} noValidate>
            <label className="label" htmlFor="email">
              E-mail address
            </label>
            <input
              id="email"
              className="input"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@college.edu.in"
            />

            <label className="label mt-4" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              className="input"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Your password"
            />

            {error && (
              <p role="alert" className="mt-3 mb-0 text-sm text-crimson">
                {error}
              </p>
            )}

            <button
              type="submit"
              className="btn btn-navy w-full mt-5"
              disabled={loading}
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-line">
            <p className="m-0 text-xs text-muted">
              Demo accounts (development only): <strong>aicte.admin@edusync.gov.in</strong>,
              <strong> principal@vidyavikas.edu.in</strong>,{' '}
              <strong>verifier@acme-corp.com</strong> &mdash; password{' '}
              <strong>EduSync@2024</strong>.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
