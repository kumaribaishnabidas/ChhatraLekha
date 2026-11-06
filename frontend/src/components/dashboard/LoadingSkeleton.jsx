export function LoadingSkeleton({ className = '', lines = 3 }) {
  return (
    <div className={`animate-pulse space-y-3 ${className}`}>
      <div className="h-4 bg-line rounded w-3/4" />
      {Array.from({ length: lines - 1 }).map((_, i) => (
        <div key={i} className="h-3 bg-line/60 rounded w-full" />
      ))}
    </div>
  )
}

export function CardSkeleton({ className = '' }) {
  return (
    <div className={`p-5 rounded-lg border border-line bg-surface animate-pulse space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="h-3 bg-line rounded w-1/3" />
        <div className="h-6 w-6 bg-line rounded-lg" />
      </div>
      <div className="h-8 bg-line rounded w-1/2" />
      <div className="h-2 bg-line/60 rounded w-2/3" />
    </div>
  )
}

export function TableSkeleton({ rows = 4, cols = 4, className = '' }) {
  return (
    <div className={`rounded-lg border border-line bg-surface animate-pulse overflow-hidden ${className}`}>
      <div className="p-4 border-b border-line bg-surface-2 flex justify-between items-center">
        <div className="h-4 bg-line rounded w-1/4" />
        <div className="h-4 bg-line rounded w-20" />
      </div>
      <div className="divide-y divide-line p-4 space-y-3">
        {Array.from({ length: rows }).map((_, rIdx) => (
          <div key={rIdx} className="grid grid-cols-4 gap-4 py-2">
            {Array.from({ length: cols }).map((_, cIdx) => (
              <div key={cIdx} className="h-3 bg-line/60 rounded" />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

export default LoadingSkeleton
