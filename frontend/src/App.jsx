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
const SchoolDashboardPage = lazy(() => import('./pages/SchoolDashboardPage'))
const CollegeDashboardPage = lazy(() => import('./pages/CollegeDashboardPage'))
const UniversityDashboardPage = lazy(() => import('./pages/UniversityDashboardPage'))
const StudentHomePage = lazy(() => import('./pages/student/StudentHomePage'))
const StudentIdCardPage = lazy(() => import('./pages/student/StudentIdCardPage'))
const StudentSharePage = lazy(() => import('./pages/student/StudentSharePage'))
const StudentConsentPage = lazy(() => import('./pages/student/StudentConsentPage'))
const StudentUploadsPage = lazy(() => import('./pages/student/StudentUploadsPage'))
const StudentResultsPage = lazy(() => import('./pages/student/StudentResultsPage'))
const StudentActivityPage = lazy(() => import('./pages/student/StudentActivityPage'))
const TransparencyPage = lazy(() => import('./pages/TransparencyPage'))
const TeacherWorkspacePage = lazy(() => import('./pages/TeacherWorkspacePage'))
const ParentPortalPage = lazy(() => import('./pages/ParentPortalPage'))
const AcademicSetupPage = lazy(() => import('./pages/AcademicSetupPage'))
const AttendancePage = lazy(() => import('./pages/AttendancePage'))
const AnnouncementsPage = lazy(() => import('./pages/AnnouncementsPage'))
const AssessmentsPage = lazy(() => import('./pages/AssessmentsPage'))
const LandingPage = lazy(() => import('./pages/LandingPage'))
const SignupPage = lazy(() => import('./pages/SignupPage'))
const OnboardingPage = lazy(() => import('./pages/OnboardingPage'))
const AccessibilityPage = lazy(() => import('./pages/AccessibilityPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const NotificationsPage = lazy(() => import('./pages/NotificationsPage'))
const WorkspacePlaceholderPage = lazy(() => import('./pages/WorkspacePlaceholderPage'))
const AboutPage = lazy(() => import('./pages/AboutPage'))
const EarlyAccessPage = lazy(() => import('./pages/EarlyAccessPage'))
const HelpPage = lazy(() => import('./pages/HelpPage'))
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
  const { role, can } = useAuth()
  const r = (role || '').toLowerCase()
  if (r === 'school_admin') return <Navigate to="/school" replace />
  if (r === 'college_admin') return <Navigate to="/college" replace />
  if (r === 'university_admin') return <Navigate to="/university" replace />
  if (can(PERMISSIONS.VIEW_NATIONAL_DASHBOARD)) {
    return <Navigate to="/dashboard" replace />
  }
  if (can(PERMISSIONS.VIEW_INSTITUTION_DASHBOARD)) {
    return <Navigate to="/institution" replace />
  }
  if (can(PERMISSIONS.RECORD_ATTENDANCE)) {
    return <Navigate to="/teacher" replace />
  }
  if (can(PERMISSIONS.VIEW_PARENT_PORTAL)) {
    return <Navigate to="/parent" replace />
  }
  if (can(PERMISSIONS.VIEW_OWN_RECORD)) {
    return <Navigate to="/me" replace />
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
        <Route path="/early-access" element={<EarlyAccessPage />} />
        <Route path="/help" element={<HelpPage />} />
        <Route path="/faq" element={<FaqPage />} />
        <Route path="/contact" element={<ContactPage />} />
        <Route path="/thank-you" element={<ThankYouPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/transparency" element={<TransparencyPage />} />
        <Route path="/accessibility" element={<AccessibilityPage />} />
      </Route>

      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route
        path="/onboarding"
        element={
          <Protected>
            <OnboardingPage />
          </Protected>
        }
      />
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
          path="/me"
          element={
            <Guarded permission={PERMISSIONS.VIEW_OWN_RECORD}>
              <StudentHomePage />
            </Guarded>
          }
        />
        <Route
          path="/me/id-card"
          element={
            <Guarded permission={PERMISSIONS.VIEW_OWN_RECORD}>
              <StudentIdCardPage />
            </Guarded>
          }
        />
        <Route
          path="/me/share"
          element={
            <Guarded permission={PERMISSIONS.ISSUE_OWN_TOKEN}>
              <StudentSharePage />
            </Guarded>
          }
        />
        <Route
          path="/me/consent"
          element={
            <Guarded permission={PERMISSIONS.MANAGE_CONSENT}>
              <StudentConsentPage />
            </Guarded>
          }
        />
        <Route
          path="/me/uploads"
          element={
            <Guarded permission={PERMISSIONS.VIEW_OWN_RECORD}>
              <StudentUploadsPage />
            </Guarded>
          }
        />
        <Route
          path="/me/results"
          element={
            <Guarded permission={PERMISSIONS.VIEW_OWN_RECORD}>
              <StudentResultsPage />
            </Guarded>
          }
        />
        <Route
          path="/me/activity"
          element={
            <Guarded permission={PERMISSIONS.VIEW_OWN_RECORD}>
              <StudentActivityPage />
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
        <Route
          path="/school"
          element={
            <Guarded permission={PERMISSIONS.VIEW_INSTITUTION_DASHBOARD}>
              <SchoolDashboardPage />
            </Guarded>
          }
        />
        <Route
          path="/college"
          element={
            <Guarded permission={PERMISSIONS.VIEW_INSTITUTION_DASHBOARD}>
              <CollegeDashboardPage />
            </Guarded>
          }
        />
        <Route
          path="/university"
          element={
            <Guarded permission={PERMISSIONS.VIEW_NATIONAL_DASHBOARD}>
              <UniversityDashboardPage />
            </Guarded>
          }
        />
        <Route
          path="/academic"
          element={
            <Guarded permission={PERMISSIONS.MANAGE_ACADEMIC_SETUP}>
              <AcademicSetupPage />
            </Guarded>
          }
        />
        <Route
          path="/attendance"
          element={
            <Guarded permission={PERMISSIONS.VIEW_ATTENDANCE}>
              <AttendancePage />
            </Guarded>
          }
        />
        <Route
          path="/me/attendance"
          element={
            <Guarded permission={PERMISSIONS.VIEW_ATTENDANCE}>
              <AttendancePage />
            </Guarded>
          }
        />
        <Route
          path="/teacher"
          element={
            <Guarded permission={PERMISSIONS.RECORD_ATTENDANCE}>
              <TeacherWorkspacePage />
            </Guarded>
          }
        />
        <Route
          path="/parent"
          element={
            <Guarded permission={PERMISSIONS.VIEW_PARENT_PORTAL}>
              <ParentPortalPage />
            </Guarded>
          }
        />
        <Route
          path="/announcements"
          element={
            <Guarded permission={PERMISSIONS.VIEW_ANNOUNCEMENTS}>
              <AnnouncementsPage />
            </Guarded>
          }
        />
        <Route
          path="/assessments"
          element={
            <Guarded permission={PERMISSIONS.VIEW_RESULTS}>
              <AssessmentsPage />
            </Guarded>
          }
        />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route
          path="/me/academics"
          element={
            <WorkspacePlaceholderPage
              title="Academic Curriculum"
              moduleName="Academics & Syllabus"
              features={['Semester Course Matrix', 'Credit Point Distribution', 'Syllabus & Learning Outcomes', 'Prerequisite Tracking']}
            />
          }
        />
        <Route
          path="/me/attendance"
          element={
            <WorkspacePlaceholderPage
              title="Attendance Register"
              moduleName="Daily & Period Attendance"
              features={['Daily Check-in Records', 'Subject-wise Percentage', 'Leave Applications', 'Parent Alerts']}
            />
          }
        />
        <Route
          path="/me/timetable"
          element={
            <WorkspacePlaceholderPage
              title="Timetable & Class Schedule"
              moduleName="Timetable & Scheduling"
              features={['Weekly Period Grid', 'Classroom & Lab Room Allocations', 'Faculty Substitutions', 'Exam Slot Schedules']}
            />
          }
        />
        <Route
          path="/me/assignments"
          element={
            <WorkspacePlaceholderPage
              title="Coursework & Assignments"
              moduleName="Learning & Assignments"
              features={['Active Problem Sets', 'File Submissions', 'Teacher Feedback & Rubrics', 'Deadlines Calendar']}
            />
          }
        />
        <Route
          path="/library"
          element={
            <WorkspacePlaceholderPage
              title="Campus Library (OPAC)"
              moduleName="Digital & Physical Library"
              features={['Online Book Catalogue (OPAC)', 'ISBN & Author Search', 'Book Reservations', 'Due Date Notifications']}
            />
          }
        />
        <Route
          path="/opportunities"
          element={
            <WorkspacePlaceholderPage
              title="Career & Opportunities"
              moduleName="Internships & Placements"
              features={['Campus Placement Drives', 'National Scholarship Directory', 'Verified Student Resume Export', 'Interview Schedules']}
            />
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
