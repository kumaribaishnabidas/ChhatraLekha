/** The application shell: the top bar, the navigation and the page frame. */
import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import LanguageSwitcher from '../common/LanguageSwitcher'
import ThemeToggle from '../common/ThemeToggle'
import VoiceButton from '../../voice/VoiceButton'
import VoicePanel from '../../voice/VoicePanel'
import { useAuth } from '../../hooks/useAuth'
import { useApi } from '../../hooks/useApi'
import { api } from '../../services/api'
import { PERMISSIONS, ROLE_LABELS } from '../../utils/permissions'

const NAVIGATION = [
  { to: '/dashboard', label: 'nav.dashboard', permission: PERMISSIONS.VIEW_NATIONAL_DASHBOARD },
  { to: '/institutions', label: 'nav.institutions', permission: PERMISSIONS.VIEW_COMPLIANCE_MATRIX },
  { to: '/students', label: 'nav.students', permission: PERMISSIONS.VIEW_STUDENT_REGISTER },
  { to: '/upload', label: 'nav.upload', permission: PERMISSIONS.IMPORT_CSV },
  { to: '/anomalies', label: 'nav.anomalies', permission: PERMISSIONS.REVIEW_ANOMALIES },
  { to: '/impact', label: 'nav.impact', permission: PERMISSIONS.PREVIEW_CORRECTION },
  { to: '/verify', label: 'nav.verify', permission: PERMISSIONS.VERIFY_CREDENTIAL },
  { to: '/reports', label: 'nav.reports', permission: PERMISSIONS.EXPORT_REPORTS },
]

export default function AppLayout() {
  const { user, role, can, logout } = useAuth()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const health = useApi(() => api.get('/health').then((r) => r.data), [])
  const [voiceOpen, setVoiceOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 bg-navy text-white shadow-lg">
        <div className="mx-auto max-w-[1240px] px-5 py-3 flex items-center gap-5">
          <NavLink to="/dashboard" className="flex items-center gap-3 no-underline">
            <img
              src="/brand/edusync-lockup.png"
              alt="EduSynC"
              className="h-9 w-auto block"
              onError={(event) => {
                event.currentTarget.style.display = 'none'
              }}
            />
            <span className="hidden sm:inline font-extrabold tracking-wide text-lg">
              EduSynC
            </span>
          </NavLink>

          <nav className="ml-auto flex items-center gap-1 overflow-x-auto">
            {NAVIGATION.filter((item) => can(item.permission)).map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-2 text-sm font-semibold no-underline whitespace-nowrap ${
                    isActive ? 'bg-white/15 text-white' : 'text-white/80 hover:bg-white/10'
                  }`
                }
              >
                {t(item.label)}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-2 ps-3 border-s border-[var(--app-header-line)]">
            <ThemeToggle label={t('settings.theme.label')} />
            <LanguageSwitcher />
            <VoiceButton onClick={() => setVoiceOpen(true)} />
            <div className="hidden md:block text-right leading-tight">
              <p className="m-0 text-sm font-semibold">{user?.display_name || t('login.signIn')}</p>
              <p className="m-0 text-[11px] text-white/70">{ROLE_LABELS[role] || role}</p>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-full border border-white/30 bg-white/10 px-3 py-1.5 text-xs font-semibold text-white cursor-pointer"
            >
              {t('nav.signOut')}
            </button>
          </div>
        </div>
      </header>

      {health.data?.in_memory_demo_data && (
        <div
          role="status"
          className="bg-warning-surface border-b border-warning/40 px-5 py-2 text-center text-sm text-warning-strong"
        >
          <strong>{t('app.name')}.</strong> {health.data.notice}
        </div>
      )}

      <main className="mx-auto max-w-[1240px] px-5 py-7">
        <Outlet />
      </main>

      {voiceOpen && <VoicePanel onClose={() => setVoiceOpen(false)} />}

      <footer className="border-t border-line bg-surface py-5 text-center text-xs text-muted">
        <strong>{t('app.name')}</strong> &mdash; {t('app.prototypeNotice')}
      </footer>
    </div>
  )
}
