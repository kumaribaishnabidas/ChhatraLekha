import { Card } from '../common'
import { Link } from 'react-router-dom'

export default function RecentActivityWidget({
  title = 'Recent Activity',
  subtitle,
  items = [],
  actionLabel = 'Full History',
  actionTo,
  emptyMessage = 'No recent activity recorded.',
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
          {items.length === 0 ? (
            <p className="m-0 text-xs text-muted py-4 text-center">{emptyMessage}</p>
          ) : (
            items.map((item, idx) => (
              <div key={item.id || idx} className="flex items-start gap-3 text-left">
                <div className="h-7 w-7 rounded-full bg-brand-light text-brand flex items-center justify-center shrink-0 mt-0.5">
                  {item.icon || (
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="m-0 text-xs font-semibold text-heading leading-snug">
                    {item.title}
                  </p>
                  {item.detail && (
                    <p className="m-0 text-[11px] text-muted truncate mt-0.5">
                      {item.detail}
                    </p>
                  )}
                  <span className="text-[10px] text-muted block mt-0.5">
                    {item.time || item.timestamp}
                  </span>
                </div>
                {item.tag && (
                  <span className="rounded px-1.5 py-0.5 text-[10px] font-medium bg-line text-muted shrink-0">
                    {item.tag}
                  </span>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </Card>
  )
}
