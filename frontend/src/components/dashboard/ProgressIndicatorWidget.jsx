import { Card } from '../common'

export default function ProgressIndicatorWidget({
  title = 'Progress & Targets',
  items = [],
  className = '',
}) {
  const toneColors = {
    good: 'bg-emerald',
    warning: 'bg-amber-500',
    critical: 'bg-danger',
    brand: 'bg-brand',
    navy: 'bg-navy',
  }

  return (
    <Card className={`p-5 flex flex-col justify-between ${className}`}>
      <div>
        <h3 className="m-0 text-base font-bold text-heading pb-3 border-b border-line">
          {title}
        </h3>

        <div className="mt-4 space-y-4">
          {items.map((item, idx) => {
            const pct = Math.min(100, Math.max(0, Math.round((item.value / (item.max || 100)) * 100)))
            const tone = item.tone || (pct >= 75 ? 'good' : pct >= 50 ? 'warning' : 'critical')
            const barClass = toneColors[tone] || 'bg-brand'

            return (
              <div key={item.id || idx} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="text-heading truncate">{item.label}</span>
                  <span className="text-muted shrink-0">
                    {item.displayValue || `${pct}%`}
                    {item.target && <span className="font-normal text-muted"> / {item.target}</span>}
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-line overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${barClass}`}
                    style={{ width: `${pct}%` }}
                    role="progressbar"
                    aria-valuenow={pct}
                    aria-valuemin="0"
                    aria-valuemax="100"
                  />
                </div>
                {item.hint && (
                  <p className="m-0 text-[11px] text-muted">
                    {item.hint}
                  </p>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </Card>
  )
}
