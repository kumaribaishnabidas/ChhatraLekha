import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useNotifications } from './useNotifications'
import NotificationPreferences from './NotificationPreferences'

const CATEGORY_TABS = [
  { id: 'ALL', label: 'All' },
  { id: 'UNREAD', label: 'Unread' },
  { id: 'ACADEMIC', label: 'Academic' },
  { id: 'ATTENDANCE', label: 'Attendance' },
  { id: 'ASSIGNMENTS', label: 'Assignments' },
  { id: 'EXAMINATIONS', label: 'Examinations' },
  { id: 'RESULTS', label: 'Results' },
  { id: 'TIMETABLE', label: 'Timetable' },
  { id: 'ANNOUNCEMENTS', label: 'Notices' },
  { id: 'ADMISSIONS', label: 'Admissions' },
  { id: 'ADMINISTRATIVE', label: 'Admin' },
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
    loading,
  } = useNotifications()

  const [activeTab, setActiveTab] = useState('ALL')
  const [readFilter, setReadFilter] = useState('ALL') // 'ALL', 'UNREAD', 'READ'
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedNotification, setSelectedNotification] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 8

  // Filter items based on activeTab, readFilter, and search query
  const filtered = useMemo(() => {
    return notifications.filter((n) => {
      // Tab filter
      if (activeTab === 'UNREAD') {
        if (n.is_read) return false
      } else if (activeTab !== 'ALL' && activeTab !== 'PREFERENCES') {
        if (n.category !== activeTab) return false
      }

      // Read status filter
      if (readFilter === 'UNREAD' && n.is_read) return false
      if (readFilter === 'READ' && !n.is_read) return false

      // Search term
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase()
        const titleMatch = n.title?.toLowerCase().includes(query)
        const msgMatch = n.message?.toLowerCase().includes(query)
        const catMatch = n.category?.toLowerCase().includes(query)
        if (!titleMatch && !msgMatch && !catMatch) return false
      }

      return true
    })
  }, [notifications, activeTab, readFilter, searchTerm])

  // Pagination calculation
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
  const paginatedItems = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    return filtered.slice(start, start + pageSize)
  }, [filtered, currentPage, pageSize])

  const handleTabChange = (tabId) => {
    setActiveTab(tabId)
    setCurrentPage(1)
  }

  const getPriorityBadge = (priority) => {
    const p = (priority || 'NORMAL').toUpperCase()
    if (p === 'URGENT') {
      return (
        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-accent text-on-accent">
          Urgent
        </span>
      )
    }
    if (p === 'HIGH') {
      return (
        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-surface-2 border border-brand text-brand">
          High
        </span>
      )
    }
    return (
      <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-surface-2 text-muted">
        Normal
      </span>
    )
  }

  const getCategoryColor = (category) => {
    switch (category) {
      case 'SECURITY':
        return 'text-accent border-accent/30 bg-surface-2'
      case 'ATTENDANCE':
        return 'text-brand border-brand/30 bg-surface-2'
      case 'EXAMINATIONS':
      case 'RESULTS':
        return 'text-ink border-line bg-surface-2 font-semibold'
      default:
        return 'text-muted border-line bg-surface-2'
    }
  }

  const formatTimestamp = (isoStr) => {
    if (!isoStr) return ''
    try {
      const date = new Date(isoStr)
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return isoStr
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="m-0 text-xl font-bold text-ink">Notification Centre</h1>
            {unreadCount > 0 && (
              <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-accent text-on-accent">
                {unreadCount} unread
              </span>
            )}
          </div>
          <p className="m-0 text-xs text-muted mt-1">
            Centralized academic updates, attendance warnings, and institutional notices.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {unreadCount > 0 && activeTab !== 'PREFERENCES' && (
            <button
              type="button"
              onClick={markAllRead}
              className="px-3 py-1.5 rounded-lg bg-surface border border-line text-xs font-semibold text-ink hover:bg-surface-2 cursor-pointer shadow-xs transition-colors"
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
              onClick={() => handleTabChange(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer whitespace-nowrap transition-colors ${
                isActive
                  ? 'bg-brand text-on-brand shadow-xs'
                  : 'bg-surface text-ink border border-line hover:border-brand'
              }`}
            >
              {tab.label}
              {tab.id === 'UNREAD' && unreadCount > 0 && (
                <span
                  className={`ml-1.5 rounded-full px-1.5 py-0.2 text-[10px] font-bold ${
                    isActive ? 'bg-white text-brand' : 'bg-accent text-on-accent'
                  }`}
                >
                  {unreadCount}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* View: Preferences Tab */}
      {activeTab === 'PREFERENCES' ? (
        <NotificationPreferences
          preferences={preferences}
          onSave={updatePreferences}
        />
      ) : (
        /* View: Notifications List */
        <div className="space-y-4">
          {/* Controls: Search and Status filter */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
            <div className="relative flex-1 max-w-md">
              <input
                type="text"
                placeholder="Search notifications by title, content or keyword..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value)
                  setCurrentPage(1)
                }}
                className="w-full text-xs px-3 py-2 pl-9 rounded-lg border border-line bg-surface text-ink placeholder:text-muted focus:border-brand focus:outline-hidden"
              />
              <svg
                className="w-4 h-4 text-muted absolute left-2.5 top-2.5 pointer-events-none"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-muted font-medium">Status:</span>
              <select
                value={readFilter}
                onChange={(e) => {
                  setReadFilter(e.target.value)
                  setCurrentPage(1)
                }}
                className="text-xs font-semibold px-2.5 py-1.5 rounded-lg border border-line bg-surface text-ink cursor-pointer focus:border-brand focus:outline-hidden"
              >
                <option value="ALL">All Status</option>
                <option value="UNREAD">Unread Only</option>
                <option value="READ">Read Only</option>
              </select>
            </div>
          </div>

          {/* Loading state */}
          {loading && (
            <div className="p-8 text-center text-xs text-muted">
              Loading notification records...
            </div>
          )}

          {/* Empty state */}
          {!loading && paginatedItems.length === 0 && (
            <div className="p-8 rounded-lg border border-dashed border-line text-center bg-surface space-y-2">
              <div className="inline-flex p-3 rounded-full bg-surface-2 text-muted">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
              <h3 className="m-0 text-sm font-semibold text-ink">No notifications found</h3>
              <p className="m-0 text-xs text-muted max-w-sm mx-auto">
                {searchTerm
                  ? 'No notifications match your search query. Try adjusting your search term.'
                  : 'You are all caught up. New announcements and alerts will appear here.'}
              </p>
            </div>
          )}

          {/* Items List */}
          {!loading && paginatedItems.length > 0 && (
            <div className="space-y-2.5">
              {paginatedItems.map((n) => {
                const isUnread = !n.is_read
                return (
                  <div
                    key={n.notification_id}
                    onClick={() => setSelectedNotification(n)}
                    className={`p-3.5 sm:p-4 rounded-lg border transition-all cursor-pointer ${
                      isUnread
                        ? 'bg-surface border-brand shadow-xs'
                        : 'bg-surface/70 border-line hover:border-brand/40'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3 min-w-0 flex-1">
                        {/* Unread indicator */}
                        <div className="pt-1 shrink-0">
                          <span
                            className={`block w-2.5 h-2.5 rounded-full ${
                              isUnread ? 'bg-brand' : 'bg-line'
                            }`}
                          />
                        </div>

                        <div className="min-w-0 flex-1 space-y-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span
                              className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${getCategoryColor(
                                n.category
                              )}`}
                            >
                              {n.category}
                            </span>
                            {getPriorityBadge(n.priority)}
                            <span className="text-[11px] text-muted font-mono">
                              {formatTimestamp(n.created_at)}
                            </span>
                          </div>

                          <h3 className={`m-0 text-xs sm:text-sm font-semibold text-ink line-clamp-1 ${
                            isUnread ? 'font-bold' : 'font-medium'
                          }`}>
                            {n.title}
                          </h3>

                          <p className="m-0 text-xs text-muted line-clamp-2 leading-relaxed">
                            {n.message}
                          </p>

                          {n.channels && n.channels.length > 0 && (
                            <div className="flex items-center gap-1.5 pt-1">
                              {n.channels.map((ch) => (
                                <span
                                  key={ch}
                                  className="text-[9px] px-1.5 py-0.2 rounded bg-surface-2 text-muted border border-line"
                                >
                                  {ch}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Action buttons */}
                      <div
                        className="flex items-center gap-1 shrink-0 pt-0.5"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {isUnread && (
                          <button
                            type="button"
                            onClick={() => markAsRead(n.notification_id)}
                            title="Mark as read"
                            className="p-1.5 rounded-md hover:bg-surface-2 text-muted hover:text-ink cursor-pointer"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                            </svg>
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => deleteNotification(n.notification_id)}
                          title="Dismiss notification"
                          className="p-1.5 rounded-md hover:bg-surface-2 text-muted hover:text-accent cursor-pointer"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* Pagination bar */}
          {!loading && totalPages > 1 && (
            <div className="flex items-center justify-between pt-3 border-t border-line text-xs">
              <span className="text-muted">
                Showing {paginatedItems.length} of {filtered.length} notifications
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={currentPage <= 1}
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  className="px-2.5 py-1 rounded-lg border border-line bg-surface text-ink disabled:opacity-40 disabled:cursor-not-allowed hover:bg-surface-2 cursor-pointer"
                >
                  Previous
                </button>
                <span className="font-semibold text-ink">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  type="button"
                  disabled={currentPage >= totalPages}
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  className="px-2.5 py-1 rounded-lg border border-line bg-surface text-ink disabled:opacity-40 disabled:cursor-not-allowed hover:bg-surface-2 cursor-pointer"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Notification Details Modal */}
      {selectedNotification && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40"
          onClick={() => setSelectedNotification(null)}
        >
          <div
            className="w-full max-w-lg rounded-lg bg-surface border border-line shadow-md p-6 space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${getCategoryColor(
                      selectedNotification.category
                    )}`}
                  >
                    {selectedNotification.category}
                  </span>
                  {getPriorityBadge(selectedNotification.priority)}
                </div>
                <h3 className="m-0 text-base font-bold text-ink">
                  {selectedNotification.title}
                </h3>
                <span className="text-xs text-muted font-mono block">
                  {formatTimestamp(selectedNotification.created_at)}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setSelectedNotification(null)}
                className="p-1 rounded-md text-muted hover:text-ink cursor-pointer"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-3.5 rounded-lg bg-surface-2 text-xs text-ink leading-relaxed">
              {selectedNotification.message}
            </div>

            {selectedNotification.deep_link && (
              <div className="pt-1">
                <Link
                  to={selectedNotification.deep_link}
                  onClick={() => setSelectedNotification(null)}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand hover:underline"
                >
                  <span>Open associated workflow</span>
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </Link>
              </div>
            )}

            <div className="flex items-center justify-between pt-3 border-t border-line text-xs">
              <button
                type="button"
                onClick={() => {
                  deleteNotification(selectedNotification.notification_id)
                  setSelectedNotification(null)
                }}
                className="px-3 py-1.5 rounded-lg border border-line text-accent hover:bg-surface-2 font-medium cursor-pointer"
              >
                Dismiss Notice
              </button>

              <div className="flex items-center gap-2">
                {!selectedNotification.is_read && (
                  <button
                    type="button"
                    onClick={() => {
                      markAsRead(selectedNotification.notification_id)
                      setSelectedNotification({ ...selectedNotification, is_read: true })
                    }}
                    className="px-3 py-1.5 rounded-lg bg-surface border border-line text-ink font-semibold hover:bg-surface-2 cursor-pointer shadow-xs"
                  >
                    Mark as Read
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setSelectedNotification(null)}
                  className="px-3 py-1.5 rounded-lg bg-brand text-on-brand font-semibold hover:opacity-90 cursor-pointer shadow-xs"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
