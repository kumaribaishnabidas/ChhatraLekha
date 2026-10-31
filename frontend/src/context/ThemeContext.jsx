/**
 * The theme controller.
 *
 * The user can choose **light**, **dark** or **system**. The choice is kept
 * in `localStorage` (when the browser allows it) and applied as
 * `data-theme="light" | "dark"` on the `<html>` element, which is what the
 * `dark:` variant and the CSS variables react to.
 *
 * When the choice is "system", the media query `prefers-color-scheme` decides,
 * and the controller listens for changes so the application follows the
 * operating system while it is open.
 *
 * An inline script in `index.html` sets the attribute before React loads, so
 * there is never a flash of the wrong theme.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

const STORAGE_KEY = 'chhatralekha.theme'

export const THEME_CHOICES = ['light', 'dark', 'system']

/** The colour of the browser chrome, per theme. */
const THEME_COLOR = { light: '#2F57D6', dark: '#0B1437' }

const ThemeContext = createContext(null)

/** Read the stored choice. A browser with storage disabled must not crash. */
function readStoredTheme() {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY)
    return THEME_CHOICES.includes(stored) ? stored : 'system'
  } catch {
    return 'system'
  }
}

/** Whether the operating system asks for a dark appearance. */
function systemPrefersDark() {
  try {
    return Boolean(
      window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches,
    )
  } catch {
    return false
  }
}

function applyTheme(theme) {
  const resolved = theme === 'system' ? (systemPrefersDark() ? 'dark' : 'light') : theme
  const root = document.documentElement
  root.setAttribute('data-theme', resolved)
  root.style.colorScheme = resolved

  const meta = document.querySelector('meta[name="theme-color"]')
  if (meta) meta.setAttribute('content', THEME_COLOR[resolved] || THEME_COLOR.light)
  return resolved
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(readStoredTheme)
  const [resolved, setResolved] = useState(() =>
    applyTheme(readStoredTheme()),
  )

  const setTheme = useCallback((next) => {
    const choice = THEME_CHOICES.includes(next) ? next : 'system'
    setThemeState(choice)
    setResolved(applyTheme(choice))
    try {
      window.localStorage.setItem(STORAGE_KEY, choice)
    } catch {
      /* storage unavailable - the theme simply will not persist */
    }
  }, [])

  useEffect(() => {
    // Follow the operating system while the choice is "system".
    let media = null
    try {
      media = window.matchMedia('(prefers-color-scheme: dark)')
    } catch {
      media = null
    }
    if (!media) return undefined

    const onChange = () => {
      setThemeState((current) => {
        if (current !== 'system') return current
        const next = applyTheme('system')
        setResolved(next)
        return current
      })
    }

    if (typeof media.addEventListener === 'function') {
      media.addEventListener('change', onChange)
      return () => media.removeEventListener('change', onChange)
    }
    // Older WebKit.
    media.addListener(onChange)
    return () => media.removeListener(onChange)
  }, [])

  const value = useMemo(
    () => ({ theme, resolved, setTheme, choices: THEME_CHOICES }),
    [theme, resolved, setTheme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

/** The theme controller. */
export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) {
    // Components are also rendered in isolation by documentation and legacy
    // tests. Keep the controls safe there; the application always supplies
    // the provider.
    return { theme: 'system', resolved: 'light', setTheme: (next) => applyTheme(next), choices: THEME_CHOICES }
  }
  return context
}
