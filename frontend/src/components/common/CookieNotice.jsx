import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const STORAGE_KEY = 'edusync.cookie_ack'

export default function CookieNotice() {
  const { t } = useTranslation()
  const [acknowledged, setAcknowledged] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === 'true'
    } catch {
      return false
    }
  })

  if (acknowledged) {
    return null
  }

  function handleAcknowledge() {
    try {
      localStorage.setItem(STORAGE_KEY, 'true')
    } catch {
      // Ignore storage restrictions
    }
    setAcknowledged(true)
  }

  return (
    <aside
      aria-label="Privacy and cookies"
      className="fixed bottom-0 inset-x-0 z-40 bg-surface border-t border-line p-4 text-xs text-ink shadow-sm"
    >
      <div className="mx-auto max-w-[1200px] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <p className="m-0 leading-relaxed text-muted">
          This platform uses only strictly necessary browser storage for session authentication, theme, and language preferences. No tracking, advertising, or third-party marketing cookies are used.{' '}
          <Link to="/privacy" className="text-brand-bright underline hover:text-brand-mid">
            Privacy policy
          </Link>
        </p>
        <button
          type="button"
          onClick={handleAcknowledge}
          className="btn btn-navy text-xs px-3 py-1.5 whitespace-nowrap cursor-pointer shrink-0"
        >
          Acknowledge
        </button>
      </div>
    </aside>
  )
}
