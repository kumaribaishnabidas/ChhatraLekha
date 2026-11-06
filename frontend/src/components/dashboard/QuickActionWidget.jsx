import { Card } from '../common'
import { Link } from 'react-router-dom'

export default function QuickActionWidget({
  title = 'Quick Actions',
  actions = [],
  className = '',
}) {
  return (
    <Card className={`p-5 ${className}`}>
      <h3 className="m-0 text-base font-bold text-heading pb-3 border-b border-line">
        {title}
      </h3>

      <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {actions.map((act, idx) => {
          const content = (
            <div className="flex flex-col items-center justify-center p-3 rounded-lg border border-line bg-surface-2 hover:bg-surface hover:border-brand/40 text-center transition-all h-full group">
              <div className="h-9 w-9 rounded-lg bg-brand-light text-brand flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
                {act.icon}
              </div>
              <span className="text-xs font-bold text-heading group-hover:text-brand transition-colors line-clamp-1">
                {act.label}
              </span>
              {act.description && (
                <span className="text-[10px] text-muted line-clamp-1 mt-0.5">
                  {act.description}
                </span>
              )}
            </div>
          )

          if (act.to) {
            return (
              <Link
                key={act.id || idx}
                to={act.to}
                className="no-underline text-inherit block h-full"
              >
                {content}
              </Link>
            )
          }

          return (
            <button
              key={act.id || idx}
              type="button"
              onClick={act.onClick}
              className="border-0 bg-transparent p-0 cursor-pointer text-inherit block w-full h-full text-left"
            >
              {content}
            </button>
          )
        })}
      </div>
    </Card>
  )
}
