import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export default function KeyboardShortcuts() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [showHelp, setShowHelp] = useState(false)

  useEffect(() => {
    let pendingG = false
    let timeoutId = null

    function handleKeyDown(event) {
      // Ignore if user is currently typing in an input, textarea, or contentEditable element
      const target = event.target
      const tagName = target?.tagName
      if (
        tagName === 'INPUT' ||
        tagName === 'TEXTAREA' ||
        tagName === 'SELECT' ||
        target?.isContentEditable
      ) {
        return
      }

      // Escape closes the help dialog
      if (event.key === 'Escape' && showHelp) {
        setShowHelp(false)
        return
      }

      // Shortcut: '?' toggles help dialog
      if (event.key === '?' || (event.shiftKey && event.key === '/')) {
        event.preventDefault()
        setShowHelp((prev) => !prev)
        return
      }

      // Shortcut: '/' focuses search input
      if (event.key === '/' && !event.ctrlKey && !event.metaKey) {
        event.preventDefault()
        const searchInput = document.querySelector(
          'input[type="search"], input[name="search"], input[placeholder*="search" i], input[placeholder*="Search" i]'
        )
        if (searchInput) {
          searchInput.focus()
        }
        return
      }

      // Shortcut sequence: 'g' then 'd' goes to Dashboard
      if (event.key === 'g' || event.key === 'G') {
        pendingG = true
        clearTimeout(timeoutId)
        timeoutId = setTimeout(() => {
          pendingG = false
        }, 1000)
        return
      }

      if (pendingG && (event.key === 'd' || event.key === 'D')) {
        pendingG = false
        clearTimeout(timeoutId)
        event.preventDefault()
        navigate('/dashboard')
        return
      }

      pendingG = false
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      clearTimeout(timeoutId)
    }
  }, [navigate, showHelp])

  if (!showHelp) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="shortcuts-dialog-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
    >
      <div className="card w-full max-w-md p-6 bg-surface border border-line">
        <div className="flex items-center justify-between pb-3 border-b border-line mb-4">
          <h2 id="shortcuts-dialog-title" className="m-0 text-base font-bold text-navy">
            Keyboard shortcuts
          </h2>
          <button
            type="button"
            onClick={() => setShowHelp(false)}
            aria-label="Close dialog"
            className="text-muted hover:text-ink text-sm font-semibold cursor-pointer"
          >
            Close
          </button>
        </div>

        <dl className="grid grid-cols-2 gap-y-3 text-sm">
          <dt className="text-muted">Focus search</dt>
          <dd className="text-right">
            <kbd className="px-2 py-0.5 rounded bg-surface-2 border border-line font-mono text-xs">
              /
            </kbd>
          </dd>

          <dt className="text-muted">Go to Dashboard</dt>
          <dd className="text-right flex justify-end gap-1">
            <kbd className="px-2 py-0.5 rounded bg-surface-2 border border-line font-mono text-xs">
              g
            </kbd>
            <span className="text-muted text-xs">then</span>
            <kbd className="px-2 py-0.5 rounded bg-surface-2 border border-line font-mono text-xs">
              d
            </kbd>
          </dd>

          <dt className="text-muted">Open shortcuts help</dt>
          <dd className="text-right">
            <kbd className="px-2 py-0.5 rounded bg-surface-2 border border-line font-mono text-xs">
              ?
            </kbd>
          </dd>

          <dt className="text-muted">Close modal</dt>
          <dd className="text-right">
            <kbd className="px-2 py-0.5 rounded bg-surface-2 border border-line font-mono text-xs">
              Esc
            </kbd>
          </dd>
        </dl>

        <p className="mt-5 mb-0 text-xs text-muted">
          Note: Shortcuts are disabled while typing in any form field. Shortcuts never trigger any record updates, token revocations, or data deletion.
        </p>
      </div>
    </div>
  )
}
