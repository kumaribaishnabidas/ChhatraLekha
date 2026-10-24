import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import AppLayout from './components/layout/AppLayout'
import PublicLayout from './components/layout/PublicLayout'
import { useAuth } from './hooks/useAuth'
import AnomaliesPage from './pages/AnomaliesPage'
import AuthCallbackPage from './pages/AuthCallbackPage'
import DashboardPage from './pages/DashboardPage'
import ImpactPage from './pages/ImpactPage'
import InstitutionsPage from './pages/InstitutionsPage'
import LoginPage from './pages/LoginPage'
import ReportsPage from './pages/ReportsPage'
import StudentsPage from './pages/StudentsPage'
import TokenVerificationPage from './pages/TokenVerificationPage'
import UploadPage from './pages/UploadPage'
import VerificationPage from './pages/VerificationPage'
import LandingPage from './pages/LandingPage'
import AboutPage from './pages/AboutPage'
import FaqPage from './pages/FaqPage'
import ContactPage from './pages/ContactPage'
import ThankYouPage from './pages/ThankYouPage'
import PrivacyPage from './pages/PrivacyPage'
import TermsPage from './pages/TermsPage'
import NotFoundPage from './pages/NotFoundPage'
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
  const { t } = useTranslation()
  if (!can(permission)) {
    return (
      <div className="card p-8 text-center">
        <h2 className="m-0">{t('common.notAvailable')}</h2>
        <p className="m-0 mt-2 text-sm text-muted">
          {t('common.permissionMissing', { permission })}
        </p>
      </div>
    )
  }
  return children
}

export default function App() {
  return (
    <Routes>
      {/* Public Pages */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/faq" element={<FaqPage />} />
        <Route path="/contact" element={<ContactPage />} />
        <Route path="/thank-you" element={<ThankYouPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/terms" element={<TermsPage />} />
      </Route>

      <Route path="/login" element={<LoginPage />} />
      {/* Where the Google sign-in returns to. The tokens arrive in the URL
          fragment, which is never sent to a server. */}
      <Route path="/auth/callback" element={<AuthCallbackPage />} />
      {/* The public token verification route. A QR badge resolves to
          {origin}/verify/t/{token}, and the SPA rewrite delivers it here. */}
      <Route path="/verify/t/:token" element={<TokenVerificationPage />} />
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
      {/* Catch-all 404 */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
