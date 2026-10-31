package com.chhatralekha.core.security

import com.chhatralekha.core.model.UserRole

/**
 * A capability that a signed-in account may exercise.
 */
enum class Permission(val label: String, val description: String) {
    VIEW_NATIONAL_DASHBOARD(
        "National dashboard",
        "See the pan-India intake, quota and anomaly picture."
    ),
    REVIEW_ANOMALIES(
        "Review anomalies",
        "Inspect, filter and resolve detected regulatory anomalies."
    ),
    VIEW_AUDIT_TRAIL(
        "Audit trail",
        "Read the tamper-evident regulatory audit trail."
    ),
    VIEW_COMPLIANCE_MATRIX(
        "Compliance matrix",
        "Compare every institution against its sanctioned intake."
    ),
    ONBOARD_STUDENTS(
        "Onboard students",
        "Create individual enrolment records."
    ),
    IMPORT_CSV(
        "Import CSV batch",
        "Upload and commit a batch enrolment file."
    ),
    VIEW_INSTITUTION_DASHBOARD(
        "Institution dashboard",
        "See the institution's own intake utilisation and registers."
    ),
    VIEW_STUDENT_REGISTER(
        "Student register",
        "Browse the enrolled student records of one's own institution."
    ),
    VIEW_OWN_RECORD(
        "Own academic record",
        "See one's own APAAR card, transcript and certificates."
    ),
    MANAGE_CONSENT(
        "Manage consent",
        "Grant, review and revoke the processing consent of a student."
    ),
    VERIFY_CREDENTIAL(
        "Verify credential",
        "Verify an APAAR credential or scan an APAAR QR badge."
    ),
    GENERATE_CERTIFICATE(
        "Generate certificate",
        "Issue a bonafide or degree certificate carrying the APAAR ID."
    ),
    EXPORT_REPORTS(
        "Export reports",
        "Download regulatory reports as CSV or PDF."
    ),
    RECORD_ATTENDANCE(
        "Record attendance",
        "Mark and submit class attendance."
    ),
    RECORD_MARKS(
        "Record assessment marks",
        "Enter and review evaluation marks and grades."
    ),
    VIEW_PARENT_PORTAL(
        "Parent portal",
        "View attendance, grades and notices for linked students."
    )
}

/**
 * The single source of truth for who may do what.
 *
 * The app, the backend and the web portal all consult this matrix, so a
 * permission can never be enforced in one surface but forgotten in another.
 */
object AccessControl {

    private val DIRECTORATE: Set<Permission> = setOf(
        Permission.VIEW_NATIONAL_DASHBOARD,
        Permission.REVIEW_ANOMALIES,
        Permission.VIEW_AUDIT_TRAIL,
        Permission.VIEW_COMPLIANCE_MATRIX,
        Permission.EXPORT_REPORTS
    )

    private val INSTITUTION: Set<Permission> = setOf(
        Permission.VIEW_INSTITUTION_DASHBOARD,
        Permission.VIEW_STUDENT_REGISTER,
        Permission.ONBOARD_STUDENTS,
        Permission.IMPORT_CSV,
        Permission.MANAGE_CONSENT,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_AUDIT_TRAIL
    )

    private val VERIFIER: Set<Permission> = setOf(
        Permission.VERIFY_CREDENTIAL,
        Permission.VIEW_AUDIT_TRAIL
    )

    private val STUDENT: Set<Permission> = setOf(
        Permission.VIEW_OWN_RECORD,
        Permission.GENERATE_CERTIFICATE,
        Permission.MANAGE_CONSENT
    )

    private val TEACHER: Set<Permission> = setOf(
        Permission.VIEW_STUDENT_REGISTER,
        Permission.RECORD_ATTENDANCE,
        Permission.RECORD_MARKS,
        Permission.VIEW_AUDIT_TRAIL
    )

    private val PARENT: Set<Permission> = setOf(
        Permission.VIEW_PARENT_PORTAL,
        Permission.VIEW_OWN_RECORD
    )

    /**
     * The permissions granted to a role.
     */
    fun permissionsFor(role: UserRole): Set<Permission> = when (role) {
        UserRole.AICTE_DIRECTORATE -> DIRECTORATE
        UserRole.INSTITUTION -> INSTITUTION
        UserRole.VERIFIER -> VERIFIER
        UserRole.STUDENT -> STUDENT
        UserRole.TEACHER -> TEACHER
        UserRole.PARENT -> PARENT
    }

    /**
     * Whether [role] may exercise [permission].
     */
    fun can(role: UserRole, permission: Permission): Boolean =
        permissionsFor(role).contains(permission)

    /**
     * Whether [role] may exercise any of [permissions].
     */
    fun canAny(role: UserRole, permissions: Collection<Permission>): Boolean =
        permissions.any { can(role, it) }

    /**
     * The permissions that [role] is **not** allowed to exercise. Useful to
     * explain a refusal in the UI instead of silently hiding a control.
     */
    fun deniedFor(role: UserRole): Set<Permission> =
        Permission.entries.toSet() - permissionsFor(role)
}
