"""Batch admission CSV ingestion.

A port of the Kotlin ``CsvParser`` / ``CsvIngestionValidator`` so that the
same spreadsheet that the mobile app accepts is accepted by the server, with
the same row-level verdicts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Iterable, Sequence

from app.models.enums import AdmissionQuota
from app.services import apaar_validator

TEMPLATE = """APAAR_ID,Full_Name,DOB,Gender,Roll_No,Program_Code,Category,Nationality,Doc_Number
984210357890,Aakash Verma,2004-03-12,Male,CSE-24-010,BTECH_CSE,REGULAR_MERIT,Indian,
984210357891,Sanya Kapoor,2005-01-20,Female,CSE-24-011,BTECH_CSE,SUPERNUMERARY_TFW,Indian,
984210357892,Rehan Qureshi,2004-11-05,Male,CSE-24-012,BTECH_CSE,SUPERNUMERARY_NRI,Indian,
984210357893,Mei Ling Chow,2004-06-30,Female,CSE-24-013,BTECH_CSE,SUPERNUMERARY_FN,Chinese,P1234567
"""

REQUIRED_COLUMNS = ("APAAR_ID", "FULL_NAME", "PROGRAM_CODE", "CATEGORY")

ALIASES = {
    "apaar_id": "APAAR_ID",
    "apaar": "APAAR_ID",
    "apaarid": "APAAR_ID",
    "aadhaar": "APAAR_ID",
    "full_name": "FULL_NAME",
    "name": "FULL_NAME",
    "student_name": "FULL_NAME",
    "dob": "DOB",
    "date_of_birth": "DOB",
    "gender": "GENDER",
    "sex": "GENDER",
    "roll_no": "ROLL_NO",
    "roll_number": "ROLL_NO",
    "institute_roll_no": "ROLL_NO",
    "program_code": "PROGRAM_CODE",
    "programme_code": "PROGRAM_CODE",
    "program": "PROGRAM_CODE",
    "category": "CATEGORY",
    "quota": "CATEGORY",
    "admission_quota": "CATEGORY",
    "nationality": "NATIONALITY",
    "doc_number": "DOC_NUMBER",
    "passport_no": "DOC_NUMBER",
    "document_number": "DOC_NUMBER",
    "social_category": "SOCIAL_CATEGORY",
    "admission_date": "ADMISSION_DATE",
    "contact_email": "CONTACT_EMAIL",
    "contact_phone": "CONTACT_PHONE",
    "state_of_domicile": "STATE_OF_DOMICILE",
    "academic_year": "ACADEMIC_YEAR",
    "institution_id": "INSTITUTION_ID",
}


class RowIssueSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"


@dataclass
class RowIssue:
    """One issue detected on a CSV row."""

    code: str
    severity: RowIssueSeverity
    message: str


@dataclass
class CsvStudentRow:
    """A parsed CSV row together with its validation outcome."""

    line_number: int
    apaar_id: str
    full_name: str
    dob: str
    gender: str
    roll_no: str
    program_code: str
    category: str
    nationality: str
    doc_number: str
    social_category: str = ""
    admission_date: str = ""
    academic_year: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    state_of_domicile: str = ""
    raw: str = ""
    issues: list[RowIssue] = field(default_factory=list)

    @property
    def critical_issues(self) -> list[RowIssue]:
        return [issue for issue in self.issues if issue.severity == RowIssueSeverity.CRITICAL]

    @property
    def warning_issues(self) -> list[RowIssue]:
        return [issue for issue in self.issues if issue.severity == RowIssueSeverity.WARNING]

    @property
    def is_blocked(self) -> bool:
        return bool(self.critical_issues)

    @property
    def is_clean(self) -> bool:
        return not self.issues

    @property
    def quota(self) -> AdmissionQuota | None:
        return AdmissionQuota.from_code(self.category)


@dataclass
class ProgramImpact:
    """Programme-level seat impact produced by an incoming batch."""

    program_code: str
    program_name: str
    approved_intake: int
    existing_regular: int
    incoming_regular: int
    existing_supernumerary: int
    incoming_supernumerary: int
    cap_messages: list[str] = field(default_factory=list)

    @property
    def projected_regular(self) -> int:
        return self.existing_regular + self.incoming_regular

    @property
    def projected_total(self) -> int:
        return self.projected_regular + self.existing_supernumerary + self.incoming_supernumerary

    @property
    def regular_overflow(self) -> int:
        return max(self.projected_regular - self.approved_intake, 0)


@dataclass
class CsvIngestionReport:
    """Full outcome of a batch ingestion preview."""

    rows: list[CsvStudentRow] = field(default_factory=list)
    header_errors: list[str] = field(default_factory=list)
    program_impacts: list[ProgramImpact] = field(default_factory=list)
    unknown_programs: list[str] = field(default_factory=list)

    @property
    def total_rows(self) -> int:
        return len(self.rows)

    @property
    def valid_rows(self) -> int:
        return sum(
            1
            for row in self.rows
            if not any(issue.severity == RowIssueSeverity.CRITICAL for issue in row.issues)
        )

    @property
    def clean_rows(self) -> int:
        return sum(1 for row in self.rows if row.is_clean)

    @property
    def critical_rows(self) -> int:
        return sum(1 for row in self.rows if row.critical_issues)

    @property
    def warning_rows(self) -> int:
        return sum(
            1
            for row in self.rows
            if row.warning_issues and not row.critical_issues
        )

    @property
    def duplicate_rows(self) -> int:
        return sum(1 for row in self.rows if any(issue.code == "DUPLICATE" for issue in row.issues))

    @property
    def committable_rows(self) -> list[CsvStudentRow]:
        return [
            row
            for row in self.rows
            if not any(issue.severity == RowIssueSeverity.CRITICAL for issue in row.issues)
        ]

    @property
    def is_empty(self) -> bool:
        return not self.rows


@dataclass
class CsvValidationContext:
    """Context required to validate an incoming batch against the live registry."""

    programs: Sequence = field(default_factory=tuple)
    existing_apaar_ids: set[str] = field(default_factory=set)
    existing_regular_counts: dict[str, int] = field(default_factory=dict)
    existing_supernumerary_counts: dict[str, int] = field(default_factory=dict)
    existing_nri_counts: dict[str, int] = field(default_factory=dict)
    existing_oci_fn_counts: dict[str, int] = field(default_factory=dict)
    existing_tfw_counts: dict[str, int] = field(default_factory=dict)
    existing_pmsss_counts: dict[str, int] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> "CsvValidationContext":
        return cls()


# ------------------------------------------------------------------- parser


def parse_csv(text: str) -> tuple[list[str], list[list[str]]]:
    """Minimal RFC-4180 style reader that tolerates quoted fields and a BOM."""
    clean = (text or "").lstrip("\ufeff")
    records: list[list[str]] = []
    current: list[str] = []
    field_chars: list[str] = []
    in_quotes = False
    index = 0

    def commit_field() -> None:
        current.append("".join(field_chars))
        field_chars.clear()

    def commit_record() -> None:
        commit_field()
        if any(value.strip() for value in current) or len(current) > 1:
            records.append(list(current))
        current.clear()

    while index < len(clean):
        char = clean[index]
        if in_quotes and char == '"' and index + 1 < len(clean) and clean[index + 1] == '"':
            field_chars.append('"')
            index += 1
        elif char == '"':
            in_quotes = not in_quotes
        elif not in_quotes and char == ",":
            commit_field()
        elif not in_quotes and char in "\n\r":
            if char == "\r" and index + 1 < len(clean) and clean[index + 1] == "\n":
                index += 1
            commit_record()
        else:
            field_chars.append(char)
        index += 1

    if field_chars or current:
        commit_record()

    if not records:
        return [], []
    return records[0], records[1:]


# ---------------------------------------------------------------- validator


def validate_csv(text: str, context: CsvValidationContext) -> CsvIngestionReport:
    """Validate a batch CSV against the live registry."""
    header_row, data_rows = parse_csv(text)
    header_errors: list[str] = []

    if not header_row:
        return CsvIngestionReport(
            header_errors=[
                "No header row found. Upload a CSV starting with the column header line."
            ]
        )

    header_index: dict[str, int] = {}
    for index, raw in enumerate(header_row):
        key = raw.strip().lower().replace(" ", "_")
        canonical = ALIASES.get(key, raw.strip().upper())
        header_index[canonical] = index

    for column in REQUIRED_COLUMNS:
        if column not in header_index:
            header_errors.append(f"Missing mandatory column '{column}'.")

    if header_errors:
        return CsvIngestionReport(header_errors=header_errors)

    programs_by_code = {program.program_id.upper(): program for program in context.programs}
    rows: list[CsvStudentRow] = []

    for row_index, fields in enumerate(data_rows):
        line_number = row_index + 2

        def value(column: str, fields=fields) -> str:
            position = header_index.get(column)
            if position is None or position >= len(fields):
                return ""
            return fields[position].strip()

        apaar_id = value("APAAR_ID")
        full_name = value("FULL_NAME")
        dob_raw = value("DOB")
        gender = value("GENDER")
        roll_no = value("ROLL_NO")
        program_code = value("PROGRAM_CODE").upper()
        category = value("CATEGORY")
        nationality = value("NATIONALITY")
        doc_number = value("DOC_NUMBER")
        social_category = value("SOCIAL_CATEGORY")
        admission_date = value("ADMISSION_DATE")
        academic_year = value("ACADEMIC_YEAR")
        contact_email = value("CONTACT_EMAIL")
        contact_phone = value("CONTACT_PHONE")
        state_of_domicile = value("STATE_OF_DOMICILE")

        issues: list[RowIssue] = []

        validation = apaar_validator.validate(apaar_id)
        if not validation.is_structurally_valid:
            issues.append(
                RowIssue(
                    "INVALID_APAAR",
                    RowIssueSeverity.CRITICAL,
                    validation.errors[0] if validation.errors else "Invalid APAAR ID.",
                )
            )
        else:
            if not validation.is_checksum_valid:
                issues.append(
                    RowIssue(
                        "LUHN_ADVISORY",
                        RowIssueSeverity.WARNING,
                        "Luhn check-digit advisory: checksum does not match (non-blocking).",
                    )
                )
            if apaar_id in context.existing_apaar_ids:
                issues.append(
                    RowIssue(
                        "DUPLICATE",
                        RowIssueSeverity.CRITICAL,
                        "APAAR ID is already enrolled in the national registry.",
                    )
                )

        if not full_name:
            issues.append(
                RowIssue("MISSING_NAME", RowIssueSeverity.CRITICAL, "Full name is mandatory.")
            )

        normalised_dob = normalise_date(dob_raw)
        if normalised_dob is None:
            issues.append(
                RowIssue(
                    "INVALID_DOB",
                    RowIssueSeverity.CRITICAL,
                    "Date of birth must be a valid calendar date (yyyy-MM-dd).",
                )
            )

        from app.models.enums import Gender

        if gender and Gender.from_code(gender) is None:
            issues.append(
                RowIssue(
                    "INVALID_GENDER",
                    RowIssueSeverity.WARNING,
                    f"Unrecognised gender value '{gender}'.",
                )
            )

        quota = AdmissionQuota.from_code(category)
        if quota is None:
            issues.append(
                RowIssue(
                    "INVALID_CATEGORY",
                    RowIssueSeverity.CRITICAL,
                    f"Unknown quota category '{category}'.",
                )
            )

        program = programs_by_code.get(program_code)
        if program is None:
            issues.append(
                RowIssue(
                    "UNKNOWN_PROGRAM",
                    RowIssueSeverity.CRITICAL,
                    f"Programme code '{program_code}' is not sanctioned for this institution.",
                )
            )

        if quota is not None and quota.requires_foreign_docs:
            if quota == AdmissionQuota.FN and not doc_number:
                issues.append(
                    RowIssue(
                        "MISSING_PASSPORT",
                        RowIssueSeverity.WARNING,
                        "Foreign National admission without a passport / document number.",
                    )
                )
        elif (
            quota is not None
            and quota.is_regular
            and nationality
            and nationality.lower() != "indian"
        ):
            issues.append(
                RowIssue(
                    "CATEGORY_MISMATCH",
                    RowIssueSeverity.WARNING,
                    f"Regular-seat quota declared against a non-Indian nationality ({nationality}).",
                )
            )

        rows.append(
            CsvStudentRow(
                line_number=line_number,
                apaar_id=apaar_id,
                full_name=full_name,
                dob=normalised_dob or dob_raw,
                gender=gender,
                roll_no=roll_no,
                program_code=program_code,
                category=category,
                nationality=nationality,
                doc_number=doc_number,
                social_category=social_category,
                admission_date=normalise_date(admission_date) or admission_date,
                academic_year=academic_year,
                contact_email=contact_email,
                contact_phone=contact_phone,
                state_of_domicile=state_of_domicile,
                raw=",".join(fields),
                issues=issues,
            )
        )

    # An identifier repeated inside the same batch blocks *every* row that
    # carries it: there is no way to tell which copy is authoritative.
    batch_counts: dict[str, int] = {}
    for row in rows:
        if row.apaar_id:
            batch_counts[row.apaar_id] = batch_counts.get(row.apaar_id, 0) + 1

    resolved: list[CsvStudentRow] = []
    for row in rows:
        if row.apaar_id and batch_counts.get(row.apaar_id, 0) > 1:
            row.issues.append(
                RowIssue(
                    "DUPLICATE",
                    RowIssueSeverity.CRITICAL,
                    "APAAR ID is duplicated inside this batch.",
                )
            )
        resolved.append(row)

    impacts = _compute_impacts(resolved, context)
    unknown = sorted(
        {
            row.program_code
            for row in resolved
            if row.program_code and row.program_code not in programs_by_code
        }
    )

    return CsvIngestionReport(
        rows=resolved,
        header_errors=[],
        program_impacts=impacts,
        unknown_programs=unknown,
    )


def _compute_impacts(
    rows: Iterable[CsvStudentRow], context: CsvValidationContext
) -> list[ProgramImpact]:
    committable = [
        row
        for row in rows
        if not any(issue.severity == RowIssueSeverity.CRITICAL for issue in row.issues)
    ]
    by_program: dict[str, list[CsvStudentRow]] = {}
    for row in committable:
        by_program.setdefault(row.program_code.upper(), []).append(row)

    impacts: list[ProgramImpact] = []
    for code, program_rows in by_program.items():
        program = next(
            (p for p in context.programs if p.program_id.upper() == code), None
        )
        if program is None:
            continue
        incoming_regular = sum(
            1 for row in program_rows if row.quota is not None and row.quota.is_regular
        )
        incoming_super = sum(
            1
            for row in program_rows
            if row.quota is not None and row.quota.is_supernumerary
        )
        existing_regular = context.existing_regular_counts.get(program.program_id, 0)
        existing_super = context.existing_supernumerary_counts.get(program.program_id, 0)

        incoming_nri = sum(1 for row in program_rows if row.quota == AdmissionQuota.NRI)
        incoming_oci_fn = sum(
            1
            for row in program_rows
            if row.quota in (AdmissionQuota.OCI, AdmissionQuota.FN)
        )
        incoming_tfw = sum(1 for row in program_rows if row.quota == AdmissionQuota.TFW)
        incoming_pmsss = sum(1 for row in program_rows if row.quota == AdmissionQuota.PMSSS)

        messages: list[str] = []
        projected_regular = existing_regular + incoming_regular
        if projected_regular > program.approved_intake:
            messages.append(
                f"Regular intake breach: {projected_regular} projected against "
                f"{program.approved_intake} sanctioned seats."
            )
        nri_total = context.existing_nri_counts.get(program.program_id, 0) + incoming_nri
        if nri_total > program.max_supernumerary_nri:
            messages.append(
                f"NRI supernumerary ceiling exceeded: {nri_total} against "
                f"{program.max_supernumerary_nri} (5% rule)."
            )
        oci_fn_total = context.existing_oci_fn_counts.get(program.program_id, 0) + incoming_oci_fn
        if oci_fn_total > program.max_supernumerary_fn_oci:
            messages.append(
                f"OCI / FN supernumerary ceiling exceeded: {oci_fn_total} against "
                f"{program.max_supernumerary_fn_oci} (15% rule)."
            )
        tfw_total = context.existing_tfw_counts.get(program.program_id, 0) + incoming_tfw
        if tfw_total > program.max_supernumerary_tfw:
            messages.append(
                f"TFW supernumerary ceiling exceeded: {tfw_total} against "
                f"{program.max_supernumerary_tfw} (5% rule)."
            )
        pmsss_total = context.existing_pmsss_counts.get(program.program_id, 0) + incoming_pmsss
        if pmsss_total > program.max_pmsss:
            messages.append(
                f"PMSSS ceiling exceeded: {pmsss_total} against {program.max_pmsss}."
            )

        impacts.append(
            ProgramImpact(
                program_code=code,
                program_name=program.program_name,
                approved_intake=program.approved_intake,
                existing_regular=existing_regular,
                incoming_regular=incoming_regular,
                existing_supernumerary=existing_super,
                incoming_supernumerary=incoming_super,
                cap_messages=messages,
            )
        )
    return impacts


def normalise_date(raw: str) -> str | None:
    """Normalise a date to ``yyyy-MM-dd``."""
    value = (raw or "").strip()
    if not value:
        return None
    parts = [part.strip() for part in value.replace("/", "-").replace(".", "-").split("-")]
    if len(parts) != 3:
        return None
    try:
        if len(parts[0]) == 4:
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        else:
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            if year < 100:
                year += 2000
    except ValueError:
        return None
    if not _is_valid_date(year, month, day):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def _is_valid_date(year: int, month: int, day: int) -> bool:
    if not 1950 <= year <= date.today().year or not 1 <= month <= 12:
        return False
    if month in (1, 3, 5, 7, 8, 10, 12):
        max_day = 31
    elif month in (4, 6, 9, 11):
        max_day = 30
    else:
        max_day = 29 if _is_leap(year) else 28
    return 1 <= day <= max_day


def _is_leap(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or year % 400 == 0
