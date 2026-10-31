import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import AppLayout from './components/layout/AppLayout'
import PublicLayout from './components/layout/PublicLayout'
import { Spinner } from './components/common'
import { useAuth } from './hooks/useAuth'
import CookieNotice from './components/common/CookieNotice'
import KeyboardShortcuts from './components/common/KeyboardShortcuts'
import { PERMISSIONS } from './utils/permissions'

const AnomaliesPage = lazy(() => import('./pages/AnomaliesPage'))
const AuthCallbackPage = lazy(() => import('./pages/AuthCallbackPage'))
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const ImpactPage = lazy(() => import('./pages/ImpactPage'))
const InstitutionsPage = lazy(() => import('./pages/InstitutionsPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const ReportsPage = lazy(() => import('./pages/ReportsPage'))
const StudentsPage = lazy(() => import('./pages/StudentsPage'))
const TokenVerificationPage = lazy(() => import('./pages/TokenVerificationPage'))
const UploadPage = lazy(() => import('./pages/UploadPage'))
const VerificationPage = lazy(() => import('./pages/VerificationPage'))
const StudentWalletPage = lazy(() => import('./pages/StudentWalletPage'))
const InstitutionDashboardPage = lazy(() => import('./pages/InstitutionDashboardPage'))
const LandingPage = lazy(() => import('./pages/LandingPage'))
const AboutPage = lazy(() => import('./pages/AboutPage'))
const FaqPage = lazy(() => import('./pages/FaqPage'))
const ContactPage = lazy(() => import('./pages/ContactPage'))
const ThankYouPage = lazy(() => import('./pages/ThankYouPage'))
const PrivacyPage = lazy(() => import('./pages/PrivacyPage'))
const TermsPage = lazy(() => import('./pages/TermsPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))

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

/** Redirects to the appropriate default page for the user's role. */
function RoleRedirect() {
  const { can } = useAuth()
  if (can(PERMISSIONS.VIEW_NATIONAL_DASHBOARD)) {
    return <Navigate to="/dashboard" replace />
  }
  if (can(PERMISSIONS.VIEW_INSTITUTION_DASHBOARD)) {
    return <Navigate to="/institution" replace />
  }
  if (can(PERMISSIONS.VIEW_OWN_RECORD)) {
    return <Navigate to="/wallet" replace />
  }
  return <Navigate to="/verify" replace />
}

export default function App() {
  return (
    <>
      <KeyboardShortcuts />
      <Suspense fallback={<div className="min-h-[50vh] flex items-center justify-center p-8"><Spinner /></div>}>
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
        <Route
          path="/wallet"
          element={
            <Guarded permission={PERMISSIONS.VIEW_OWN_RECORD}>
              <StudentWalletPage />
            </Guarded>
          }
        />
        <Route
          path="/institution"
          element={
            <Guarded permission={PERMISSIONS.VIEW_INSTITUTION_DASHBOARD}>
              <InstitutionDashboardPage />
            </Guarded>
          }
        />
        <Route path="*" element={<RoleRedirect />} />
      </Route>
      {/* Catch-all 404 */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
    </Suspense>
    <CookieNotice />
    </>
  )
}
