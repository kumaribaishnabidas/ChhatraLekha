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

export function Button({
  children,
  variant = 'primary',
  className = '',
  loading = false,
  type = 'button',
  ...props
}) {
  const variants = {
    primary: 'btn-navy',
    accent: 'btn-primary',
    secondary: 'btn-outline',
    ghost: 'btn-ghost',
    danger: 'btn-danger',
  }
  return (
    <button
      type={type}
      className={`btn ${variants[variant] || variants.primary} ${className}`}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading && <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" aria-hidden="true" />}
      {children}
    </button>
  )
}

export function StatusChip({ status, children }) {
  const styles = {
    valid: 'bg-success-surface text-success-strong',
    active: 'bg-success-surface text-success-strong',
    expired: 'bg-warning-surface text-warning-strong',
    revoked: 'bg-danger-surface text-danger-strong',
    pending: 'bg-warning-surface text-warning-strong',
    'needs refresh': 'bg-info-surface text-info-strong',
  }
  const key = String(status || children || '').toLowerCase()
  return <Badge className={styles[key] || 'bg-neutral-surface text-neutral-strong'}>{children || status}</Badge>
}

export function Field({ label, hint, error, children }) {
  return (
    <label className="block">
      {label && <span className="label">{label}</span>}
      {children}
      {hint && !error && <span className="mt-1 block text-xs text-muted">{hint}</span>}
      {error && <span className="mt-1 block text-xs text-danger-strong">{error}</span>}
    </label>
  )
}

export function Input({ label, hint, error, id, className = '', ...props }) {
  const inputId = id || (label ? `input-${label.toLowerCase().replace(/[^a-z0-9]/g, '-')}` : undefined)
  return (
    <div className="w-full">
      {label && <label htmlFor={inputId} className="label">{label}</label>}
      <input id={inputId} className={`input ${error ? 'border-danger' : ''} ${className}`} {...props} />
      {hint && !error && <span className="mt-1 block text-xs text-muted">{hint}</span>}
      {error && <span className="mt-1 block text-xs text-danger-strong">{error}</span>}
    </div>
  )
}

export function Select({ label, hint, error, id, options = [], className = '', children, ...props }) {
  const selectId = id || (label ? `select-${label.toLowerCase().replace(/[^a-z0-9]/g, '-')}` : undefined)
  return (
    <div className="w-full">
      {label && <label htmlFor={selectId} className="label">{label}</label>}
      <select id={selectId} className={`input cursor-pointer ${error ? 'border-danger' : ''} ${className}`} {...props}>
        {options.map((opt) => (
          <option key={opt.value ?? opt} value={opt.value ?? opt}>
            {opt.label ?? opt}
          </option>
        ))}
        {children}
      </select>
      {hint && !error && <span className="mt-1 block text-xs text-muted">{hint}</span>}
      {error && <span className="mt-1 block text-xs text-danger-strong">{error}</span>}
    </div>
  )
}

export function Modal({ open, onClose, title, children, footer, className = '' }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true">
      <div className="fixed inset-0 bg-ink/40 transition-opacity" onClick={onClose} aria-hidden="true" />
      <div className={`relative z-10 w-full max-w-lg rounded-lg border border-line bg-surface p-6 shadow-md ${className}`}>
        {title && (
          <div className="flex items-center justify-between pb-3 mb-4 border-b border-line">
            <h3 className="m-0 text-lg font-bold text-ink">{title}</h3>
            <button
              type="button"
              onClick={onClose}
              className="text-muted hover:text-ink text-sm p-1 cursor-pointer font-bold"
              aria-label="Close"
            >
              x
            </button>
          </div>
        )}
        <div className="space-y-4">{children}</div>
        {footer && <div className="mt-6 flex justify-end gap-2 pt-3 border-t border-line">{footer}</div>}
      </div>
    </div>
  )
}

export function Table({ headers = [], rows, children, className = '' }) {
  return (
    <div className={`table-wrap ${className}`}>
      <table className="data-table">
        {headers.length > 0 && (
          <thead>
            <tr>
              {headers.map((h, i) => (
                <th key={i}>{h}</th>
              ))}
            </tr>
          </thead>
        )}
        <tbody>
          {rows
            ? rows.map((row, rIdx) => (
                <tr key={rIdx}>
                  {Array.isArray(row)
                    ? row.map((cell, cIdx) => <td key={cIdx}>{cell}</td>)
                    : row}
                </tr>
              ))
            : children}
        </tbody>
      </table>
    </div>
  )
}

export function Tabs({ tabs = [], activeTab, onChange, className = '' }) {
  return (
    <div className={`flex items-center gap-1 border-b border-line ${className}`} role="tablist">
      {tabs.map((tab) => {
        const id = tab.id ?? tab
        const label = tab.label ?? tab
        const active = activeTab === id
        return (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(id)}
            className={`px-4 py-2 text-sm font-semibold border-b-2 cursor-pointer transition-colors ${
              active
                ? 'border-brand text-brand font-bold bg-surface-2'
                : 'border-transparent text-muted hover:text-ink hover:border-line'
            }`}
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}

export { default as CopyButton, sanitizeCopyPayload } from './CopyButton'
