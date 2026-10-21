"""Deterministic CSV writers for the regulatory reports.

The student export is deliberately **round-trip compatible** with
``csv_ingestion``: the columns written here can be pasted straight back into
the batch importer without any column mapping.

Quoting follows RFC 4180: a field is quoted when it contains a comma, a
double quote or a line break, and embedded quotes are doubled.
"""

from __future__ import annotations

from typing import Iterable, Sequence

STUDENT_COLUMNS = [
    "APAAR_ID",
    "FULL_NAME",
    "DOB",
    "GENDER",
    "ROLL_NO",
    "PROGRAM_CODE",
    "CATEGORY",
    "NATIONALITY",
    "DOC_NUMBER",
    "SOCIAL_CATEGORY",
    "ADMISSION_DATE",
    "ACADEMIC_YEAR",
    "INSTITUTION_ID",
    "CONTACT_EMAIL",
    "CONTACT_PHONE",
    "STATE_OF_DOMICILE",
    "VERIFICATION_STATUS",
]

ANOMALY_COLUMNS = [
    "APAAR_ID",
    "INSTITUTION_ID",
    "PROGRAM_CODE",
    "ANOMALY_TYPE",
    "SEVERITY",
    "DETAILS",
    "DETECTED_AT",
]

AUDIT_COLUMNS = [
    "TIMESTAMP",
    "ACTOR",
    "ACTION",
    "SUBJECT",
    "CATEGORY",
    "DETAILS",
    "PREV_HASH",
    "HASH",
]

PROGRAM_COLUMNS = [
    "INSTITUTION_ID",
    "PROGRAM_CODE",
    "PROGRAM_NAME",
    "LEVEL",
    "APPROVED_INTAKE",
    "ENROLLED",
    "REGULAR_ENROLLED",
    "SUPERNUMERARY_ENROLLED",
    "UTILISATION_PERCENT",
    "NRI",
    "OCI_FN",
    "TFW",
    "PMSSS",
]


def escape(value: str | None) -> str:
    """Quote a single CSV field following RFC 4180."""
    raw = "" if value is None else str(value)
    if any(char in raw for char in (",", '"', "\n", "\r")):
        return '"' + raw.replace('"', '""') + '"'
    return raw


def _row(values: Sequence) -> str:
    return ",".join(escape(value) for value in values)


def students(rows: Iterable, include_header: bool = True) -> str:
    """Render the student register as CSV."""
    lines: list[str] = []
    if include_header:
        lines.append(",".join(STUDENT_COLUMNS))
    for student in rows:
        quota = getattr(student, "admission_quota", None)
        gender = getattr(student, "gender", None)
        status = getattr(student, "verification_status", None)
        social = getattr(student, "social_category", None)
        lines.append(
            _row(
                [
                    student.apaar_id,
                    student.student_name,
                    student.date_of_birth,
                    getattr(gender, "value", gender),
                    student.student_institute_roll_no,
                    student.program_id,
                    getattr(quota, "value", quota),
                    student.nationality,
                    student.passport_number or "",
                    getattr(social, "value", social),
                    student.admission_date or "",
                    student.academic_year,
                    student.institution_id,
                    student.contact_email or "",
                    student.contact_phone or "",
                    student.state_of_domicile or "",
                    getattr(status, "value", status),
                ]
            )
        )
    return "\n".join(lines)


def anomalies(rows: Iterable, include_header: bool = True) -> str:
    """Render the anomaly register as CSV."""
    lines: list[str] = []
    if include_header:
        lines.append(",".join(ANOMALY_COLUMNS))
    for anomaly in rows:
        anomaly_type = getattr(anomaly, "anomaly_type", None)
        severity = getattr(anomaly, "severity", None)
        detected_at = getattr(anomaly, "detected_at", None)
        lines.append(
            _row(
                [
                    anomaly.student_apaar_id,
                    anomaly.institution_id,
                    anomaly.program_id or "",
                    getattr(anomaly_type, "value", anomaly_type),
                    getattr(severity, "value", severity),
                    anomaly.details,
                    detected_at.isoformat() if hasattr(detected_at, "isoformat") else (detected_at or ""),
                ]
            )
        )
    return "\n".join(lines)


def audit_trail(rows: Iterable, include_header: bool = True) -> str:
    """Render the audit trail as CSV, including the chain hashes."""
    lines: list[str] = []
    if include_header:
        lines.append(",".join(AUDIT_COLUMNS))
    for entry in rows:
        timestamp = getattr(entry, "timestamp", None)
        lines.append(
            _row(
                [
                    timestamp.isoformat() if hasattr(timestamp, "isoformat") else (timestamp or ""),
                    entry.actor,
                    entry.action,
                    entry.subject,
                    entry.category,
                    entry.details,
                    entry.prev_hash,
                    entry.hash,
                ]
            )
        )
    return "\n".join(lines)


def programme_utilisation(rows: Iterable, include_header: bool = True) -> str:
    """Render the programme utilisation matrix as CSV."""
    lines: list[str] = []
    if include_header:
        lines.append(",".join(PROGRAM_COLUMNS))
    for snapshot in rows:
        program = snapshot.program
        utilisation = snapshot.overall_utilisation * 100
        lines.append(
            _row(
                [
                    program.institution_id,
                    program.program_id,
                    program.program_name,
                    program.program_level,
                    program.approved_intake,
                    snapshot.total_enrolled,
                    snapshot.regular_enrolled,
                    snapshot.supernumerary_enrolled,
                    f"{utilisation:.1f}",
                    snapshot.nri_enrolled,
                    snapshot.oci_fn_enrolled,
                    snapshot.tfw_enrolled,
                    snapshot.pmsss_enrolled,
                ]
            )
        )
    return "\n".join(lines)
