"""Role-based access control.

The matrix below is the single source of truth for who may do what, and it is
the Python counterpart of the Kotlin ``AccessControl`` object in the Android
client. The server and the mobile app therefore enforce exactly the same
rules.
"""

from __future__ import annotations

from enum import Enum
from typing import Iterable

from app.core.security import (
    ROLE_ACADEMIC_ADMIN,
    ROLE_AICTE,
    ROLE_INSTITUTION,
    ROLE_PARENT,
    ROLE_PLATFORM_OPERATOR,
    ROLE_STUDENT,
    ROLE_TEACHER,
    ROLE_VERIFIER,
)


class Permission(str, Enum):
    """A capability that an authenticated principal may exercise."""

    VIEW_NATIONAL_DASHBOARD = "view_national_dashboard"
    REVIEW_ANOMALIES = "review_anomalies"
    VIEW_AUDIT_TRAIL = "view_audit_trail"
    VIEW_COMPLIANCE_MATRIX = "view_compliance_matrix"
    ONBOARD_STUDENTS = "onboard_students"
    IMPORT_CSV = "import_csv"
    VIEW_INSTITUTION_DASHBOARD = "view_institution_dashboard"
    VIEW_STUDENT_REGISTER = "view_student_register"
    VIEW_OWN_RECORD = "view_own_record"
    MANAGE_CONSENT = "manage_consent"
    VERIFY_CREDENTIAL = "verify_credential"
    GENERATE_CERTIFICATE = "generate_certificate"
    EXPORT_REPORTS = "export_reports"
    PREVIEW_CORRECTION = "preview_correction"
    APPLY_CORRECTION = "apply_correction"
    VIEW_IMPACTS = "view_impacts"
    REVIEW_TASKS = "review_tasks"
    ISSUE_OWN_TOKEN = "issue_own_token"

    # Connected Campus (Schools and Colleges) MVP capabilities:
    MANAGE_ACADEMIC_SETUP = "manage_academic_setup"
    RECORD_ATTENDANCE = "record_attendance"
    VIEW_ATTENDANCE = "view_attendance"
    RECORD_MARKS = "record_marks"
    PUBLISH_RESULTS = "publish_results"
    VIEW_RESULTS = "view_results"
    MANAGE_ANNOUNCEMENTS = "manage_announcements"
    VIEW_ANNOUNCEMENTS = "view_announcements"
    VIEW_PARENT_PORTAL = "view_parent_portal"
    MANAGE_INSTITUTION_SETTINGS = "manage_institution_settings"


_DIRECTORATE = frozenset(
    {
        Permission.VIEW_NATIONAL_DASHBOARD,
        Permission.REVIEW_ANOMALIES,
        Permission.VIEW_AUDIT_TRAIL,
        Permission.VIEW_COMPLIANCE_MATRIX,
        Permission.EXPORT_REPORTS,
        Permission.VERIFY_CREDENTIAL,
        Permission.PREVIEW_CORRECTION,
        Permission.APPLY_CORRECTION,
        Permission.VIEW_IMPACTS,
        Permission.REVIEW_TASKS,
        Permission.VIEW_ANNOUNCEMENTS,
        Permission.MANAGE_ANNOUNCEMENTS,
    }
)

_INSTITUTION = frozenset(
    {
        Permission.VIEW_INSTITUTION_DASHBOARD,
        Permission.VIEW_STUDENT_REGISTER,
        Permission.ONBOARD_STUDENTS,
        Permission.IMPORT_CSV,
        Permission.MANAGE_CONSENT,
        Permission.GENERATE_CERTIFICATE,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_AUDIT_TRAIL,
        Permission.PREVIEW_CORRECTION,
        Permission.APPLY_CORRECTION,
        Permission.VIEW_IMPACTS,
        Permission.REVIEW_TASKS,
        Permission.MANAGE_ACADEMIC_SETUP,
        Permission.RECORD_ATTENDANCE,
        Permission.VIEW_ATTENDANCE,
        Permission.RECORD_MARKS,
        Permission.PUBLISH_RESULTS,
        Permission.VIEW_RESULTS,
        Permission.MANAGE_ANNOUNCEMENTS,
        Permission.VIEW_ANNOUNCEMENTS,
        Permission.MANAGE_INSTITUTION_SETTINGS,
    }
)

