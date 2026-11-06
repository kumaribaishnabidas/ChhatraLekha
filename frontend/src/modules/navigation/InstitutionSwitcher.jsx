import { useState } from 'react'

export default function InstitutionSwitcher({
  currentInstitutionName = 'Vidya Vikas Institute of Technology',
  currentInstitutionId = 'INST-0421',
  memberships = [],
  onSwitch,
  collapsed = false,
}) {
  const [open, setOpen] = useState(false)

  if (collapsed) {
    return (
      <div className="px-2 py-1 flex justify-center" title={`${currentInstitutionName} (${currentInstitutionId})`}>
        <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-accent text-xs font-bold border border-white/20">
          {currentInstitutionId.split('-')[0] || 'INS'}
        </div>
      </div>
    )
  }

  const hasMultiple = memberships && memberships.length > 1

  return (
    <div className="px-3 py-2 border-b border-white/10 relative">
      <div className="flex items-center justify-between text-[11px] text-white/60 mb-1">
        <span>ACTIVE INSTITUTION</span>
        {hasMultiple && (
          <button
            type="button"
            onClick={() => setOpen(!open)}
            className="text-accent hover:underline cursor-pointer bg-transparent border-0 p-0 text-[10px] font-semibold"
          >
            {open ? 'Close' : 'Switch'}
          </button>
        )}
      </div>

      <div className="flex items-center gap-2">
        <div className="w-6 h-6 rounded bg-brand flex-shrink-0 flex items-center justify-center text-[10px] font-bold text-white border border-white/20">
          IN
        </div>
        <div className="min-w-0 flex-1">
          <p className="m-0 text-xs font-semibold text-white truncate" title={currentInstitutionName}>
            {currentInstitutionName}
          </p>
          <p className="m-0 text-[10px] text-white/50 truncate font-mono">
            {currentInstitutionId}
          </p>
        </div>
      </div>

      {open && hasMultiple && (
        <div className="mt-2 rounded-lg bg-surface border border-line p-2 text-ink shadow-md space-y-1">
          <p className="m-0 text-[10px] font-bold text-muted uppercase px-1">Your Affiliated Institutions</p>
          {memberships.map((m) => (
            <button
              key={m.membership_id || m.institution_id}
              type="button"
              onClick={() => {
                onSwitch?.(m.institution_id)
                setOpen(false)
              }}
              className={`w-full text-left p-1.5 rounded text-xs cursor-pointer flex items-center justify-between ${
                m.institution_id === currentInstitutionId
                  ? 'bg-brand/10 text-brand font-semibold'
                  : 'hover:bg-surface-2 text-ink'
              }`}
            >
              <span className="truncate">{m.institution_name}</span>
              <span className="text-[10px] text-muted font-mono ml-1">{m.role}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
