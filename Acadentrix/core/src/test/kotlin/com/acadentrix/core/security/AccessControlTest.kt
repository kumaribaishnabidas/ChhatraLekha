package com.acadentrix.core.security

import com.acadentrix.core.model.UserRole
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Behaviour of the role-based access-control matrix.
 */
class AccessControlTest {

    @Test
    fun theDirectorateSeesTheNationalPicture() {
        val role = UserRole.AICTE_DIRECTORATE
        assertTrue(AccessControl.can(role, Permission.VIEW_NATIONAL_DASHBOARD))
        assertTrue(AccessControl.can(role, Permission.REVIEW_ANOMALIES))
        assertTrue(AccessControl.can(role, Permission.VIEW_COMPLIANCE_MATRIX))
        assertTrue(AccessControl.can(role, Permission.VIEW_AUDIT_TRAIL))
    }

    @Test
    fun theDirectorateCannotOnboardStudents() {
        val role = UserRole.AICTE_DIRECTORATE
        assertFalse(AccessControl.can(role, Permission.ONBOARD_STUDENTS))
        assertFalse(AccessControl.can(role, Permission.IMPORT_CSV))
        assertFalse(AccessControl.can(role, Permission.VERIFY_CREDENTIAL))
    }

    @Test
    fun anInstitutionOnboardsButCannotAuditTheNation() {
        val role = UserRole.INSTITUTION
        assertTrue(AccessControl.can(role, Permission.ONBOARD_STUDENTS))
        assertTrue(AccessControl.can(role, Permission.IMPORT_CSV))
        assertTrue(AccessControl.can(role, Permission.VIEW_STUDENT_REGISTER))
        assertFalse(AccessControl.can(role, Permission.VIEW_NATIONAL_DASHBOARD))
        assertFalse(AccessControl.can(role, Permission.REVIEW_ANOMALIES))
    }

    @Test
    fun aVerifierMayOnlyVerify() {
        val role = UserRole.VERIFIER
        assertTrue(AccessControl.can(role, Permission.VERIFY_CREDENTIAL))
        assertFalse(AccessControl.can(role, Permission.ONBOARD_STUDENTS))
        assertFalse(AccessControl.can(role, Permission.EXPORT_REPORTS))
        assertFalse(AccessControl.can(role, Permission.VIEW_OWN_RECORD))
    }

    @Test
    fun aStudentSeesOnlyTheirOwnRecord() {
        val role = UserRole.STUDENT
        assertTrue(AccessControl.can(role, Permission.VIEW_OWN_RECORD))
        assertTrue(AccessControl.can(role, Permission.GENERATE_CERTIFICATE))
        assertFalse(AccessControl.can(role, Permission.VIEW_STUDENT_REGISTER))
        assertFalse(AccessControl.can(role, Permission.EXPORT_REPORTS))
    }

    @Test
    fun noRoleCanDoEverything() {
        UserRole.entries.forEach { role ->
            assertFalse(
                "role ${role.name} must not hold every permission",
                AccessControl.permissionsFor(role).size == Permission.entries.size
            )
        }
    }

    @Test
    fun theDeniedSetIsTheComplementOfTheGrantedSet() {
        UserRole.entries.forEach { role ->
            assertEquals(
                Permission.entries.toSet() - AccessControl.permissionsFor(role),
                AccessControl.deniedFor(role)
            )
        }
    }

    @Test
    fun canAnyMatchesWhenAtLeastOnePermissionIsGranted() {
        assertTrue(
            AccessControl.canAny(
                UserRole.VERIFIER,
                listOf(Permission.ONBOARD_STUDENTS, Permission.VERIFY_CREDENTIAL)
            )
        )
        assertFalse(
            AccessControl.canAny(
                UserRole.VERIFIER,
                listOf(Permission.ONBOARD_STUDENTS, Permission.EXPORT_REPORTS)
            )
        )
    }
}
