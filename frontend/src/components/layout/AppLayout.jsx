/** The application shell: sidebar navigation, top bar controls and content frame. */
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
  { to: '/academic', label: 'nav.academic', permission: PERMISSIONS.MANAGE_ACADEMIC_SETUP },
  { to: '/teacher', label: 'nav.teacherWorkspace', permission: PERMISSIONS.RECORD_ATTENDANCE },
  { to: '/assessments', label: 'nav.assessments', permission: PERMISSIONS.VIEW_RESULTS },
  { to: '/announcements', label: 'nav.announcements', permission: PERMISSIONS.VIEW_ANNOUNCEMENTS },
  { to: '/parent', label: 'nav.parentPortal', permission: PERMISSIONS.VIEW_PARENT_PORTAL },
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
  { to: '/announcements', label: 'nav.announcements' },
  { to: '/wallet', label: 'nav.wallet' },
  { to: '/me/consent', label: 'nav.consent' },
  { to: '/me/uploads', label: 'nav.uploads' },
  { to: '/me/results', label: 'nav.results' },
  { to: '/me/activity', label: 'nav.activity' },
]

function NavIcon({ to }) {
  const iconProps = { className: 'w-4 h-4 flex-shrink-0', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }
  if (to === '/me' || to === '/dashboard' || to === '/institution') {
    return (
      <svg {...iconProps}>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    )
  }
  if (to === '/me/id-card') {
    return (
      <svg {...iconProps}>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2M15 11h3m-3 4h2" />
      </svg>
    )
  }
  if (to === '/me/share') {
    return (
      <svg {...iconProps}>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
      </svg>
    )
  }
  if (to === '/announcements') {
    return (
      <svg {...iconProps}>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
      </svg>
    )
  }
  if (to === '/wallet') {
    return (
      <svg {...iconProps}>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
      </svg>
    )
  }
  if (to === '/me/consent') {
    return (
      <svg {...iconProps}>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    )
  }
  if (to === '/me/uploads' || to === '/upload') {
    return (
      <svg {...iconProps}>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
    )
  }
  if (to === '/me/results' || to === '/assessments') {
    return (
      <svg {...iconProps}>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    )
  }
  if (to === '/me/activity') {
    return (
      <svg {...iconProps}>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    )
  }
  if (to === '/students') {
    return (
      <svg {...iconProps}>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
      </svg>
    )
  }
  if (to === '/anomalies') {
    return (
      <svg {...iconProps}>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    )
  }
  if (to === '/impact') {
    return (
      <svg {...iconProps}>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
      </svg>
    )
  }
  if (to === '/verify') {
    return (
      <svg {...iconProps}>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
      </svg>
    )
  }
  if (to === '/reports') {
    return (
      <svg {...iconProps}>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    )
  }
  return (
    <svg {...iconProps}>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
    </svg>
  )
}

