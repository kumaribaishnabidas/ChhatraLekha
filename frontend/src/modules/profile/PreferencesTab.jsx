import { useState, useEffect } from 'react'

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी (Hindi)' },
  { code: 'bn', label: 'বাংলা (Bengali)' },
  { code: 'te', label: 'తెలుగు (Telugu)' },
  { code: 'mr', label: 'मराठी (Marathi)' },
  { code: 'ta', label: 'தமிழ் (Tamil)' },
  { code: 'ur', label: 'اردو (Urdu)' },
  { code: 'gu', label: 'ગુજરાતી (Gujarati)' },
  { code: 'kn', label: 'ಕನ್ನಡ (Kannada)' },
  { code: 'ml', label: 'മലയാളം (Malayalam)' },
  { code: 'or', label: 'ଓଡ଼ିଆ (Odia)' },
  { code: 'pa', label: 'ਪੰਜਾਬੀ (Punjabi)' },
  { code: 'as', label: 'অসমীয়া (Assamese)' },
]

export default function PreferencesTab({
  preferences = {},
  onSave,
}) {
  const [language, setLanguage] = useState(preferences.preferred_language || 'en')
  const [theme, setTheme] = useState(preferences.theme || 'system')
  const [highContrast, setHighContrast] = useState(preferences.high_contrast || false)
  const [screenReader, setScreenReader] = useState(preferences.screen_reader_optimized || false)
  const [directoryVisible, setDirectoryVisible] = useState(preferences.directory_visible ?? true)
  const [saved, setSaved] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (preferences) {
      setLanguage(preferences.preferred_language || 'en')
      setTheme(preferences.theme || 'system')
      setHighContrast(preferences.high_contrast || false)
      setScreenReader(preferences.screen_reader_optimized || false)
      setDirectoryVisible(preferences.directory_visible ?? true)
    }
  }, [preferences])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsSubmitting(true)
    try {
      if (onSave) {
        await onSave({
          preferred_language: language,
          theme,
          high_contrast: highContrast,
          screen_reader_optimized: screenReader,
          directory_visible: directoryVisible,
        })
      }
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {saved && (
        <div className="p-3 rounded-lg bg-surface-2 border border-brand text-brand font-medium text-xs">
          Accessibility and language preferences successfully saved.
        </div>
      )}

      {/* Language */}
      <div className="p-4 rounded-lg bg-surface border border-line space-y-3">
        <h3 className="m-0 text-sm font-bold text-ink">Language & Regional Interface</h3>
        <p className="m-0 text-xs text-muted">
          Choose your default language for portal labels, notices, and voice assistance.
        </p>
        <div className="w-full sm:w-72">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-line bg-surface text-ink text-xs font-medium cursor-pointer"
          >
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Theme */}
      <div className="p-4 rounded-lg bg-surface border border-line space-y-3">
        <h3 className="m-0 text-sm font-bold text-ink">Display Theme</h3>
        <p className="m-0 text-xs text-muted">
          Adjust the visual theme across daytime and low-light environments.
        </p>
        <div className="flex gap-2">
          {['light', 'dark', 'system'].map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setTheme(m)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize cursor-pointer transition-colors ${
                theme === m
                  ? 'bg-brand text-on-brand shadow-xs'
                  : 'bg-surface text-ink border border-line hover:border-brand'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {/* Accessibility & Privacy */}
      <div className="p-4 rounded-lg bg-surface border border-line space-y-3">
        <h3 className="m-0 text-sm font-bold text-ink">Accessibility & Directory Visibility</h3>
        <div className="space-y-2 pt-1">
          <label className="flex items-center gap-3 cursor-pointer text-xs text-ink font-medium">
            <input
              type="checkbox"
              checked={highContrast}
              onChange={(e) => setHighContrast(e.target.checked)}
              className="rounded border-line text-brand"
            />
            <span>High Contrast Interface (WCAG AAA compliant borders and text)</span>
          </label>

          <label className="flex items-center gap-3 cursor-pointer text-xs text-ink font-medium">
            <input
              type="checkbox"
              checked={screenReader}
              onChange={(e) => setScreenReader(e.target.checked)}
              className="rounded border-line text-brand"
            />
            <span>Screen Reader Optimizations (Expanded ARIA live regions and descriptions)</span>
          </label>

          <label className="flex items-center gap-3 cursor-pointer text-xs text-ink font-medium">
            <input
              type="checkbox"
              checked={directoryVisible}
              onChange={(e) => setDirectoryVisible(e.target.checked)}
              className="rounded border-line text-brand"
            />
            <span>Campus Directory Visibility (Display profile in verified institutional student register)</span>
          </label>
        </div>
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="px-4 py-2 rounded-lg bg-brand text-on-brand font-bold text-xs hover:bg-brand-deep cursor-pointer transition-colors shadow-xs"
      >
        {isSubmitting ? 'Saving...' : 'Save Preferences'}
      </button>
    </form>
  )
}

