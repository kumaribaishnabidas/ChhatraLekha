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
}

const DIRECTORATE = [
  PERMISSIONS.VIEW_NATIONAL_DASHBOARD,
  PERMISSIONS.REVIEW_ANOMALIES,
  PERMISSIONS.VIEW_AUDIT_TRAIL,
  PERMISSIONS.VIEW_COMPLIANCE_MATRIX,
  PERMISSIONS.EXPORT_REPORTS,
  // The Directorate is the national authority, so it verifies credentials
  // and issues the tokens that back them.
  PERMISSIONS.VERIFY_CREDENTIAL,
  PERMISSIONS.PREVIEW_CORRECTION,
  PERMISSIONS.APPLY_CORRECTION,
  PERMISSIONS.VIEW_IMPACTS,
  PERMISSIONS.REVIEW_TASKS,
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
]

const VERIFIER = [PERMISSIONS.VERIFY_CREDENTIAL, PERMISSIONS.VIEW_AUDIT_TRAIL]

const STUDENT = [
  PERMISSIONS.VIEW_OWN_RECORD,
  PERMISSIONS.GENERATE_CERTIFICATE,
  PERMISSIONS.MANAGE_CONSENT,
  PERMISSIONS.ISSUE_OWN_TOKEN,
]

export const ROLE_PERMISSIONS = {
  aicte_admin: DIRECTORATE,
  institution_admin: INSTITUTION,
  verifier: VERIFIER,
  student: STUDENT,
}

export const ROLE_LABELS = {
  aicte_admin: 'AICTE Directorate',
  institution_admin: 'Institution Admin',
  verifier: 'Verifier',
  student: 'Student',
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
