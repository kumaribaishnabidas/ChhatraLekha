import { useState, useRef, useEffect } from 'react'
import { NavLink } from 'react-router-dom'

export default function NotificationBell({
  unreadCount = 0,
  notifications = [],
  onMarkRead,
  onMarkAllRead,
}) {
  const [open, setOpen] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setOpen(false)
      }
    }
    if (open) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [open])

  const previewItems = notifications.slice(0, 3)

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="rounded border border-line bg-surface p-2 text-ink hover:bg-surface-2 cursor-pointer flex items-center justify-center relative shadow-xs"
        title="View Notifications"
        aria-label="Open notifications menu"
        aria-expanded={open}
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-accent text-on-accent text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center shadow-xs">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 rounded-lg bg-surface border border-line shadow-md p-3 z-50 text-left">
          <div className="flex items-center justify-between pb-2 border-b border-line mb-2">
            <span className="text-xs font-bold text-ink">Notifications</span>
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={() => {
                  onMarkAllRead?.()
                  setOpen(false)
                }}
                className="text-[11px] text-brand hover:underline cursor-pointer bg-transparent border-0 p-0"
              >
                Mark all read
              </button>
            )}
          </div>

          <div className="space-y-2 max-h-64 overflow-y-auto">
            {previewItems.length === 0 ? (
              <p className="m-0 text-xs text-muted text-center py-4">No notifications.</p>
            ) : (
              previewItems.map((n) => (
                <div
                  key={n.notification_id || n.id}
                  className={`p-2 rounded text-xs border ${
                    n.is_read ? 'bg-surface-2/40 border-line text-muted' : 'bg-surface-2 border-line text-ink font-medium'
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] mb-1">
                    <span className="font-bold uppercase tracking-wider text-accent">{n.category}</span>
                    <span className="text-muted">{new Date(n.created_at).toLocaleDateString()}</span>
                  </div>
                  <p className="m-0 font-semibold text-ink line-clamp-1">{n.title}</p>
                  <p className="m-0 text-[11px] text-muted line-clamp-2 mt-0.5">{n.message}</p>
                  {!n.is_read && (
                    <button
                      type="button"
                      onClick={() => onMarkRead?.(n.notification_id || n.id)}
                      className="mt-1 text-[10px] text-brand hover:underline cursor-pointer p-0 bg-transparent border-0"
                    >
                      Mark as read
                    </button>
                  )}
                </div>
              ))
            )}
          </div>

          <div className="border-t border-line pt-2 text-center mt-2">
            <NavLink
              to="/notifications"
              onClick={() => setOpen(false)}
              className="text-xs font-semibold text-brand hover:underline no-underline block"
            >
              Open Notification Centre
            </NavLink>
          </div>
        </div>
      )}
    </div>
  )
}