_ACADEMIC_ADMIN = frozenset(
    {
        Permission.VIEW_INSTITUTION_DASHBOARD,
        Permission.VIEW_STUDENT_REGISTER,
        Permission.ONBOARD_STUDENTS,
        Permission.MANAGE_ACADEMIC_SETUP,
        Permission.RECORD_ATTENDANCE,
        Permission.VIEW_ATTENDANCE,
        Permission.PUBLISH_RESULTS,
        Permission.VIEW_RESULTS,
        Permission.MANAGE_ANNOUNCEMENTS,
        Permission.VIEW_ANNOUNCEMENTS,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_AUDIT_TRAIL,
    }
)

_TEACHER = frozenset(
    {
        Permission.VIEW_ATTENDANCE,
        Permission.RECORD_ATTENDANCE,
        Permission.RECORD_MARKS,
        Permission.VIEW_RESULTS,
        Permission.VIEW_ANNOUNCEMENTS,
        Permission.MANAGE_ANNOUNCEMENTS,
    }
)

_VERIFIER = frozenset(
    {
        Permission.VERIFY_CREDENTIAL,
        Permission.VIEW_AUDIT_TRAIL,
    }
)

_STUDENT = frozenset(
    {
        Permission.VIEW_OWN_RECORD,
        Permission.GENERATE_CERTIFICATE,
        Permission.MANAGE_CONSENT,
        Permission.ISSUE_OWN_TOKEN,
        Permission.VIEW_ATTENDANCE,
        Permission.VIEW_RESULTS,
        Permission.VIEW_ANNOUNCEMENTS,
    }
)

_PARENT = frozenset(
    {
        Permission.VIEW_PARENT_PORTAL,
        Permission.VIEW_ATTENDANCE,
        Permission.VIEW_RESULTS,
        Permission.VIEW_ANNOUNCEMENTS,
    }
)

ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    ROLE_AICTE: _DIRECTORATE,
    ROLE_PLATFORM_OPERATOR: _DIRECTORATE,
    ROLE_INSTITUTION: _INSTITUTION,
    ROLE_ACADEMIC_ADMIN: _ACADEMIC_ADMIN,
    ROLE_TEACHER: _TEACHER,
    ROLE_VERIFIER: _VERIFIER,
    ROLE_STUDENT: _STUDENT,
    ROLE_PARENT: _PARENT,
}

ROLE_LABELS: dict[str, str] = {
    ROLE_AICTE: "Platform Operator / Directorate",
    ROLE_PLATFORM_OPERATOR: "Platform Operator",
    ROLE_INSTITUTION: "Institution Owner / Admin",
    ROLE_ACADEMIC_ADMIN: "Academic Administrator",
    ROLE_TEACHER: "Teacher / Faculty",
    ROLE_VERIFIER: "Credential Verifier",
    ROLE_STUDENT: "Student",
    ROLE_PARENT: "Parent / Guardian",
}


def permissions_for(role: str) -> frozenset[Permission]:
    """The permissions granted to a role."""
    return ROLE_PERMISSIONS.get(role, frozenset())


def has_permission(role: str, permission: Permission | str) -> bool:
    """Whether the role may exercise the permission."""
    try:
        resolved = Permission(permission)
    except ValueError:
        return False
    return resolved in permissions_for(role)


def has_any_permission(role: str, permissions: Iterable[Permission | str]) -> bool:
    """Whether the role may exercise at least one of the permissions."""
    return any(has_permission(role, permission) for permission in permissions)


def denied_for(role: str) -> frozenset[Permission]:
    """The permissions the role is *not* allowed to exercise."""
    return frozenset(Permission) - permissions_for(role)
