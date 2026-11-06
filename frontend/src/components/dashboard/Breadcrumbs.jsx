import { useLocation, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const ROUTE_LABELS = {
  me: 'Student Portal',
  academics: 'Academic Records',
  attendance: 'Attendance Register',
  timetable: 'Timetable Schedule',
  assignments: 'Assignments',
  results: 'Results & Examinations',
  'id-card': 'Digital ID Card',
  share: 'Share Proof',
  wallet: 'Academic Wallet',
  consent: 'Consent Ledger',
  uploads: 'Document OCR',
  parent: 'Parent & Guardian Portal',
  teacher: 'Faculty Workspace',
  institution: 'Campus Administration',
  school: 'School Administration',
  college: 'College Administration',
  dashboard: 'University & National Dashboard',
  university: 'University Oversight',
  students: 'Student Register',
  academic: 'Academic Setup',
  reports: 'Reports & Compliance',
  upload: 'CSV Ingestion',
  anomalies: 'Audit Anomalies',
  impact: 'Correction Preview',
  verify: 'Credential Verification',
  profile: 'Profile & Preferences',
  notifications: 'Notifications Centre',
  onboarding: 'User Onboarding',
}

export default function Breadcrumbs() {
  const { t } = useTranslation()
  const location = useLocation()
  const pathSegments = location.pathname.split('/').filter(Boolean)

  if (pathSegments.length === 0) return null

  let accumulatedPath = ''
  const breadcrumbItems = pathSegments.map((segment) => {
    accumulatedPath += `/${segment}`
    const label = ROUTE_LABELS[segment] || segment.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
    return {
      path: accumulatedPath,
      label,
    }
  })

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-muted">
      <Link to="/" className="text-muted hover:text-heading no-underline transition-colors">
        Home
      </Link>
      {breadcrumbItems.map((item, idx) => {
        const isLast = idx === breadcrumbItems.length - 1
        return (
          <span key={item.path} className="flex items-center gap-1.5">
            <span className="text-line select-none">/</span>
            {isLast ? (
              <span className="font-semibold text-heading truncate" aria-current="page">
                {item.label}
              </span>
            ) : (
              <Link to={item.path} className="text-muted hover:text-heading no-underline transition-colors truncate">
                {item.label}
              </Link>
            )}
          </span>
        )
      })}
    </nav>
  )
}
