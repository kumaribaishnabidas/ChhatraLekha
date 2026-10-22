/**
 * The light / dark / system switch.
 *
 * A three-state segmented control. Every state is a real button, so it is
 * reachable with the keyboard and announced by a screen reader.
 */
import { useTheme } from '../../context/ThemeContext'
import { useTranslation } from 'react-i18next'

const STATES = [
  { value: 'light', labelKey: 'settings.theme.light', icon: SunIcon },
  { value: 'dark', labelKey: 'settings.theme.dark', icon: MoonIcon },
  { value: 'system', labelKey: 'settings.theme.system', icon: ScreenIcon },
]

export default function ThemeToggle({ variant = 'header', label = 'Theme' }) {
  const { theme, setTheme } = useTheme()
  const { t } = useTranslation()

  return (
    <div
      role="group"
      aria-label={label}
      className={
        variant === 'header'
          ? 'inline-flex items-center rounded-full border border-[var(--app-header-line)] bg-[var(--app-header-hover)] p-0.5'
          : 'inline-flex items-center rounded-full border border-line bg-surface-2 p-0.5'
      }
    >
      {STATES.map((state) => {
        const Icon = state.icon
        const selected = theme === state.value
        return (
          <button
            key={state.value}
            type="button"
            aria-pressed={selected}
            title={t(state.labelKey)}
            onClick={() => setTheme(state.value)}
            className={[
              'rounded-full p-1.5 cursor-pointer transition-colors',
              variant === 'header'
                ? selected
                  ? 'bg-[var(--app-header-active)] text-white'
                  : 'text-[var(--app-header-ink-soft)] hover:bg-[var(--app-header-hover)]'
                : selected
                  ? 'bg-surface text-brand-text shadow-sm'
                  : 'text-muted hover:text-brand-text',
            ].join(' ')}
          >
            <Icon />
            <span className="sr-only">{t(state.labelKey)}</span>
          </button>
        )
      })}
    </div>
  )
}

function SunIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="4.5" stroke="currentColor" strokeWidth="1.8" />
      <path
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M18.7 5.3l-1.4 1.4M6.7 17.3l-1.4 1.4"
      />
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M20 14.2A8.2 8.2 0 0 1 9.8 4a8.2 8.2 0 1 0 10.2 10.2Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function ScreenIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="2.5" y="4" width="19" height="13" rx="2" stroke="currentColor" strokeWidth="1.8" />
      <path stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" d="M8 21h8M12 17v4" />
    </svg>
  )
}
