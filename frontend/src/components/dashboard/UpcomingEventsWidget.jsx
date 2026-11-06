import { Card } from '../common'
import { Link } from 'react-router-dom'

export default function UpcomingEventsWidget({
  title = 'Upcoming Events',
  subtitle,
  events = [],
  actionLabel = 'View All',
  actionTo = '/timetable',
  emptyMessage = 'No upcoming events scheduled.',
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
          {events.length === 0 ? (
            <p className="m-0 text-xs text-muted py-4 text-center">{emptyMessage}</p>
          ) : (
            events.map((evt, idx) => (
              <div
                key={evt.id || idx}
                className="flex items-start gap-3 p-2.5 rounded-lg border border-line bg-surface-2 hover:bg-surface transition-colors"
              >
                <div className="flex flex-col items-center justify-center h-10 w-10 rounded-md bg-brand-light text-brand shrink-0 font-bold">
                  <span className="text-[10px] uppercase leading-none">{evt.month || 'DAY'}</span>
                  <span className="text-sm font-black leading-none mt-0.5">{evt.day || idx + 1}</span>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="m-0 text-xs font-bold text-heading truncate">{evt.title}</p>
                  <p className="m-0 text-[11px] text-muted truncate mt-0.5">{evt.subtitle || evt.description}</p>
                  {(evt.time || evt.location) && (
                    <div className="flex items-center gap-2 mt-1 text-[10px] text-muted">
                      {evt.time && <span>{evt.time}</span>}
                      {evt.time && evt.location && <span>|</span>}
                      {evt.location && <span>{evt.location}</span>}
                    </div>
                  )}
                </div>
                {evt.status && (
                  <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold bg-line text-muted shrink-0">
                    {evt.status}
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
