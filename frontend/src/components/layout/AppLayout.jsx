/** The application shell: responsive sidebar navigation, top bar controls and content frame. */
import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import LanguageSwitcher from '../common/LanguageSwitcher'
import ThemeToggle from '../common/ThemeToggle'
import DemoGuide from '../common/DemoGuide'
import VoiceButton from '../../voice/VoiceButton'
import VoicePanel from '../../voice/VoicePanel'
import AiAssistantDrawer from '../ai/AiAssistantDrawer'
import { useAuth } from '../../hooks/useAuth'
import { useApi } from '../../hooks/useApi'
import { api } from '../../services/api'
import { PERMISSIONS, ROLE_LABELS } from '../../utils/permissions'

const ROLE_NAVIGATIONS = {
  student: [
    { to: '/me', label: 'nav.dashboard', icon: 'dashboard' },
    { to: '/me/academics', label: 'nav.academics', icon: 'academic' },
    { to: '/me/attendance', label: 'nav.attendance', icon: 'attendance' },
    { to: '/me/timetable', label: 'nav.timetable', icon: 'timetable' },
    { to: '/me/assignments', label: 'nav.assignments', icon: 'assignments' },
    { to: '/me/results', label: 'nav.examinations', icon: 'examinations' },
    { to: '/me/results', label: 'nav.results', icon: 'results' },
    { to: '/me/id-card', label: 'nav.documents', icon: 'documents' },
    { to: '/library', label: 'nav.library', icon: 'library' },
    { to: '/opportunities', label: 'nav.opportunities', icon: 'opportunities' },
    { to: '/notifications', label: 'nav.notifications', icon: 'notifications' },
    { to: '/profile', label: 'nav.profile', icon: 'profile' },
  ],
  parent: [
    { to: '/parent', label: 'nav.dashboard', icon: 'dashboard' },
    { to: '/parent', label: 'nav.children', icon: 'students' },
    { to: '/parent', label: 'nav.attendance', icon: 'attendance' },
    { to: '/assessments', label: 'nav.results', icon: 'results' },
    { to: '/announcements', label: 'nav.announcements', icon: 'announcements' },
    { to: '/parent', label: 'nav.meetings', icon: 'timetable' },
    { to: '/notifications', label: 'nav.notifications', icon: 'notifications' },
    { to: '/profile', label: 'nav.profile', icon: 'profile' },
  ],
  teacher: [
    { to: '/teacher', label: 'nav.dashboard', icon: 'dashboard' },
    { to: '/teacher', label: 'nav.classes', icon: 'academic' },
    { to: '/teacher', label: 'nav.attendance', icon: 'attendance' },
    { to: '/teacher', label: 'nav.assignments', icon: 'assignments' },
    { to: '/assessments', label: 'nav.examinations', icon: 'examinations' },
    { to: '/assessments', label: 'nav.results', icon: 'results' },
    { to: '/students', label: 'nav.students', icon: 'students' },
    { to: '/announcements', label: 'nav.announcements', icon: 'announcements' },
    { to: '/profile', label: 'nav.profile', icon: 'profile' },
  ],
  institution_admin: [
    { to: '/institution', label: 'nav.dashboard', icon: 'dashboard' },
    { to: '/students', label: 'nav.students', icon: 'students' },
    { to: '/teacher', label: 'nav.staff', icon: 'staff' },
    { to: '/students', label: 'nav.admissions', icon: 'admissions' },
    { to: '/academic', label: 'nav.academics', icon: 'academic' },
    { to: '/teacher', label: 'nav.attendance', icon: 'attendance' },
    { to: '/assessments', label: 'nav.examinations', icon: 'examinations' },
    { to: '/reports', label: 'nav.reports', icon: 'reports' },
    { to: '/upload', label: 'nav.documents', icon: 'documents' },
    { to: '/notifications', label: 'nav.notifications', icon: 'notifications' },
    { to: '/profile', label: 'nav.settings', icon: 'profile' },
  ],
  university_admin: [
    { to: '/dashboard', label: 'nav.universityDashboard', icon: 'dashboard' },
    { to: '/institutions', label: 'nav.institutions', icon: 'institutions' },
    { to: '/academic', label: 'nav.departments', icon: 'academic' },
    { to: '/academic', label: 'nav.programmes', icon: 'academic' },
    { to: '/students', label: 'nav.students', icon: 'students' },
    { to: '/assessments', label: 'nav.examinations', icon: 'examinations' },
    { to: '/assessments', label: 'nav.results', icon: 'results' },
    { to: '/reports', label: 'nav.reports', icon: 'reports' },
    { to: '/profile', label: 'nav.settings', icon: 'profile' },
  ],
}

