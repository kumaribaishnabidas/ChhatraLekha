import { useState, useEffect } from 'react'

const NOTIFICATION_CATEGORIES = [
  { id: 'ACADEMIC', label: 'Academic Announcements & Circulars', desc: 'Curriculum updates and official notices' },
  { id: 'ATTENDANCE', label: 'Attendance Alerts & Threshold Notices', desc: 'Daily attendance logs and warning thresholds' },
  { id: 'ASSIGNMENTS', label: 'Assignments & Coursework Submissions', desc: 'New problem sets, project prompts, and deadlines' },
  { id: 'EXAMINATIONS', label: 'Examinations & Hall Ticket Schedules', desc: 'Mid-term and end-term exam dates and seatings' },
  { id: 'RESULTS', label: 'Semester Results & Digital Grade Cards', desc: 'Official marks publication and grade updates' },
  { id: 'TIMETABLE', label: 'Timetable & Class Rescheduling', desc: 'Room relocations, timing changes, and lab schedules' },
  { id: 'ANNOUNCEMENTS', label: 'General Institutional Notices', desc: 'Campus events, library access, and holiday alerts' },
  { id: 'ADMISSIONS', label: 'Admissions & Enrollment Updates', desc: 'Elective registrations and semester intake notices' },
  { id: 'ADMINISTRATIVE', label: 'Administrative & Fee Reminders', desc: 'Tuition clearance and documentation reminders' },
  { id: 'SECURITY', label: 'Account Security & Session Warnings', desc: 'New sign-ins, password changes, and 2FA alerts', required: true },
]

