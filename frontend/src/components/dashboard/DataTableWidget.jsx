import { useState } from 'react'
import { Card } from '../common'

export default function DataTableWidget({
  title,
  subtitle,
  columns = [],
  data = [],
  searchable = false,
  searchPlaceholder = 'Search records...',
  emptyMessage = 'No records found.',
  action,
  className = '',
}) {
  const [searchTerm, setSearchTerm] = useState('')

  const filteredData = searchable && searchTerm.trim()
    ? data.filter((row) =>
        Object.values(row).some((val) =>
          String(val).toLowerCase().includes(searchTerm.toLowerCase())
        )
      )
    : data

  return (
    <Card className={`overflow-hidden ${className}`}>
      <div className="p-5 border-b border-line flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          {title && <h3 className="m-0 text-base font-bold text-heading">{title}</h3>}
          {subtitle && <p className="m-0 text-xs text-muted mt-0.5">{subtitle}</p>}
        </div>

        <div className="flex items-center gap-2">
          {searchable && (
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder={searchPlaceholder}
              className="text-xs px-3 py-1.5 rounded-md border border-line bg-surface text-heading placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-brand w-48"
            />
          )}
          {action}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-surface-2 border-b border-line">
              {columns.map((col, idx) => (
                <th
                  key={col.key || idx}
                  className={`py-2.5 px-4 font-bold text-muted uppercase tracking-wider ${col.className || ''}`}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {filteredData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="py-8 text-center text-muted">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              filteredData.map((row, rowIdx) => (
                <tr key={row.id || rowIdx} className="hover:bg-surface-2/60 transition-colors">
                  {columns.map((col, colIdx) => (
                    <td
                      key={col.key || colIdx}
                      className={`py-3 px-4 text-heading ${col.cellClassName || ''}`}
                    >
                      {col.render ? col.render(row[col.key], row, rowIdx) : row[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
