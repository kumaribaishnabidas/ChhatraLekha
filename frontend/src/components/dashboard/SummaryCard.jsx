import { Card } from '../common'

export default function SummaryCard({
  label,
  value,
  hint,
  tone = 'default',
  icon,
  trend,
  className = '',
}) {
  const toneClasses = {
    default: 'text-navy',
    good: 'text-emerald',
    warning: 'text-amber-600 dark:text-amber-400',
    critical: 'text-danger',
    accent: 'text-accent-strong',
  }

  const toneBg = {
    default: 'bg-navy/10',
    good: 'bg-emerald/10',
    warning: 'bg-amber-500/10',
    critical: 'bg-danger/10',
    accent: 'bg-accent/10',
  }

  return (
    <Card className={`p-5 flex flex-col justify-between space-y-3 ${className}`}>
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs font-bold uppercase tracking-wider text-muted truncate">
          {label}
        </span>
        {icon && (
          <div className={`h-8 w-8 rounded-lg flex items-center justify-center shrink-0 ${toneBg[tone] || 'bg-line'}`}>
            {icon}
          </div>
        )}
      </div>

      <div>
        <div className="flex items-baseline gap-2">
          <span className={`text-2xl sm:text-3xl font-black tracking-tight ${toneClasses[tone] || 'text-heading'}`}>
            {value}
          </span>
          {trend && (
            <span className="text-xs font-semibold text-muted">
              {trend}
            </span>
          )}
        </div>
        {hint && (
          <p className="m-0 mt-1 text-xs text-muted truncate">
            {hint}
          </p>
        )}
      </div>
    </Card>
  )
}