export default function AppLayout() {
  const { user, role, can, logout } = useAuth()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const health = useApi(() => api.get('/health').then((r) => r.data), [])
  const [voiceOpen, setVoiceOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)

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
    : role === 'parent'
    ? '/parent'
    : role === 'teacher'
    ? '/teacher'
    : can(PERMISSIONS.VIEW_NATIONAL_DASHBOARD)
    ? '/dashboard'
    : can(PERMISSIONS.VIEW_INSTITUTION_DASHBOARD)
    ? '/institution'
    : can(PERMISSIONS.VIEW_OWN_RECORD)
    ? '/me'
    : '/verify'

  const activeNav = role === 'student' ? STUDENT_NAVIGATION : NAVIGATION.filter((item) => can(item.permission))

  const roleContextTitle =
    role === 'student'
      ? 'Student Identity Hub'
      : role === 'parent'
      ? 'Parent Portal'
      : role === 'teacher'
      ? 'Teacher Workspace'
      : role === 'institution_admin'
      ? 'Institution Operations'
      : role === 'verifier'
      ? 'Credential Verification'
      : 'National Administration'

  return (
    <div className="min-h-screen flex bg-canvas">
      <DemoGuide />

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Left Sidebar Navigation */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 lg:w-72 bg-brand-deep text-white flex flex-col border-r border-navy-deep transition-transform duration-200 ease-in-out lg:static lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand & Logo Header */}
        <div className="p-4 sm:p-5 border-b border-white/10 flex items-center justify-between">
          <NavLink to={homePath} className="flex items-center gap-3 no-underline">
            <img
              src="/brand/chhatralekha-logo.png"
              alt="ChhatraLekha"
              className="h-9 w-auto rounded bg-white p-1"
              onError={(event) => {
                event.currentTarget.style.display = 'none'
              }}
            />
            <div>
              <span className="font-bold text-white text-base tracking-tight block">ChhatraLekha</span>
              <span className="text-[10px] text-white/70 uppercase tracking-wider block">Unified Campus</span>
            </div>
          </NavLink>

          <button
            type="button"
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1.5 rounded text-white/70 hover:text-white hover:bg-white/10 cursor-pointer"
            aria-label="Close navigation"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Section Context Header */}
        <div className="px-5 pt-4 pb-1 text-[11px] font-semibold text-white/50 uppercase tracking-wider">
          {roleContextTitle}
        </div>

        {/* Nav Links */}
        <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
          {activeNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors no-underline ${
                  isActive
                    ? 'bg-brand text-white shadow-sm font-semibold'
                    : 'text-white/80 hover:bg-white/10 hover:text-white'
                }`
              }
            >
              <NavIcon to={item.to} />
              <span>{t(item.label)}</span>
            </NavLink>
          ))}
        </nav>

        {/* User Card & Sign Out at bottom of sidebar */}
        <div className="p-4 border-t border-white/10 bg-black/10">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-brand flex items-center justify-center font-bold text-xs text-white border border-white/20 flex-shrink-0">
              {(user?.display_name || user?.name || user?.email || 'U').charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="m-0 text-xs font-semibold text-white truncate">
                {user?.display_name || user?.name || user?.email || t('login.signIn')}
              </p>
              <p className="m-0 text-[10px] text-white/60 truncate">
                {ROLE_LABELS[role] || role}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 rounded border border-white/20 bg-white/10 px-3 py-1.5 text-xs font-semibold text-white cursor-pointer hover:bg-white/20 transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span>{t('nav.signOut')}</span>
          </button>
        </div>
      </aside>

      {/* Main Content Frame */}
      <div className="flex-1 min-w-0 flex flex-col min-h-screen">
        {/* Top Controls Header */}
        <header className="sticky top-0 z-30 bg-surface border-b border-line px-4 sm:px-6 py-2.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-lg text-ink hover:bg-surface-2 border border-line cursor-pointer flex items-center justify-center"
              aria-label="Open navigation"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="hidden sm:flex items-center gap-2 text-xs text-muted">
              <span className="font-semibold text-ink">{t('app.name')}</span>
              <span>/</span>
              <span>{roleContextTitle}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {role === 'student' && (
              <div className="relative">
                <button
                  type="button"
                  onClick={handleToggleNotifications}
                  className="rounded border border-line bg-surface p-2 text-sm text-ink hover:bg-surface-2 cursor-pointer flex items-center justify-center relative"
                  title="Notifications"
                >
                  <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
                    <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
                  </svg>
                  {notifications.length > 0 && (
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-accent" />
                  )}
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
          </div>
        </header>

        {/* Demo Data Warning Banner */}
        {health.data?.in_memory_demo_data && (
          <div
            role="status"
            className="bg-warning-surface border-b border-warning/40 px-5 py-2 text-center text-xs text-warning-strong"
          >
            <strong>{t('app.name')}.</strong> {health.data.notice}
          </div>
        )}

        {/* Main Content Area */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
          <Outlet />
        </main>

        {voiceOpen && <VoicePanel onClose={() => setVoiceOpen(false)} />}

        {/* App Footer */}
        <footer className="border-t border-line bg-surface py-4 text-center text-xs text-muted">
          <strong>{t('app.name')}</strong> - {t('app.prototypeNotice')}
        </footer>
      </div>
    </div>
  )
}
