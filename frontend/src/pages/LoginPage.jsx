import { useEffect, useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import GoogleSignInButton from '../components/common/GoogleSignInButton'
import LanguageSwitcher from '../components/common/LanguageSwitcher'
import ThemeToggle from '../components/common/ThemeToggle'
import { useAuth } from '../hooks/useAuth'
import { api, errorMessage } from '../services/api'

export default function LoginPage() {
  const { login, isAuthenticated, loading } = useAuth()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [googleEnabled, setGoogleEnabled] = useState(false)

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
    try {
      const data = await login(email, password)
      const target =
        data.role === 'aicte_admin' ? '/dashboard' : location.state?.from || '/dashboard'
      navigate(target, { replace: true })
    } catch (caught) {
      setError(errorMessage(caught, t('login.failed'), t))
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-canvas">
      <section className="hidden lg:flex flex-col justify-between bg-gradient-to-br from-navy via-mid-blue to-bright-blue text-white p-12">
        <div className="flex items-center gap-3">
          <img src="/brand/edusync-lockup.png" alt="EduSynC" className="h-11 w-auto" />
        </div>
        <div className="max-w-xl">
          <h1 className="m-0 text-white text-4xl leading-tight">
              {t('login.headline')}
          </h1>
          <p className="mt-4 text-white/85 leading-relaxed">
            {t('login.description')}
          </p>
          <ul className="mt-6 pl-5 text-white/80 leading-loose">
            <li>{t('login.featureAnomaly')}</li>
            <li>{t('login.featureImpact')}</li>
            <li>{t('login.featureToken')}</li>
            <li>{t('login.featureConsent')}</li>
          </ul>
        </div>
        <p className="m-0 text-xs text-white/60">
          {t('app.prototypeNotice')}
        </p>
      </section>

      <section className="flex items-center justify-center p-6">
        <div className="card w-full max-w-md p-7">
          <div className="flex items-center justify-between gap-3 mb-6">
            <img src="/brand/edusync-wordmark.png" alt="EduSynC" className="h-9 w-auto" />
            <div className="flex items-center gap-2">
              <ThemeToggle variant="surface" label={t('settings.theme.label')} />
              <LanguageSwitcher variant="surface" />
            </div>
          </div>
          <h2 className="m-0 text-xl">{t('login.title')}</h2>
          <p className="m-0 mt-1 mb-5 text-sm text-muted">
            {t('login.lead')}
          </p>

          <form onSubmit={handleSubmit} noValidate>
            <label className="label" htmlFor="email">
              {t('login.email')}
            </label>
            <input
              id="email"
              className="input"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder={t('login.emailPlaceholder')}
            />

            <label className="label mt-4" htmlFor="password">
              {t('login.password')}
            </label>
            <input
              id="password"
              className="input"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder={t('login.passwordPlaceholder')}
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
              {loading ? t('login.signingIn') : t('login.signIn')}
            </button>
          </form>

          {googleEnabled && (
            <>
              <div className="my-5 flex items-center gap-3">
                <span className="h-px flex-1 bg-line" />
                <span className="text-[11px] font-bold uppercase tracking-widest text-muted">
                  {t('login.or')}
                </span>
                <span className="h-px flex-1 bg-line" />
              </div>
              <GoogleSignInButton />
              <p className="mt-2 mb-0 text-center text-[11px] text-muted">
                {t('login.googleRestricted')}
              </p>
            </>
          )}

          <div className="mt-6 pt-5 border-t border-line">
            <p className="m-0 text-xs text-muted">
              {t('login.demo')}
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