function NavIcon({ icon, className = 'w-4 h-4 flex-shrink-0' }) {
  const iconProps = { className, fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }

  switch (icon) {
    case 'dashboard':
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      )
    case 'academic':
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
        </svg>
      )
    case 'attendance':
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    case 'timetable':
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      )
    case 'assignments':
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
        </svg>
      )
    case 'examinations':
    case 'assessments':
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      )
    case 'results':
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    case 'documents':
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2M15 11h3m-3 4h2" />
        </svg>
      )
    case 'library':
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      )
    case 'opportunities':
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      )
    case 'notifications':
    case 'announcements':
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
      )
    case 'profile':
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      )
    case 'students':
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      )
    case 'staff':
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      )
    case 'admissions':
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
        </svg>
      )
    case 'reports':
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      )
    case 'institutions':
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      )
    default:
      return (
        <svg {...iconProps}>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
  }
}

export default function AppLayout() {
  const { user, role, logout } = useAuth()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [voiceOpen, setVoiceOpen] = useState(false)
  const [aiAssistantOpen, setAiAssistantOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    try {
      return localStorage.getItem('chhatralekha.sidebar_collapsed') === 'true'
    } catch {
      return false
    }
  })

  // Quick notifications popover
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [notifications, setNotifications] = useState([
    {
      id: 'ntf-01',
      title: 'Monthly Attendance Summary',
      message: 'October 2024 attendance recorded at 94.2%.',
      created_at: new Date().toISOString(),
    },
    {
      id: 'ntf-02',
      title: 'Examination Timetable',
      message: 'Mid-term schedule published.',
      created_at: new Date(Date.now() - 86400000).toISOString(),
    },
  ])

  const health = useApi(() => api.get('/health'), [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const toggleSidebarCollapse = () => {
    const next = !sidebarCollapsed
    setSidebarCollapsed(next)
    try {
      localStorage.setItem('chhatralekha.sidebar_collapsed', String(next))
    } catch {
      // Ignore
    }
  }

  const normalizedRole = (role || '').toLowerCase()

  // Select active role navigation
  let activeNav = ROLE_NAVIGATIONS[normalizedRole]
  if (!activeNav) {
    if (normalizedRole === 'college_admin' || normalizedRole === 'school_admin') {
      activeNav = ROLE_NAVIGATIONS.institution_admin
    } else if (
      normalizedRole === 'aicte_admin' ||
      normalizedRole === 'national_admin' ||
      normalizedRole === 'platform_operator'
    ) {
      activeNav = ROLE_NAVIGATIONS.university_admin
    } else {
      activeNav = ROLE_NAVIGATIONS.student
    }
  }

  const roleContextTitle =
    normalizedRole === 'student'
      ? 'Student Identity Hub'
      : normalizedRole === 'parent'
      ? 'Parent Portal'
      : normalizedRole === 'teacher'
      ? 'Teacher Workspace'
      : normalizedRole.includes('admin')
      ? 'Institutional Administration'
      : 'Academic Services'

  const homePath =
    normalizedRole === 'student'
      ? '/me'
      : normalizedRole === 'parent'
      ? '/parent'
      : normalizedRole === 'teacher'
      ? '/teacher'
      : normalizedRole.includes('univ') || normalizedRole === 'national_admin'
      ? '/dashboard'
      : '/institution'

  const userInitial = (user?.display_name || user?.full_name || user?.email || 'U').charAt(0).toUpperCase()

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <DemoGuide />

      <div className="flex-1 flex min-h-0 relative">
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
          className={`fixed inset-y-0 left-0 z-50 flex-shrink-0 bg-brand-deep text-white flex flex-col border-r border-navy-deep transition-all duration-200 ease-in-out lg:static lg:translate-x-0 ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          } ${sidebarCollapsed ? 'w-20' : 'w-64 lg:w-72'}`}
        >
          {/* Brand & Logo Header */}
          <div className="p-3 border-b border-white/10 flex items-center justify-between bg-black/15">
            <NavLink to={homePath} className="flex-1 block no-underline overflow-hidden">
              <div className="rounded-lg bg-white p-2 shadow-xs flex items-center justify-center">
                <img
                  src="/brand/chhatralekha-logo.png"
                  alt="ChhatraLekha - Authenticate, Verify, Empower"
                  className={`w-full object-contain block transition-all ${
                    sidebarCollapsed ? 'max-h-8' : 'max-h-12'
                  }`}
                />
              </div>
            </NavLink>

            {/* Desktop Collapse / Expand Toggle */}
            <button
              type="button"
              onClick={toggleSidebarCollapse}
              className="hidden lg:flex ml-2 p-1.5 rounded text-white/70 hover:text-white hover:bg-white/10 cursor-pointer border-0"
              title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {sidebarCollapsed ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                )}
              </svg>
            </button>

            {/* Mobile Close Button */}
            <button
              type="button"
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden ml-2 p-1.5 rounded text-white/70 hover:text-white hover:bg-white/10 cursor-pointer border-0"
              aria-label="Close navigation"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Section Context Header */}
          {!sidebarCollapsed && (
            <div className="px-5 pt-3 pb-1 text-[11px] font-semibold text-white/50 uppercase tracking-wider truncate">
              {roleContextTitle}
            </div>
          )}

          {/* Nav Links */}
          <nav className="flex-1 px-2.5 py-2 space-y-1 overflow-y-auto">
            {activeNav.map((item, idx) => (
              <NavLink
                key={`${item.to}-${idx}`}
                to={item.to}
                onClick={() => setSidebarOpen(false)}
                title={sidebarCollapsed ? t(item.label) : undefined}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors no-underline ${
                    sidebarCollapsed ? 'justify-center' : ''
                  } ${
                    isActive
                      ? 'bg-brand text-white shadow-xs font-semibold'
                      : 'text-white/80 hover:bg-white/10 hover:text-white'
                  }`
                }
              >
                <NavIcon icon={item.icon} />
                {!sidebarCollapsed && <span className="truncate">{t(item.label)}</span>}
              </NavLink>
            ))}
          </nav>

          {/* AI Assistant Quick Trigger in Sidebar */}
          <div className="p-2.5 border-t border-white/10">
            <button
              type="button"
              onClick={() => setAiAssistantOpen(true)}
              className={`w-full flex items-center justify-center gap-2 rounded-lg bg-accent text-on-accent p-2 text-xs font-bold shadow-xs hover:bg-accent-strong hover:text-white transition-colors cursor-pointer border-0 ${
                sidebarCollapsed ? 'px-1' : 'px-3'
              }`}
              title="Open Multilingual AI Assistant"
            >
              <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              {!sidebarCollapsed && <span>AI Assistant</span>}
            </button>
          </div>

          {/* User Profile Card & Sign Out at bottom of sidebar */}
          <div className="p-3 border-t border-white/10 bg-black/15">
            <NavLink
              to="/profile"
              className="flex items-center gap-2.5 mb-2.5 p-1 rounded hover:bg-white/10 transition-colors no-underline text-white block cursor-pointer"
              title="Open User Profile"
            >
              <div className="w-8 h-8 rounded-full bg-brand flex items-center justify-center font-bold text-xs text-white border border-white/20 flex-shrink-0">
                {userInitial}
              </div>
              {!sidebarCollapsed && (
                <div className="min-w-0 flex-1">
                  <p className="m-0 text-xs font-semibold text-white truncate">
                    {user?.display_name || user?.full_name || user?.email || 'User'}
                  </p>
                  <p className="m-0 text-[10px] text-white/60 truncate">
                    {ROLE_LABELS[normalizedRole] || normalizedRole}
                  </p>
                </div>
              )}
            </NavLink>

            <button
              type="button"
              onClick={handleLogout}
              className={`w-full flex items-center justify-center gap-2 rounded border border-white/20 bg-white/10 py-1.5 text-xs font-semibold text-white cursor-pointer hover:bg-white/20 transition-colors ${
                sidebarCollapsed ? 'px-1' : 'px-3'
              }`}
              title={t('nav.signOut')}
            >
              <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              {!sidebarCollapsed && <span>{t('nav.signOut')}</span>}
            </button>
          </div>
        </aside>

        {/* Main Content Frame */}
        <div className="flex-1 min-w-0 flex flex-col min-h-screen">
          {/* Top Header Controls */}
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
              <div className="flex items-center gap-2.5">
                <img
                  src="/brand/chhatralekha-logo.png"
                  alt="ChhatraLekha"
                  className="h-8 w-auto object-contain rounded bg-white p-0.5 border border-line lg:hidden"
                />
                <div className="hidden sm:flex items-center gap-2 text-xs text-muted">
                  <span className="font-semibold text-ink">{t('app.name')}</span>
                  <span>/</span>
                  <span>{roleContextTitle}</span>
                </div>
              </div>
            </div>

            {/* Right Top Header Actions */}
            <div className="flex items-center gap-2">
              {/* Notifications shortcut with quick popover */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setNotificationsOpen(!notificationsOpen)}
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
                  <div className="absolute right-0 mt-2 w-80 rounded-lg border border-line bg-surface p-4 text-ink shadow-md z-50 space-y-3">
                    <div className="flex items-center justify-between border-b border-line pb-2">
                      <span className="font-bold text-xs uppercase tracking-wider text-muted">Recent Notices</span>
                      <button
                        type="button"
                        onClick={() => setNotificationsOpen(false)}
                        className="text-xs text-muted hover:text-ink cursor-pointer bg-transparent border-0"
                      >
                        Close
                      </button>
                    </div>
                    <div className="max-h-60 overflow-y-auto space-y-2">
                      {notifications.map((n) => (
                        <div key={n.id} className="rounded border border-line bg-surface-2 p-2.5 text-xs space-y-0.5">
                          <p className="m-0 font-bold text-ink">{n.title}</p>
                          <p className="m-0 text-muted">{n.message}</p>
                          <p className="m-0 text-[10px] text-muted pt-1">{new Date(n.created_at).toLocaleDateString()}</p>
                        </div>
                      ))}
                    </div>
                    <div className="border-t border-line pt-2 text-center">
                      <NavLink
                        to="/notifications"
                        onClick={() => setNotificationsOpen(false)}
                        className="text-xs font-semibold text-brand hover:underline no-underline"
                      >
                        Open Notification Centre
                      </NavLink>
                    </div>
                  </div>
                )}
              </div>

              {/* Profile Shortcut */}
              <NavLink
                to="/profile"
                className="rounded border border-line bg-surface p-2 text-sm text-ink hover:bg-surface-2 cursor-pointer flex items-center justify-center no-underline"
                title="View Profile & Settings"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </NavLink>

              <ThemeToggle label={t('settings.theme.label')} />
              <LanguageSwitcher />

              {/* AI Assistant Button */}
              <button
                type="button"
                onClick={() => setAiAssistantOpen(true)}
                className="rounded border border-line bg-surface p-2 text-xs font-bold text-ink hover:border-brand cursor-pointer flex items-center gap-1.5 shadow-xs"
                title="Ask Multilingual AI Assistant"
              >
                <svg className="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span className="hidden md:inline">AI Helper</span>
              </button>

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
          <AiAssistantDrawer isOpen={aiAssistantOpen} onClose={() => setAiAssistantOpen(false)} />

          {/* App Footer */}
          <footer className="border-t border-line bg-surface py-4 text-center text-xs text-muted">
            <strong>{t('app.name')}</strong> - {t('app.prototypeNotice')}
          </footer>
        </div>
      </div>
    </div>
  )
}
