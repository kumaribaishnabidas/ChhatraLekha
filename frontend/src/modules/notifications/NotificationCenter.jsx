import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useNotifications } from './useNotifications'
import NotificationPreferences from './NotificationPreferences'

const CATEGORY_TABS = [
  { id: 'ALL', label: 'All Notifications' },
  { id: 'UNREAD', label: 'Unread' },
  { id: 'ACADEMIC', label: 'Academic' },
  { id: 'ATTENDANCE', label: 'Attendance' },
  { id: 'ASSIGNMENTS', label: 'Assignments' },
  { id: 'EXAMINATIONS', label: 'Examinations' },
  { id: 'SECURITY', label: 'Security' },
  { id: 'PREFERENCES', label: 'Preferences' },
]

export default function NotificationCenter() {
  const {
    notifications,
    unreadCount,
    markAsRead,
    markAllRead,
    deleteNotification,
    preferences,
    updatePreferences,
  } = useNotifications()

  const [activeTab, setActiveTab] = useState('ALL')
  const [searchTerm, setSearchTerm] = useState('')

  const filtered = useMemo(() => {
    return notifications.filter((n) => {
      // Category filter
      if (activeTab === 'UNREAD' && n.is_read) return false
      if (activeTab !== 'ALL' && activeTab !== 'UNREAD' && activeTab !== 'PREFERENCES') {
        if (n.category !== activeTab) return false
      }
      // Search term
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase()
        return (
          n.title?.toLowerCase().includes(query) ||
          n.message?.toLowerCase().includes(query) ||
          n.category?.toLowerCase().includes(query)
        )
      }
      return true
    })
  }, [notifications, activeTab, searchTerm])

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
          {unreadCount > 0 && activeTab !== 'PREFERENCES' && (
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

      {/* Tabs */}
      <div className="flex items-center gap-1.5 border-b border-line pb-2 overflow-x-auto">
        {CATEGORY_TABS.map((tab) => {
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer whitespace-nowrap transition-colors ${
                isActive
                  ? 'bg-brand text-on-brand shadow-xs'
                  : 'bg-surface text-ink border border-line hover:border-brand'
              }`}
            >
              {tab.label}
              {tab.id === 'UNREAD' && unreadCount > 0 && (
                <span className={`ml-1.5 rounded-full px-1.5 py-0.2 text-[10px] font-bold ${
                  isActive ? 'bg-white text-brand' : 'bg-accent text-on-accent'
                }`}>
                  {unreadCount}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* View Content */}
      {activeTab === 'PREFERENCES' ? (
        <NotificationPreferences
          preferences={preferences}
          onSave={updatePreferences}
        />
      ) : (
        <div className="space-y-4">
          {/* Search bar */}
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Search notifications..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full sm:w-72 px-3 py-1.5 rounded-lg border border-line bg-surface text-xs text-ink placeholder:text-muted focus:outline-hidden focus:border-brand"
            />
          </div>

          {filtered.length === 0 ? (
            <div className="p-8 text-center rounded-lg bg-surface border border-line text-muted">
              <p className="m-0 text-sm font-semibold text-ink">No notifications found.</p>
              <p className="m-0 text-xs mt-1">You are all caught up with institutional updates.</p>
            </div>
          ) : (
            <div className="space-y-2.5">
              {filtered.map((item) => (
                <div
                  key={item.notification_id || item.id}
                  className={`p-4 rounded-lg border transition-all ${
                    item.is_read
                      ? 'bg-surface border-line'
                      : 'bg-surface-2 border-brand/40 shadow-xs'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="rounded bg-accent/15 text-accent-strong border border-accent/30 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider">
                          {item.category}
                        </span>
                        {item.priority === 'URGENT' && (
                          <span className="rounded bg-danger/15 text-danger border border-danger/30 px-1.5 py-0.5 text-[10px] font-bold uppercase">
                            URGENT
                          </span>
                        )}
                        <span className="text-[11px] text-muted">
                          {new Date(item.created_at).toLocaleDateString()}
                        </span>
                      </div>

                      <h2 className="m-0 text-sm font-bold text-ink">{item.title}</h2>
                      <p className="m-0 text-xs text-muted mt-1 leading-relaxed">{item.message}</p>

                      {item.deep_link && (
                        <div className="mt-2.5">
                          <Link
                            to={item.deep_link}
                            className="inline-flex items-center gap-1 text-xs font-semibold text-brand hover:underline no-underline"
                          >
                            <span>Open in portal</span>
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                            </svg>
                          </Link>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      {!item.is_read && (
                        <button
                          type="button"
                          onClick={() => markAsRead(item.notification_id || item.id)}
                          className="px-2 py-1 rounded border border-line bg-surface text-[11px] font-semibold text-ink hover:bg-surface-2 cursor-pointer shadow-xs"
                          title="Mark as read"
                        >
                          Mark read
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => deleteNotification(item.notification_id || item.id)}
                        className="p-1 rounded text-muted hover:text-danger hover:bg-danger/10 cursor-pointer border-0"
                        title="Dismiss notification"
                        aria-label="Dismiss notification"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
