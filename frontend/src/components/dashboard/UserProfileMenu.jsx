import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../hooks/useAuth'

export default function UserProfileMenu({ onLogout }) {
  const { t } = useTranslation()
  const { user, role } = useAuth()
  const [open, setOpen] = useState(false)
  const menuRef = useRef(null)

  const name = user?.display_name || user?.full_name || user?.email || 'User'
  const email = user?.email || 'user@chhatralekha.edu.in'
  const roleLabel = (role || user?.role || 'User').replace(/_/g, ' ').toUpperCase()
  const initial = name.charAt(0).toUpperCase()
  const institution = user?.institution_name || user?.institution_id || 'ChhatraLekha Platform'

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded-lg border border-line bg-surface p-1.5 hover:bg-surface-2 transition-colors cursor-pointer text-left"
        aria-expanded={open}
        aria-haspopup="true"
        aria-label="User account menu"
      >
        <div className="h-7 w-7 rounded-full bg-brand text-white flex items-center justify-center text-xs font-bold shrink-0">
          {initial}
        </div>
        <div className="hidden xl:block min-w-0 pr-1">
          <p className="m-0 text-xs font-bold text-heading truncate max-w-[120px]">{name}</p>
          <p className="m-0 text-[10px] text-muted truncate">{roleLabel}</p>
        </div>
        <svg
          className={`w-3.5 h-3.5 text-muted transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-72 rounded-lg border border-line bg-surface shadow-md p-3 z-50 text-left space-y-3">
          {/* User Info Header */}
          <div className="border-b border-line pb-3 space-y-1">
            <div className="flex items-center gap-2">
              <div className="h-9 w-9 rounded-full bg-brand text-white flex items-center justify-center text-sm font-bold shrink-0">
                {initial}
              </div>
              <div className="min-w-0 flex-1">
                <p className="m-0 text-sm font-bold text-heading truncate">{name}</p>
                <p className="m-0 text-xs text-muted truncate">{email}</p>
              </div>
            </div>
            <div className="flex items-center justify-between pt-1">
              <span className="rounded-full bg-brand-light px-2 py-0.5 text-[10px] font-bold text-brand uppercase tracking-wider">
                {roleLabel}
              </span>
              <span className="text-[10px] text-muted truncate font-medium max-w-[140px]" title={institution}>
                {institution}
              </span>
            </div>
          </div>

          {/* Quick Menu Links */}
          <div className="space-y-1 text-xs">
            <Link
              to="/profile"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 px-2.5 py-2 rounded-md text-heading hover:bg-surface-2 no-underline transition-colors font-medium"
            >
              <svg className="w-4 h-4 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              <span>{t('nav.profile', { defaultValue: 'My Profile & Preferences' })}</span>
            </Link>
            <Link
              to="/notifications"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 px-2.5 py-2 rounded-md text-heading hover:bg-surface-2 no-underline transition-colors font-medium"
            >
              <svg className="w-4 h-4 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <span>{t('nav.notifications', { defaultValue: 'Notifications Centre' })}</span>
            </Link>
            <Link
              to="/help"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 px-2.5 py-2 rounded-md text-heading hover:bg-surface-2 no-underline transition-colors font-medium"
            >
              <svg className="w-4 h-4 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{t('footer.help', { defaultValue: 'Help & Documentation' })}</span>
            </Link>
          </div>

          {/* Sign Out Action */}
          <div className="border-t border-line pt-2">
            <button
              type="button"
              onClick={() => {
                setOpen(false)
                onLogout?.()
              }}
              className="w-full flex items-center gap-2 px-2.5 py-2 rounded-md text-xs font-semibold text-danger hover:bg-danger/10 transition-colors cursor-pointer border-0 text-left"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span>{t('auth.logout', { defaultValue: 'Sign Out' })}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
