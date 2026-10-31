/**
 * The role-to-permission matrix of the web frontend.
 *
 * This mirrors `app/core/rbac.py` on the server. It is used **only** to decide
 * what to show; the server enforces every permission independently, so a
 * user who tampers with the frontend gains nothing.
 */

export const PERMISSIONS = {
  VIEW_NATIONAL_DASHBOARD: 'view_national_dashboard',
  REVIEW_ANOMALIES: 'review_anomalies',
  VIEW_AUDIT_TRAIL: 'view_audit_trail',
  VIEW_COMPLIANCE_MATRIX: 'view_compliance_matrix',
  ONBOARD_STUDENTS: 'onboard_students',
  IMPORT_CSV: 'import_csv',
  VIEW_INSTITUTION_DASHBOARD: 'view_institution_dashboard',
  VIEW_STUDENT_REGISTER: 'view_student_register',
  VIEW_OWN_RECORD: 'view_own_record',
  MANAGE_CONSENT: 'manage_consent',
  VERIFY_CREDENTIAL: 'verify_credential',
  GENERATE_CERTIFICATE: 'generate_certificate',
  EXPORT_REPORTS: 'export_reports',
  PREVIEW_CORRECTION: 'preview_correction',
  APPLY_CORRECTION: 'apply_correction',
  VIEW_IMPACTS: 'view_impacts',
  REVIEW_TASKS: 'review_tasks',
  ISSUE_OWN_TOKEN: 'issue_own_token',

  // Connected Campus permissions
  MANAGE_ACADEMIC_SETUP: 'manage_academic_setup',
  RECORD_ATTENDANCE: 'record_attendance',
  VIEW_ATTENDANCE: 'view_attendance',
  RECORD_MARKS: 'record_marks',
  PUBLISH_RESULTS: 'publish_results',
  VIEW_RESULTS: 'view_results',
  MANAGE_ANNOUNCEMENTS: 'manage_announcements',
  VIEW_ANNOUNCEMENTS: 'view_announcements',
  VIEW_PARENT_PORTAL: 'view_parent_portal',
}

const DIRECTORATE = [
  PERMISSIONS.VIEW_NATIONAL_DASHBOARD,
  PERMISSIONS.REVIEW_ANOMALIES,
  PERMISSIONS.VIEW_AUDIT_TRAIL,
  PERMISSIONS.VIEW_COMPLIANCE_MATRIX,
  PERMISSIONS.EXPORT_REPORTS,
  PERMISSIONS.VERIFY_CREDENTIAL,
  PERMISSIONS.PREVIEW_CORRECTION,
  PERMISSIONS.APPLY_CORRECTION,
  PERMISSIONS.VIEW_IMPACTS,
  PERMISSIONS.REVIEW_TASKS,
  PERMISSIONS.VIEW_ANNOUNCEMENTS,
  PERMISSIONS.MANAGE_ANNOUNCEMENTS,
]

const INSTITUTION = [
  PERMISSIONS.VIEW_INSTITUTION_DASHBOARD,
  PERMISSIONS.VIEW_STUDENT_REGISTER,
  PERMISSIONS.ONBOARD_STUDENTS,
  PERMISSIONS.IMPORT_CSV,
  PERMISSIONS.MANAGE_CONSENT,
  PERMISSIONS.GENERATE_CERTIFICATE,
  PERMISSIONS.EXPORT_REPORTS,
  PERMISSIONS.VIEW_AUDIT_TRAIL,
  PERMISSIONS.PREVIEW_CORRECTION,
  PERMISSIONS.APPLY_CORRECTION,
  PERMISSIONS.VIEW_IMPACTS,
  PERMISSIONS.REVIEW_TASKS,
  PERMISSIONS.MANAGE_ACADEMIC_SETUP,
  PERMISSIONS.RECORD_ATTENDANCE,
  PERMISSIONS.VIEW_ATTENDANCE,
  PERMISSIONS.RECORD_MARKS,
  PERMISSIONS.PUBLISH_RESULTS,
  PERMISSIONS.VIEW_RESULTS,
  PERMISSIONS.MANAGE_ANNOUNCEMENTS,
  PERMISSIONS.VIEW_ANNOUNCEMENTS,
]

const ACADEMIC_ADMIN = [
  PERMISSIONS.VIEW_INSTITUTION_DASHBOARD,
  PERMISSIONS.VIEW_STUDENT_REGISTER,
  PERMISSIONS.ONBOARD_STUDENTS,
  PERMISSIONS.MANAGE_ACADEMIC_SETUP,
  PERMISSIONS.RECORD_ATTENDANCE,
  PERMISSIONS.VIEW_ATTENDANCE,
  PERMISSIONS.PUBLISH_RESULTS,
  PERMISSIONS.VIEW_RESULTS,
  PERMISSIONS.MANAGE_ANNOUNCEMENTS,
  PERMISSIONS.VIEW_ANNOUNCEMENTS,
  PERMISSIONS.EXPORT_REPORTS,
  PERMISSIONS.VIEW_AUDIT_TRAIL,
]

const TEACHER = [
  PERMISSIONS.VIEW_ATTENDANCE,
  PERMISSIONS.RECORD_ATTENDANCE,
  PERMISSIONS.RECORD_MARKS,
  PERMISSIONS.VIEW_RESULTS,
  PERMISSIONS.VIEW_ANNOUNCEMENTS,
  PERMISSIONS.MANAGE_ANNOUNCEMENTS,
]

const VERIFIER = [PERMISSIONS.VERIFY_CREDENTIAL, PERMISSIONS.VIEW_AUDIT_TRAIL]

const STUDENT = [
  PERMISSIONS.VIEW_OWN_RECORD,
  PERMISSIONS.GENERATE_CERTIFICATE,
  PERMISSIONS.MANAGE_CONSENT,
  PERMISSIONS.ISSUE_OWN_TOKEN,
  PERMISSIONS.VIEW_ATTENDANCE,
  PERMISSIONS.VIEW_RESULTS,
  PERMISSIONS.VIEW_ANNOUNCEMENTS,
]

const PARENT = [
  PERMISSIONS.VIEW_PARENT_PORTAL,
  PERMISSIONS.VIEW_ATTENDANCE,
  PERMISSIONS.VIEW_RESULTS,
  PERMISSIONS.VIEW_ANNOUNCEMENTS,
]

export const ROLE_PERMISSIONS = {
  national_admin: DIRECTORATE,
  aicte_admin: DIRECTORATE,
  platform_operator: DIRECTORATE,
  state_admin: DIRECTORATE,
  district_admin: DIRECTORATE,
  regulator_admin: DIRECTORATE,
  institution_admin: INSTITUTION,
  academic_admin: ACADEMIC_ADMIN,
  teacher: TEACHER,
  verifier: VERIFIER,
  student: STUDENT,
  parent: PARENT,
}

export const ROLE_LABELS = {
  national_admin: 'National Administrator',
  aicte_admin: 'Platform Operator / Directorate',
  platform_operator: 'Platform Operator',
  state_admin: 'State Education Authority',
  district_admin: 'District Education Officer',
  regulator_admin: 'Board / Affiliation Regulator',
  institution_admin: 'Institution Owner / Admin',
  academic_admin: 'Academic Administrator',
  teacher: 'Teacher / Faculty',
  verifier: 'Verifier',
  student: 'Student',
  parent: 'Parent / Guardian',
}

export function permissionsFor(role) {
  return ROLE_PERMISSIONS[role] || []
}

export function can(role, permission) {
  return permissionsFor(role).includes(permission)
}

export function canAny(role, permissions) {
  return permissions.some((permission) => can(role, permission))
}
