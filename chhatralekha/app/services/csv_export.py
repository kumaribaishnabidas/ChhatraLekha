"""Deterministic CSV writers for the regulatory reports.

The student export is deliberately **round-trip compatible** with
``csv_ingestion``: the columns written here can be pasted straight back into
the batch importer without any column mapping.

Quoting follows RFC 4180: a field is quoted when it contains a comma, a
double quote or a line break, and embedded quotes are doubled.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from app.models.documents import enum_value, field

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
        lines.append(
            _row(
                [
                    field(student, "apaar_id", ""),
                    field(student, "student_name", ""),
                    field(student, "date_of_birth", ""),
                    enum_value(field(student, "gender", "")),
                    field(student, "student_institute_roll_no", ""),
                    field(student, "program_id", ""),
                    enum_value(field(student, "admission_quota", "")),
                    field(student, "nationality", ""),
                    field(student, "passport_number", "") or "",
                    enum_value(field(student, "social_category", "")),
                    field(student, "admission_date", "") or "",
                    field(student, "academic_year", ""),
                    field(student, "institution_id", ""),
                    field(student, "contact_email", "") or "",
                    field(student, "contact_phone", "") or "",
                    field(student, "state_of_domicile", "") or "",
                    enum_value(field(student, "verification_status", "")),
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
        detected_at = field(anomaly, "detected_at", "")
        lines.append(
            _row(
                [
                    field(anomaly, "student_apaar_id", ""),
                    field(anomaly, "institution_id", ""),
                    field(anomaly, "program_id", "") or "",
                    enum_value(field(anomaly, "anomaly_type", "")),
                    enum_value(field(anomaly, "severity", "")),
                    field(anomaly, "details", ""),
                    detected_at.isoformat()
                    if hasattr(detected_at, "isoformat")
                    else (detected_at or ""),
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
        timestamp = field(entry, "timestamp", "")
        lines.append(
            _row(
                [
                    timestamp.isoformat()
                    if hasattr(timestamp, "isoformat")
                    else (timestamp or ""),
                    field(entry, "actor", ""),
                    field(entry, "action", ""),
                    field(entry, "subject", ""),
                    field(entry, "category", ""),
                    field(entry, "details", ""),
                    field(entry, "prev_hash", ""),
                    field(entry, "hash", ""),
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
        program = field(snapshot, "program", {}) or {}
        utilisation = float(field(snapshot, "overall_utilisation", 0.0) or 0.0) * 100
        lines.append(
            _row(
                [
                    field(program, "institution_id", ""),
                    field(program, "program_id", ""),
                    field(program, "program_name", ""),
                    field(program, "program_level", ""),
                    field(program, "approved_intake", 0),
                    field(snapshot, "total_enrolled", 0),
                    field(snapshot, "regular_enrolled", 0),
                    field(snapshot, "supernumerary_enrolled", 0),
                    f"{utilisation:.1f}",
                    field(snapshot, "nri_enrolled", 0),
                    field(snapshot, "oci_fn_enrolled", 0),
                    field(snapshot, "tfw_enrolled", 0),
                    field(snapshot, "pmsss_enrolled", 0),
                ]
            )
        )
    return "\n".join(lines)
