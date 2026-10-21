/** Formatting helpers shared by the pages. */

export function formatNumber(value) {
  return Number(value || 0).toLocaleString('en-IN')
}

export function formatPercent(value, digits = 1) {
  return `${Number(value || 0).toFixed(digits)}%`
}

export function formatDate(value) {
  if (!value) return '-'
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

export function formatDateTime(value) {
  if (!value) return '-'
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatApaar(value) {
  const digits = String(value || '').replace(/\D/g, '')
  if (digits.length !== 12) return value || '-'
  return `${digits.slice(0, 4)} ${digits.slice(4, 8)} ${digits.slice(8)}`
}

export function maskApaar(value) {
  const digits = String(value || '').replace(/\D/g, '')
  if (digits.length < 4) return '*'.repeat(digits.length)
  return `${digits.slice(0, 4)} **** ****`
}

/** A readable label for a quota code. */
export const QUOTA_LABELS = {
  REGULAR_MERIT: 'Merit',
  MANAGEMENT: 'Management',
  SUPERNUMERARY_NRI: 'NRI',
  SUPERNUMERARY_OCI: 'OCI',
  SUPERNUMERARY_FN: 'Foreign National',
  SUPERNUMERARY_TFW: 'TFW',
  PMSSS: 'PMSSS',
}

export function quotaLabel(code) {
  return QUOTA_LABELS[code] || code || '-'
}

export const ANOMALY_LABELS = {
  EXCESS_APPROVED_INTAKE: 'Over-admission',
  DUPLICATE_CROSS_COLLEGE: 'Cross-enrolment',
  DUPLICATE_SAME_INSTITUTION: 'Duplicate record',
  DUPLICATE_ROLL_NUMBER: 'Duplicate roll no.',
  INVALID_APAAR_FORMAT: 'Invalid APAAR',
  SUPERNUMERARY_BREACH: 'Supernumerary cap',
  INCONSISTENT_CATEGORY: 'Data inconsistency',
  IMPOSSIBLE_DATE: 'Date conflict',
  MISSING_REQUIRED_FIELD: 'Incomplete record',
  UNSANCTIONED_PROGRAM: 'Unregistered course',
}

export function anomalyLabel(code) {
  return ANOMALY_LABELS[code] || code || '-'
}

/** Tailwind classes for a severity badge. */
export function severityClass(severity) {
  switch (severity) {
    case 'CRITICAL':
      return 'bg-[#FDE7E7] text-crimson'
    case 'HIGH':
      return 'bg-[#FEF3DC] text-[#96650A]'
    case 'WARNING':
      return 'bg-[#E7EFFC] text-mid-blue'
    default:
      return 'bg-[#EDF1F6] text-muted'
  }
}

export function statusClass(status) {
  switch (status) {
    case 'VERIFIED':
      return 'bg-[#E2F6EC] text-[#0A6B3D]'
    case 'FLAGGED_ANOMALY':
      return 'bg-[#FDE7E7] text-crimson'
    default:
      return 'bg-[#FEF3DC] text-[#96650A]'
  }
}

export function riskClass(band) {
  switch (band) {
    case 'CRITICAL':
      return 'bg-crimson text-white'
    case 'HIGH':
      return 'bg-[#FDE7E7] text-crimson'
    case 'MEDIUM':
      return 'bg-[#FEF3DC] text-[#96650A]'
    default:
      return 'bg-[#E2F6EC] text-[#0A6B3D]'
  }
}
