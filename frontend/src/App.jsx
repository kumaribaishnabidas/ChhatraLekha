import { Navigate, Route, Routes, useLocation } from 'react-router-dom'

import AppLayout from './components/layout/AppLayout'
import { useAuth } from './hooks/useAuth'
import AnomaliesPage from './pages/AnomaliesPage'
import DashboardPage from './pages/DashboardPage'
import ImpactPage from './pages/ImpactPage'
import InstitutionsPage from './pages/InstitutionsPage'
import LoginPage from './pages/LoginPage'
import ReportsPage from './pages/ReportsPage'
import StudentsPage from './pages/StudentsPage'
import UploadPage from './pages/UploadPage'
import VerificationPage from './pages/VerificationPage'
import { PERMISSIONS } from './utils/permissions'

/** A route that requires a signed-in user. */
function Protected({ children }) {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  return children
}

/** A route that requires a specific permission. */
function Guarded({ permission, children }) {
  const { can } = useAuth()
  if (!can(permission)) {
    return (
      <div className="card p-8 text-center">
        <h2 className="m-0">Not available for your role</h2>
        <p className="m-0 mt-2 text-sm text-muted">
          Your account does not hold the <code>{permission}</code> permission. The server
          enforces the same rule independently of this screen.
        </p>
      </div>
    )
  }
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <Protected>
            <AppLayout />
          </Protected>
        }
      >
        <Route
          path="/dashboard"
          element={
            <Guarded permission={PERMISSIONS.VIEW_NATIONAL_DASHBOARD}>
              <DashboardPage />
            </Guarded>
          }
        />
        <Route
          path="/institutions"
          element={
            <Guarded permission={PERMISSIONS.VIEW_COMPLIANCE_MATRIX}>
              <InstitutionsPage />
            </Guarded>
          }
        />
        <Route
          path="/students"
          element={
            <Guarded permission={PERMISSIONS.VIEW_STUDENT_REGISTER}>
              <StudentsPage />
            </Guarded>
          }
        />
        <Route
          path="/upload"
          element={
            <Guarded permission={PERMISSIONS.IMPORT_CSV}>
              <UploadPage />
            </Guarded>
          }
        />
        <Route
          path="/anomalies"
          element={
            <Guarded permission={PERMISSIONS.REVIEW_ANOMALIES}>
              <AnomaliesPage />
            </Guarded>
          }
        />
        <Route
          path="/impact"
          element={
            <Guarded permission={PERMISSIONS.PREVIEW_CORRECTION}>
              <ImpactPage />
            </Guarded>
          }
        />
        <Route
          path="/verify"
          element={
            <Guarded permission={PERMISSIONS.VERIFY_CREDENTIAL}>
              <VerificationPage />
            </Guarded>
          }
        />
        <Route
          path="/reports"
          element={
            <Guarded permission={PERMISSIONS.EXPORT_REPORTS}>
              <ReportsPage />
            </Guarded>
          }
        />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  )
}
