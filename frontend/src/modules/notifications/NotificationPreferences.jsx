import { useState, useEffect } from 'react'

const CATEGORIES = [
  { id: 'ACADEMIC', label: 'Academic Announcements' },
  { id: 'ATTENDANCE', label: 'Attendance Alerts & Monthly Summaries' },
  { id: 'ASSIGNMENTS', label: 'Assignments & Coursework Submissions' },
  { id: 'EXAMINATIONS', label: 'Examinations, Schedules & Results' },
  { id: 'ANNOUNCEMENTS', label: 'General Institutional Notices' },
  { id: 'SECURITY', label: 'Account Security & Session Warnings' },
]

export default function NotificationPreferences({
  preferences,
  onSave,
}) {
  const [inApp, setInApp] = useState(true)
  const [email, setEmail] = useState(true)
  const [push, setPush] = useState(true)
  const [quietHours, setQuietHours] = useState(false)
  const [quietStart, setQuietStart] = useState('22:00')
  const [quietEnd, setQuietEnd] = useState('07:00')
  const [selectedCategories, setSelectedCategories] = useState(CATEGORIES.map((c) => c.id))
  const [savedMessage, setSavedMessage] = useState(false)

  useEffect(() => {
    if (preferences) {
      setInApp(preferences.in_app_enabled ?? true)
      setEmail(preferences.email_enabled ?? true)
      setPush(preferences.push_enabled ?? true)
      setQuietHours(preferences.quiet_hours_enabled ?? false)
      setQuietStart(preferences.quiet_hours_start || '22:00')
      setQuietEnd(preferences.quiet_hours_end || '07:00')
      if (preferences.subscribed_categories) {
        setSelectedCategories(preferences.subscribed_categories)
      }
    }
  }, [preferences])

  const toggleCategory = (id) => {
    setSelectedCategories((prev) =>
      prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]
    )
  }

  const handleSave = async (e) => {
    e.preventDefault()
    if (onSave) {
      await onSave({
        in_app_enabled: inApp,
        email_enabled: email,
        push_enabled: push,
        quiet_hours_enabled: quietHours,
        quiet_hours_start: quietStart,
        quiet_hours_end: quietEnd,
        subscribed_categories: selectedCategories,
      })
      setSavedMessage(true)
      setTimeout(() => setSavedMessage(false), 3000)
    }
  }

  return (
    <form onSubmit={handleSave} className="space-y-6">
      {savedMessage && (
        <div className="p-3 rounded-lg bg-surface-2 border border-brand text-brand font-medium text-xs">
          Notification preferences successfully updated.
        </div>
      )}

      {/* Channels */}
      <div className="p-4 rounded-lg bg-surface border border-line space-y-3">
        <h3 className="m-0 text-sm font-bold text-ink">Delivery Channels</h3>
        <p className="m-0 text-xs text-muted">
          Choose where you receive notifications. Critical security alerts are always delivered.
        </p>
        <div className="space-y-2 pt-2">
          <label className="flex items-center gap-3 cursor-pointer text-xs text-ink font-medium">
            <input
              type="checkbox"
              checked={inApp}
              onChange={(e) => setInApp(e.target.checked)}
              className="rounded border-line text-brand"
            />
            <span>In-App Notification Centre</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer text-xs text-ink font-medium">
            <input
              type="checkbox"
              checked={email}
              onChange={(e) => setEmail(e.target.checked)}
              className="rounded border-line text-brand"
            />
            <span>Email Delivery (Daily digests & important alerts)</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer text-xs text-ink font-medium">
            <input
              type="checkbox"
              checked={push}
              onChange={(e) => setPush(e.target.checked)}
              className="rounded border-line text-brand"
            />
            <span>Mobile Push Notifications (Android & iOS)</span>
          </label>
        </div>
      </div>

      {/* Quiet Hours */}
      <div className="p-4 rounded-lg bg-surface border border-line space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="m-0 text-sm font-bold text-ink">Quiet Hours</h3>
            <p className="m-0 text-xs text-muted">
              Mute non-urgent push notifications and emails during night hours.
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={quietHours}
              onChange={(e) => setQuietHours(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-9 h-5 bg-line peer-focus:outline-hidden rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-line after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-brand" />
          </label>
        </div>

        {quietHours && (
          <div className="grid grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-semibold text-muted mb-1">Start Time</label>
              <input
                type="time"
                value={quietStart}
                onChange={(e) => setQuietStart(e.target.value)}
                className="w-full px-3 py-1.5 rounded border border-line bg-surface text-ink text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-muted mb-1">End Time</label>
              <input
                type="time"
                value={quietEnd}
                onChange={(e) => setQuietEnd(e.target.value)}
                className="w-full px-3 py-1.5 rounded border border-line bg-surface text-ink text-xs"
              />
            </div>
          </div>
        )}
      </div>

      {/* Categories */}
      <div className="p-4 rounded-lg bg-surface border border-line space-y-3">
        <h3 className="m-0 text-sm font-bold text-ink">Subscribed Topics</h3>
        <p className="m-0 text-xs text-muted">Select which notification categories you want to follow.</p>
        <div className="space-y-2 pt-2">
          {CATEGORIES.map((c) => (
            <label key={c.id} className="flex items-center gap-3 cursor-pointer text-xs text-ink font-medium">
              <input
                type="checkbox"
                checked={selectedCategories.includes(c.id)}
                onChange={() => toggleCategory(c.id)}
                className="rounded border-line text-brand"
              />
              <span>{c.label}</span>
            </label>
          ))}
        </div>
      </div>

      <button
        type="submit"
        className="px-4 py-2 rounded-lg bg-brand text-on-brand font-bold text-xs hover:bg-brand-deep cursor-pointer transition-colors shadow-xs"
      >
        Save Preferences
      </button>
    </form>
  )
}
