/** The application shell: responsive modular sidebar navigation, top bar controls and content frame. */
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
import { Sidebar, MobileBottomBar, useNavigation } from '../../modules/navigation'
import { NotificationBell, useNotifications } from '../../modules/notifications'

export default function AppLayout() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const { t } = useTranslation()

  const [voiceOpen, setVoiceOpen] = useState(false)
  const [aiAssistantOpen, setAiAssistantOpen] = useState(false)

  const {
    navItems,
    roleContextTitle,
    homePath,
    sidebarOpen,
    setSidebarOpen,
    sidebarCollapsed,
    toggleSidebarCollapse,
    user,
    role,
  } = useNavigation()

  const {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
  } = useNotifications()

  const health = useApi(() => api.get('/health'), [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

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

        {/* Shared Modular Sidebar */}
        <Sidebar
          navItems={navItems}
          roleContextTitle={roleContextTitle}
          homePath={homePath}
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
          sidebarCollapsed={sidebarCollapsed}
          toggleSidebarCollapse={toggleSidebarCollapse}
          user={user}
          role={role}
          onLogout={handleLogout}
          onOpenAiAssistant={() => setAiAssistantOpen(true)}
          unreadCount={unreadCount}
        />

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
              {/* Modular Notification Bell with Quick Popover */}
              <NotificationBell
                unreadCount={unreadCount}
                notifications={notifications}
                onMarkRead={markAsRead}
                onMarkAllRead={markAllAsRead}
              />

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
          <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full pb-20 lg:pb-8">
            <Outlet />
          </main>

          {voiceOpen && <VoicePanel onClose={() => setVoiceOpen(false)} />}
          <AiAssistantDrawer isOpen={aiAssistantOpen} onClose={() => setAiAssistantOpen(false)} />

          {/* App Footer */}
          <footer className="border-t border-line bg-surface py-4 text-center text-xs text-muted mb-14 lg:mb-0">
            <strong>{t('app.name')}</strong> - {t('app.prototypeNotice')}
          </footer>
        </div>
      </div>

      {/* Mobile Bottom Navigation Bar */}
      <MobileBottomBar navItems={navItems} unreadCount={unreadCount} />
    </div>
  )
}
