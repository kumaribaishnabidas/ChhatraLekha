/** The application shell: the top bar, the navigation and the page frame. */
import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import LanguageSwitcher from '../common/LanguageSwitcher'
import ThemeToggle from '../common/ThemeToggle'
import DemoGuide from '../common/DemoGuide'
import VoiceButton from '../../voice/VoiceButton'
import VoicePanel from '../../voice/VoicePanel'
import { useAuth } from '../../hooks/useAuth'
import { useApi } from '../../hooks/useApi'
import { api } from '../../services/api'
import { PERMISSIONS, ROLE_LABELS } from '../../utils/permissions'

const NAVIGATION = [
  { to: '/dashboard', label: 'nav.dashboard', permission: PERMISSIONS.VIEW_NATIONAL_DASHBOARD },
  { to: '/institution', label: 'nav.institutionDashboard', permission: PERMISSIONS.VIEW_INSTITUTION_DASHBOARD },
  { to: '/wallet', label: 'nav.wallet', permission: PERMISSIONS.VIEW_OWN_RECORD },
  { to: '/institutions', label: 'nav.institutions', permission: PERMISSIONS.VIEW_COMPLIANCE_MATRIX },
  { to: '/students', label: 'nav.students', permission: PERMISSIONS.VIEW_STUDENT_REGISTER },
  { to: '/upload', label: 'nav.upload', permission: PERMISSIONS.IMPORT_CSV },
  { to: '/anomalies', label: 'nav.anomalies', permission: PERMISSIONS.REVIEW_ANOMALIES },
  { to: '/impact', label: 'nav.impact', permission: PERMISSIONS.PREVIEW_CORRECTION },
  { to: '/verify', label: 'nav.verify', permission: PERMISSIONS.VERIFY_CREDENTIAL },
  { to: '/reports', label: 'nav.reports', permission: PERMISSIONS.EXPORT_REPORTS },
]

const STUDENT_NAVIGATION = [
  { to: '/me', label: 'nav.home' },
  { to: '/me/id-card', label: 'nav.idCard' },
  { to: '/me/share', label: 'nav.shares' },
  { to: '/wallet', label: 'nav.wallet' },
  { to: '/me/consent', label: 'nav.consent' },
  { to: '/me/uploads', label: 'nav.uploads' },
  { to: '/me/results', label: 'nav.results' },
  { to: '/me/activity', label: 'nav.activity' },
]

export default function AppLayout() {
  const { user, role, can, logout } = useAuth()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const health = useApi(() => api.get('/health').then((r) => r.data), [])
  const [voiceOpen, setVoiceOpen] = useState(false)

  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [notifications, setNotifications] = useState([])

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  const loadNotifications = async () => {
    if (role !== 'student') return
    try {
      const { data } = await api.get('/me/notifications')
      setNotifications(data || [])
    } catch {
      // Ignore background notification fetch errors
    }
  }

  const handleToggleNotifications = () => {
    if (!notificationsOpen) loadNotifications()
    setNotificationsOpen(!notificationsOpen)
  }

  const homePath = role === 'student'
    ? '/me'
    : can(PERMISSIONS.VIEW_NATIONAL_DASHBOARD)
    ? '/dashboard'
    : can(PERMISSIONS.VIEW_INSTITUTION_DASHBOARD)
    ? '/institution'
    : can(PERMISSIONS.VIEW_OWN_RECORD)
    ? '/me'
    : '/verify'

  const activeNav = role === 'student' ? STUDENT_NAVIGATION : NAVIGATION.filter((item) => can(item.permission))

  return (
    <div className="min-h-screen">
      <DemoGuide />
      <header className="sticky top-0 z-40 bg-navy text-white border-b border-navy-deep">
        <div className="mx-auto max-w-[1240px] px-5 py-3 flex items-center gap-5">
          <NavLink to={homePath} className="flex items-center gap-3 no-underline">
            <img
              src="/brand/chhatralekha-lockup-inverse.svg"
              alt="ChhatraLekha"
              className="h-9 w-auto block"
              onError={(event) => {
                event.currentTarget.style.display = 'none'
              }}
            />
          </NavLink>

          <nav className="ml-auto flex items-center gap-1 overflow-x-auto">
            {activeNav.map((item) => (
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

          <div className="flex items-center gap-2 ps-3 border-s border-[var(--app-header-line)] relative">
            {role === 'student' && (
              <div className="relative">
                <button
                  type="button"
                  onClick={handleToggleNotifications}
                  className="rounded border border-white/20 bg-white/10 p-2 text-sm text-white hover:bg-white/20 cursor-pointer flex items-center justify-center"
                  title="Notifications"
                >
                  <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
                    <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
                  </svg>
                </button>
                {notificationsOpen && (
                  <div className="absolute right-0 mt-2 w-80 rounded-lg border border-line bg-surface p-4 text-ink shadow-[0_12px_30px_var(--app-shadow-strong)] z-50 space-y-3">
                    <div className="flex items-center justify-between border-b border-line pb-2">
                      <span className="font-bold text-xs uppercase tracking-wider text-muted">Notifications</span>
                      <button
                        type="button"
                        onClick={() => setNotificationsOpen(false)}
                        className="text-xs text-muted hover:text-ink cursor-pointer bg-transparent border-0"
                      >
                        Close
                      </button>
                    </div>
                    <div className="max-h-60 overflow-y-auto space-y-2">
                      {notifications.length === 0 ? (
                        <p className="m-0 text-xs text-muted text-center py-2">No new notifications.</p>
                      ) : (
                        notifications.map((n) => (
                          <div key={n.id} className="rounded border border-line bg-surface-2 p-2.5 text-xs space-y-0.5">
                            <p className="m-0 font-bold text-ink">{n.title}</p>
                            <p className="m-0 text-muted">{n.message}</p>
                            <p className="m-0 text-[10px] text-muted pt-1">{new Date(n.created_at).toLocaleString()}</p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
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
              className="rounded border border-white/30 bg-white/10 px-3 py-1.5 text-xs font-semibold text-white cursor-pointer hover:bg-white/20"
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
        <strong>{t('app.name')}</strong> - {t('app.prototypeNotice')}
      </footer>
    </div>
  )
}
