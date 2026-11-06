import { useState } from 'react'
import { Link } from 'react-router-dom'

const SAMPLE_NOTIFICATIONS = [
  {
    id: 'ntf-01',
    category: 'ATTENDANCE',
    title: 'Monthly Attendance Summary (October 2024)',
    message: 'Your overall attendance for October 2024 is recorded at 94.2%. Keep up the good work.',
    created_at: '2024-11-01T09:30:00Z',
    is_read: false,
    deep_link: '/me',
  },
  {
    id: 'ntf-02',
    category: 'ASSIGNMENTS',
    title: 'New Assignment: Database Relational Normalization',
    message: 'Prof. Rajesh Kumar posted Problem Set 4 for Database Systems. Due on Friday, 15 November.',
    created_at: '2024-10-30T14:15:00Z',
    is_read: false,
    deep_link: '/me',
  },
  {
    id: 'ntf-03',
    category: 'EXAMINATIONS',
    title: 'Mid-Term Examination Schedule Released',
    message: 'The examination timetable for 5th Semester B.Tech has been published by the academic office.',
    created_at: '2024-10-28T11:00:00Z',
    is_read: true,
    deep_link: '/me/results',
  },
  {
    id: 'ntf-04',
    category: 'ANNOUNCEMENTS',
    title: 'National Digital Library of India Access Enabled',
    message: 'Students and faculty can now access NDLI digital repositories using single sign-on.',
    created_at: '2024-10-25T16:45:00Z',
    is_read: true,
    deep_link: '/announcements',
  },
  {
    id: 'ntf-05',
    category: 'SECURITY',
    title: 'New Web Session Authenticated',
    message: 'Your ChhatraLekha account was signed into from a new browser session (IP: 103.21.244.18).',
    created_at: '2024-10-24T08:20:00Z',
    is_read: true,
    deep_link: '/profile',
  },
]

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState(SAMPLE_NOTIFICATIONS)
  const [activeCategory, setActiveCategory] = useState('ALL')

  const unreadCount = notifications.filter((n) => !n.is_read).length

  const filteredNotifications = notifications.filter((n) => {
    if (activeCategory === 'ALL') return true
    if (activeCategory === 'UNREAD') return !n.is_read
    return n.category === activeCategory
  })

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
  }

  const toggleRead = (id) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: !n.is_read } : n))
    )
  }

  const deleteNotification = (id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="m-0 text-xl font-bold text-ink">Notification Centre</h1>
          <p className="m-0 text-xs text-muted mt-0.5">
            Centralized academic updates, attendance warnings, and institutional announcements.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <button
              type="button"
              onClick={markAllRead}
              className="px-3 py-1.5 rounded bg-surface border border-line text-xs font-semibold text-ink hover:bg-surface-2 cursor-pointer shadow-xs"
            >
              Mark all as read
            </button>
          )}
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex flex-wrap gap-1.5 border-b border-line pb-3 text-xs">
        {[
          { id: 'ALL', label: 'All Notifications' },
          { id: 'UNREAD', label: `Unread (${unreadCount})` },
          { id: 'ATTENDANCE', label: 'Attendance' },
          { id: 'ASSIGNMENTS', label: 'Assignments' },
          { id: 'EXAMINATIONS', label: 'Examinations' },
          { id: 'ANNOUNCEMENTS', label: 'Announcements' },
          { id: 'SECURITY', label: 'Security' },
        ].map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveCategory(tab.id)}
            className={`px-3 py-1.5 rounded font-semibold text-xs transition-colors cursor-pointer border-0 ${
              activeCategory === tab.id
                ? 'bg-brand text-white shadow-xs'
                : 'bg-surface-2 text-muted hover:text-ink hover:bg-surface'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Notification List */}
      <div className="space-y-3">
        {filteredNotifications.length === 0 ? (
          <div className="p-8 text-center rounded border border-line bg-surface text-muted text-xs">
            No notifications in this category.
          </div>
        ) : (
          filteredNotifications.map((item) => (
            <div
              key={item.id}
              className={`p-4 rounded-lg border transition-colors flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${
                item.is_read
                  ? 'bg-surface border-line text-ink'
                  : 'bg-blue-50/40 border-blue-200 text-ink'
              }`}
            >
              <div className="space-y-1 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-surface border border-line text-muted uppercase tracking-wider">
                    {item.category}
                  </span>
                  {!item.is_read && (
                    <span className="w-2 h-2 rounded-full bg-brand flex-shrink-0" title="Unread" />
                  )}
                  <span className="text-[11px] text-muted">
                    {new Date(item.created_at).toLocaleString()}
                  </span>
                </div>
                <h4 className="m-0 text-sm font-bold text-ink">{item.title}</h4>
                <p className="m-0 text-xs text-muted leading-relaxed">{item.message}</p>
              </div>

              <div className="flex items-center gap-2 flex-shrink-0 self-end sm:self-center">
                {item.deep_link && (
                  <Link
                    to={item.deep_link}
                    className="px-2.5 py-1 rounded bg-surface border border-line text-xs font-semibold text-brand hover:bg-surface-2 no-underline"
                  >
                    View Details
                  </Link>
                )}
                <button
                  type="button"
                  onClick={() => toggleRead(item.id)}
                  className="px-2.5 py-1 rounded bg-surface border border-line text-xs font-medium text-muted hover:text-ink cursor-pointer"
                >
                  {item.is_read ? 'Mark unread' : 'Mark read'}
                </button>
                <button
                  type="button"
                  onClick={() => deleteNotification(item.id)}
                  className="p-1 text-muted hover:text-red-700 cursor-pointer bg-transparent border-0"
                  title="Delete notification"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Preferences Reminder */}
      <div className="p-3.5 rounded border border-line bg-surface-2 text-xs text-muted flex items-center justify-between">
        <span>Looking to change notification channels, frequency, or quiet hours?</span>
        <Link to="/profile" className="text-brand font-semibold hover:underline no-underline">
          Go to Profile Settings
        </Link>
      </div>
    </div>
  )
}

