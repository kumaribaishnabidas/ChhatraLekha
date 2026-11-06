import { Card } from '../common'
import { Link } from 'react-router-dom'

export default function NotificationPreviewWidget({
  title = 'Notifications & Announcements',
  subtitle,
  notifications = [],
  actionLabel = 'All Notifications',
  actionTo = '/notifications',
  emptyMessage = 'No active announcements or notifications.',
  className = '',
}) {
  return (
    <Card className={`p-5 flex flex-col justify-between ${className}`}>
      <div>
        <div className="flex items-center justify-between pb-3 border-b border-line">
          <div>
            <h3 className="m-0 text-base font-bold text-heading">{title}</h3>
            {subtitle && <p className="m-0 text-xs text-muted mt-0.5">{subtitle}</p>}
          </div>
          {actionTo && (
            <Link
              to={actionTo}
              className="text-xs font-semibold text-brand hover:underline no-underline"
            >
              {actionLabel}
            </Link>
          )}
        </div>

        <div className="mt-4 space-y-3">
          {notifications.length === 0 ? (
            <p className="m-0 text-xs text-muted py-4 text-center">{emptyMessage}</p>
          ) : (
            notifications.map((item, idx) => (
              <div
                key={item.id || idx}
                className={`p-3 rounded-lg border transition-colors ${
                  item.unread
                    ? 'border-brand/30 bg-brand-light/30'
                    : 'border-line bg-surface-2 hover:bg-surface'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    {item.unread && (
                      <span className="h-2 w-2 rounded-full bg-brand shrink-0" aria-label="Unread" />
                    )}
                    <h4 className="m-0 text-xs font-bold text-heading truncate">
                      {item.title}
                    </h4>
                  </div>
                  {item.priority && (
                    <span
                      className={`rounded px-1.5 py-0.2 text-[9px] font-bold uppercase tracking-wide shrink-0 ${
                        item.priority === 'HIGH' || item.priority === 'CRITICAL'
                          ? 'bg-danger/10 text-danger'
                          : 'bg-navy/10 text-navy'
                      }`}
                    >
                      {item.priority}
                    </span>
                  )}
                </div>
                {item.body && (
                  <p className="m-0 text-[11px] text-muted line-clamp-2 mt-1">
                    {item.body}
                  </p>
                )}
                <div className="flex items-center justify-between mt-2 pt-1 border-t border-line/40 text-[10px] text-muted">
                  <span>{item.author || item.sender || 'Administration'}</span>
                  <span>{item.date || item.created_at || 'Recent'}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </Card>
  )
}
