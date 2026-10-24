/** Small, reusable building blocks shared by every page. */
import { useTranslation } from 'react-i18next'

export function Card({ title, subtitle, actions, children, className = '' }) {
  return (
    <section className={`card p-5 ${className}`}>
      {(title || actions) && (
        <header className="flex flex-wrap items-start justify-between gap-3 mb-4">
          <div>
            {title && <h2 className="text-base m-0">{title}</h2>}
            {subtitle && <p className="m-0 mt-1 text-sm text-muted">{subtitle}</p>}
          </div>
          {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
        </header>
      )}
      {children}
    </section>
  )
}

export function KpiCard({ label, value, hint, tone = 'default' }) {
  const tones = {
    default: 'text-navy',
    good: 'text-emerald',
    warning: 'text-saffron',
    critical: 'text-crimson',
  }
  return (
    <div className="card p-5 flex flex-col gap-1">
      <span className={`text-3xl font-extrabold tracking-tight ${tones[tone] || tones.default}`}>
        {value}
      </span>
      <span className="text-[11px] font-bold uppercase tracking-widest text-muted">{label}</span>
      {hint && <span className="text-xs text-muted">{hint}</span>}
    </div>
  )
}

export function Badge({ children, className = '' }) {
  return (
    <span
      className={`inline-block rounded px-2 py-0.5 text-[11px] font-bold tracking-wide ${className}`}
    >
      {children}
    </span>
  )
}

export function Spinner({ label = 'Loading...' }) {
  const { t } = useTranslation()
  return (
    <div className="flex items-center gap-3 p-8 text-sm text-muted" role="status">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-line border-t-bright-blue" />
       {label === 'Loading...' ? t('common.loading') : label}
    </div>
  )
}

export function Skeleton({ className = 'h-4 w-full' }) {
  return <div className={`skeleton ${className}`} aria-hidden="true" />
}

export function TableSkeleton({ rows = 5, columns = 4 }) {
  return (
    <div className="table-wrap p-4" aria-busy="true">
      <div className="flex flex-col gap-3">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="flex gap-4">
            {Array.from({ length: columns }).map((_, c) => (
              <div key={c} className="skeleton h-5 flex-1" />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  const { t } = useTranslation()
  return (
    <div
      role="alert"
      className="rounded border border-danger/30 bg-danger-surface p-5 text-sm text-danger-strong"
    >
      <p className="m-0 font-semibold">{t('common.errorTitle')}</p>
      <p className="m-0 mt-1">{message}</p>
      {onRetry && (
        <button type="button" className="btn btn-outline mt-3" onClick={onRetry}>
          {t('common.retry')}
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title, description, action }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded border border-dashed border-line bg-surface-2 p-10 text-center">
      <p className="m-0 font-semibold text-navy">{title}</p>
      {description && <p className="m-0 text-sm text-muted">{description}</p>}
      {action}
    </div>
  )
}

export function Pagination({ page, pageCount, onChange }) {
  const { t } = useTranslation()
  if (!pageCount || pageCount <= 1) return null
  return (
    <nav className="flex items-center justify-end gap-2 mt-4" aria-label={t('common.page', { page, count: pageCount })}>
      <button
        type="button"
        className="btn btn-outline"
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
      >
        {t('common.previous')}
      </button>
      <span className="text-sm text-muted">
        {t('common.page', { page, count: pageCount })}
      </span>
      <button
        type="button"
        className="btn btn-outline"
        disabled={page >= pageCount}
        onClick={() => onChange(page + 1)}
      >
        {t('common.next')}
      </button>
    </nav>
  )
}

export function FilterBar({ children }) {
  return <div className="flex flex-wrap items-end gap-3 mb-4">{children}</div>
}

export { default as CopyButton, sanitizeCopyPayload } from './CopyButton'
