/** The application shell: the top bar, the navigation and the page frame. */
import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useAuth } from '../../hooks/useAuth'
import { useApi } from '../../hooks/useApi'
import { api } from '../../services/api'
import { PERMISSIONS, ROLE_LABELS } from '../../utils/permissions'

const NAVIGATION = [
  { to: '/dashboard', label: 'Dashboard', permission: PERMISSIONS.VIEW_NATIONAL_DASHBOARD },
  { to: '/institutions', label: 'Institutions', permission: PERMISSIONS.VIEW_COMPLIANCE_MATRIX },
  { to: '/students', label: 'Students', permission: PERMISSIONS.VIEW_STUDENT_REGISTER },
  { to: '/upload', label: 'Upload CSV', permission: PERMISSIONS.IMPORT_CSV },
  { to: '/anomalies', label: 'Anomalies', permission: PERMISSIONS.REVIEW_ANOMALIES },
  { to: '/impact', label: 'Change Impact', permission: PERMISSIONS.PREVIEW_CORRECTION },
  { to: '/verify', label: 'Verify', permission: PERMISSIONS.VERIFY_CREDENTIAL },
  { to: '/reports', label: 'Reports', permission: PERMISSIONS.EXPORT_REPORTS },
]

export default function AppLayout() {
  const { user, role, can, logout } = useAuth()
  const navigate = useNavigate()
  const health = useApi(() => api.get('/health').then((r) => r.data), [])

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 bg-navy text-white shadow-lg">
        <div className="mx-auto max-w-[1240px] px-5 py-3 flex items-center gap-5">
          <NavLink to="/dashboard" className="flex items-center gap-3 no-underline">
            <img
              src="/brand/edusync-lockup.png"
              alt="EduSynC"
              className="h-9 w-auto block"
              onError={(event) => {
                event.currentTarget.style.display = 'none'
              }}
            />
            <span className="hidden sm:inline font-extrabold tracking-wide text-lg">
              EduSynC
            </span>
          </NavLink>

          <nav className="ml-auto flex items-center gap-1 overflow-x-auto">
            {NAVIGATION.filter((item) => can(item.permission)).map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-2 text-sm font-semibold no-underline whitespace-nowrap ${
                    isActive ? 'bg-white/15 text-white' : 'text-white/80 hover:bg-white/10'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-3 pl-3 border-l border-white/20">
            <div className="hidden md:block text-right leading-tight">
              <p className="m-0 text-sm font-semibold">{user?.display_name || 'Signed in'}</p>
              <p className="m-0 text-[11px] text-white/70">{ROLE_LABELS[role] || role}</p>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-full border border-white/30 bg-white/10 px-3 py-1.5 text-xs font-semibold text-white cursor-pointer"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      {health.data?.in_memory_demo_data && (
        <div
          role="status"
          className="bg-[#FEF3DC] border-b border-[#E8C97A] px-5 py-2 text-center text-sm text-[#96650A]"
        >
          <strong>Demo mode.</strong> {health.data.notice}
        </div>
      )}

      <main className="mx-auto max-w-[1240px] px-5 py-7">
        <Outlet />
      </main>

      <footer className="border-t border-line bg-white py-5 text-center text-xs text-muted">
        <strong>EduSynC</strong> &mdash; the APAAR ID Student Data Management &amp;
        Verification Platform. Synthetic demonstration data only. Verification is
        against this prototype&apos;s database, not official APAAR or AICTE
        verification.
      </footer>
    </div>
  )
}