const LANGUAGE_OPTIONS = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'Hindi (हिंदी)' },
  { code: 'bn', label: 'Bengali (বাংলা)' },
  { code: 'te', label: 'Telugu (తెలుగు)' },
  { code: 'ta', label: 'Tamil (தமிழ்)' },
  { code: 'mr', label: 'Marathi (मराठी)' },
  { code: 'gu', label: 'Gujarati (ગુજરાતી)' },
  { code: 'kn', label: 'Kannada (ಕನ್ನಡ)' },
  { code: 'ml', label: 'Malayalam (മലയാളം)' },
  { code: 'or', label: 'Odia (ଓଡ଼ିଆ)' },
  { code: 'pa', label: 'Punjabi (ਪੰਜਾਬੀ)' },
  { code: 'as', label: 'Assamese (অসমীয়া)' },
  { code: 'ur', label: 'Urdu (اردو)' },
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
  const [languagePreference, setLanguagePreference] = useState('en')
  const [selectedCategories, setSelectedCategories] = useState(
    NOTIFICATION_CATEGORIES.map((c) => c.id)
  )
  const [savedMessage, setSavedMessage] = useState(false)

  useEffect(() => {
    if (preferences) {
      setInApp(preferences.in_app_enabled ?? true)
      setEmail(preferences.email_enabled ?? true)
      setPush(preferences.push_enabled ?? true)
      setQuietHours(preferences.quiet_hours_enabled ?? false)
      setQuietStart(preferences.quiet_hours_start || '22:00')
      setQuietEnd(preferences.quiet_hours_end || '07:00')
      setLanguagePreference(preferences.language_preference || 'en')
      if (preferences.subscribed_categories) {
        // Ensure SECURITY is present
        const cats = preferences.subscribed_categories.includes('SECURITY')
          ? preferences.subscribed_categories
          : [...preferences.subscribed_categories, 'SECURITY']
        setSelectedCategories(cats)
      }
    }
  }, [preferences])

  const toggleCategory = (id) => {
    if (id === 'SECURITY') {
      return // Non-disableable
    }
    setSelectedCategories((prev) =>
      prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]
    )
  }

  const handleSave = async (e) => {
    e.preventDefault()
    if (onSave) {
      const payload = {
        in_app_enabled: inApp,
        email_enabled: email,
        push_enabled: push,
        quiet_hours_enabled: quietHours,
        quiet_hours_start: quietStart,
        quiet_hours_end: quietEnd,
        language_preference: languagePreference,
        // Always include SECURITY
        subscribed_categories: selectedCategories.includes('SECURITY')
          ? selectedCategories
          : [...selectedCategories, 'SECURITY'],
      }
      await onSave(payload)
      setSavedMessage(true)
      setTimeout(() => setSavedMessage(false), 3000)
    }
  }

  return (
    <form onSubmit={handleSave} className="space-y-6">
      {savedMessage && (
        <div className="p-3 rounded-lg bg-surface-2 border border-brand text-brand font-medium text-xs flex items-center gap-2">
          <svg className="w-4 h-4 text-brand shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
          </svg>
          Notification preferences successfully updated.
        </div>
      )}

      {/* Delivery Channels */}
      <div className="p-4 rounded-lg bg-surface border border-line space-y-3">
        <h3 className="m-0 text-sm font-bold text-ink">Delivery Channels</h3>
        <p className="m-0 text-xs text-muted">
          Select communication channels for alerts. Essential security warnings are always delivered.
        </p>
        <div className="space-y-2 pt-2">
          <label className="flex items-center gap-3 cursor-pointer text-xs text-ink font-medium">
            <input
              type="checkbox"
              checked={inApp}
              onChange={(e) => setInApp(e.target.checked)}
              className="rounded border-line text-brand"
            />
            <span>In-App Notification Centre (Real-time bell and dashboard feed)</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer text-xs text-ink font-medium">
            <input
              type="checkbox"
              checked={email}
              onChange={(e) => setEmail(e.target.checked)}
              className="rounded border-line text-brand"
            />
            <span>Email Delivery (Daily digests, academic circulars, and grade alerts)</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer text-xs text-ink font-medium">
            <input
              type="checkbox"
              checked={push}
              onChange={(e) => setPush(e.target.checked)}
              className="rounded border-line text-brand"
            />
            <span>Mobile Push Notifications (Android FCM and iOS APNs)</span>
          </label>
        </div>
      </div>

      {/* Multilingual Notification Preference */}
      <div className="p-4 rounded-lg bg-surface border border-line space-y-3">
        <h3 className="m-0 text-sm font-bold text-ink">Language & Regional Preferences</h3>
        <p className="m-0 text-xs text-muted">
          Choose the preferred language for email notifications and push notification summaries.
        </p>
        <div className="pt-1 max-w-xs">
          <select
            value={languagePreference}
            onChange={(e) => setLanguagePreference(e.target.value)}
            className="w-full text-xs font-medium px-3 py-2 rounded-lg bg-surface border border-line text-ink focus:border-brand focus:outline-hidden"
          >
            {LANGUAGE_OPTIONS.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Category Subscriptions */}
      <div className="p-4 rounded-lg bg-surface border border-line space-y-3">
        <h3 className="m-0 text-sm font-bold text-ink">Subscribed Categories</h3>
        <p className="m-0 text-xs text-muted">
          Select notification categories to receive. Account security notices cannot be disabled.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-2">
          {NOTIFICATION_CATEGORIES.map((cat) => {
            const isChecked = selectedCategories.includes(cat.id)
            const isRequired = cat.required
            return (
              <label
                key={cat.id}
                className={`flex items-start gap-3 p-2.5 rounded-lg border text-xs font-medium transition-colors ${
                  isRequired
                    ? 'bg-surface-2 border-line cursor-not-allowed opacity-90'
                    : 'bg-surface border-line hover:border-brand cursor-pointer'
                }`}
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  disabled={isRequired}
                  onChange={() => toggleCategory(cat.id)}
                  className="rounded border-line text-brand mt-0.5"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-ink font-semibold">{cat.label}</span>
                    {isRequired && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-brand text-on-brand font-semibold">
                        Required
                      </span>
                    )}
                  </div>
                  <p className="m-0 text-[11px] text-muted mt-0.5">{cat.desc}</p>
                </div>
              </label>
            )
          })}
        </div>
      </div>

      {/* Quiet Hours */}
      <div className="p-4 rounded-lg bg-surface border border-line space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="m-0 text-sm font-bold text-ink">Quiet Hours</h3>
            <p className="m-0 text-xs text-muted mt-0.5">
              Silence non-urgent push and email notifications during designated study or resting hours.
            </p>
          </div>
          <input
            type="checkbox"
            checked={quietHours}
            onChange={(e) => setQuietHours(e.target.checked)}
            className="rounded border-line text-brand h-4 w-4 cursor-pointer"
          />
        </div>

        {quietHours && (
          <div className="flex items-center gap-4 pt-2 border-t border-line text-xs">
            <div>
              <label className="block text-muted mb-1 font-medium">Starts At</label>
              <input
                type="time"
                value={quietStart}
                onChange={(e) => setQuietStart(e.target.value)}
                className="px-2.5 py-1.5 rounded-lg border border-line bg-surface text-ink font-mono text-xs"
              />
            </div>
            <div>
              <label className="block text-muted mb-1 font-medium">Ends At</label>
              <input
                type="time"
                value={quietEnd}
                onChange={(e) => setQuietEnd(e.target.value)}
                className="px-2.5 py-1.5 rounded-lg border border-line bg-surface text-ink font-mono text-xs"
              />
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-end">
        <button
          type="submit"
          className="px-4 py-2 rounded-lg bg-brand text-on-brand font-semibold text-xs shadow-xs hover:opacity-90 cursor-pointer"
        >
          Save Preferences
        </button>
      </div>
    </form>
  )
}
