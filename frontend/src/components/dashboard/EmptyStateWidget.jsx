import { Card, Button } from '../common'

export default function EmptyStateWidget({
  title = 'No Data Available',
  description = 'There are currently no records or updates to display in this section.',
  actionLabel,
  onAction,
  icon,
  className = '',
}) {
  return (
    <Card className={`p-8 text-center flex flex-col items-center justify-center space-y-3 ${className}`}>
      <div className="h-12 w-12 rounded-full bg-surface-2 border border-line text-muted flex items-center justify-center">
        {icon || (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
        )}
      </div>

      <div className="max-w-md">
        <h4 className="m-0 text-sm font-bold text-heading">{title}</h4>
        <p className="m-0 text-xs text-muted mt-1">{description}</p>
      </div>

      {actionLabel && (
        <div className="pt-2">
          <Button variant="primary" size="sm" onClick={onAction}>
            {actionLabel}
          </Button>
        </div>
      )}
    </Card>
  )
}
