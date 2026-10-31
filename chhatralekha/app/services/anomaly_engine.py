"""Multi-layer regulatory anomaly detection engine.

A faithful port of the Kotlin ``AnomalyEngine``. Ten discrete checks are
executed over the registry snapshot:

1. APAAR syntactic check — 12-digit structure and non-triviality.
2. Cross-institutional multi-enrolment — one APAAR, many institutions.
3. Same-institution duplicate — one APAAR, twice in a single institution.
4. Duplicate institute roll number within one institution.
5. Intake breach check — regular enrolment against sanctioned capacity.
6. Supernumerary ceiling check — NRI / OCI+FN / TFW / PMSSS caps.
7. Documentary consistency for foreign nationals and quota contradictions.
8. Impossible dates — unparseable, future, or enrolment before birth.
9. Missing mandatory fields.
10. Unsanctioned programme — enrolment in a course the institute may not run.

Layers 1-4 are *identity* checks, layers 5-6 are *capacity* checks and layers
7-10 are *data-integrity* checks. Every rule is a pure function of the
snapshot, so the server and the mobile app always reach the same verdict for
the same data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, Protocol, Sequence

from app.models.enums import (
    AdmissionQuota,
    AnomalySeverity,
    AnomalyType,
    Gender,
    InstitutionType,
)
from app.services import apaar_validator

#: Severity is escalated to CRITICAL once a cap is exceeded by more than two seats.
ESCALATION_THRESHOLD = 2

#: No student can plausibly enrol before this age.
MINIMUM_ENROLMENT_AGE = 15

#: The earliest birth year that can be real for a student in the registry.
EARLIEST_PLAUSIBLE_BIRTH_YEAR = 1900


# ---------------------------------------------------------------- protocols


class InstitutionLike(Protocol):
    institution_id: str
    name: str
    institution_type: InstitutionType
    state: str
    city: str
    affiliation_university: str
    approval_year: int
    naac_grade: str


class ProgramIntakeLike(Protocol):
    program_id: str
    institution_id: str
    program_name: str
    program_level: str
    approved_intake: int
    max_supernumerary_nri: int
    max_supernumerary_fn_oci: int
    max_supernumerary_tfw: int
    max_pmsss: int


class StudentLike(Protocol):
    apaar_id: str
    student_name: str
    date_of_birth: str
    gender: Gender
    institution_id: str
    program_id: str
    academic_year: str
    admission_quota: AdmissionQuota
    enrollment_date: str
    student_institute_roll_no: str
    nationality: str
    passport_number: str | None
    visa_validity: str | None
    country_of_origin: str | None
    is_active: bool


# --------------------------------------------------------------- structures


@dataclass
class RegistrySnapshot:
    """A point-in-time view of the whole national registry."""

    institutions: Sequence[InstitutionLike] = field(default_factory=tuple)
    programs: Sequence[ProgramIntakeLike] = field(default_factory=tuple)
    students: Sequence[StudentLike] = field(default_factory=tuple)


@dataclass
class DetectedAnomaly:
    """An anomaly detected by the engine, before it is persisted."""

    student_apaar_id: str
    institution_id: str
    program_id: str | None
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    details: str


@dataclass
class IntakeSnapshot:
    """Real-time utilisation of one programme's sanctioned capacity."""

    program: ProgramIntakeLike
    regular_enrolled: int
    supernumerary_enrolled: int
    total_enrolled: int
    nri_enrolled: int
    oci_fn_enrolled: int
    tfw_enrolled: int
    pmsss_enrolled: int

    @property
    def regular_utilisation(self) -> float:
        if self.program.approved_intake == 0:
            return 0.0
        return self.regular_enrolled / self.program.approved_intake

    @property
    def overall_utilisation(self) -> float:
        if self.program.total_sanctioned == 0:
            return 0.0
        return self.total_enrolled / self.program.total_sanctioned

    @property
    def regular_overflow(self) -> int:
        return max(self.regular_enrolled - self.program.approved_intake, 0)

    @property
    def nri_overflow(self) -> int:
        return max(self.nri_enrolled - self.program.max_supernumerary_nri, 0)

    @property
    def oci_fn_overflow(self) -> int:
        return max(self.oci_fn_enrolled - self.program.max_supernumerary_fn_oci, 0)

    @property
    def tfw_overflow(self) -> int:
        return max(self.tfw_enrolled - self.program.max_supernumerary_tfw, 0)

    @property
    def pmsss_overflow(self) -> int:
        return max(self.pmsss_enrolled - self.program.max_pmsss, 0)

    @property
    def has_breach(self) -> bool:
        return (
            self.regular_overflow > 0
            or self.nri_overflow > 0
            or self.oci_fn_overflow > 0
            or self.tfw_overflow > 0
            or self.pmsss_overflow > 0
        )


# ------------------------------------------------------------------ engine


class AnomalyEngine:
    """Executes every detection layer over a registry snapshot."""

    def evaluate(self, snapshot: RegistrySnapshot) -> list[DetectedAnomaly]:
        """Run all ten layers and return the findings."""
        anomalies: list[DetectedAnomaly] = []
        anomalies += self.detect_unsanctioned_programmes(snapshot)
        anomalies += self.detect_invalid_apaar_format(snapshot)
        anomalies += self.detect_cross_institution_duplicates(snapshot)
        anomalies += self.detect_same_institution_duplicates(snapshot)
        anomalies += self.detect_duplicate_roll_numbers(snapshot)
        anomalies += self.detect_intake_breaches(snapshot)
        anomalies += self.detect_supernumerary_breaches(snapshot)
        anomalies += self.detect_inconsistencies(snapshot)
        anomalies += self.detect_impossible_dates(snapshot)
        anomalies += self.detect_missing_required_fields(snapshot)

        # Dispatch to school rule pack when school institutions or grade levels are present
        has_school = any(
            getattr(inst, "rule_pack", None) == "school_basic"
            or str(getattr(inst, "category", "")).upper() == "SCHOOL"
            or str(getattr(inst, "institution_type", "")).upper() in ("SCHOOL", "K12")
            for inst in getattr(snapshot, "institutions", ())
        ) or any(
            getattr(st, "grade_level", None) is not None
            or getattr(st, "is_minor", None) is not None
            for st in getattr(snapshot, "students", ())
        )
        if has_school:
            from app.services.rule_packs.school_basic import SchoolBasicPack

            anomalies += SchoolBasicPack().evaluate(snapshot)

        return anomalies

    # ------------------------------------------------------------ layer 10

    def detect_unsanctioned_programmes(
        self, snapshot: RegistrySnapshot
    ) -> list[DetectedAnomaly]:
        """A student may only map to a programme the institution is approved for."""
        sanctioned = {
            (program.institution_id, program.program_id) for program in snapshot.programs
        }
        out: list[DetectedAnomaly] = []
        for student in snapshot.students:
            if (student.institution_id, student.program_id) in sanctioned:
                continue
            out.append(
                DetectedAnomaly(
                    student_apaar_id=student.apaar_id,
                    institution_id=student.institution_id,
                    program_id=student.program_id,
                    anomaly_type=AnomalyType.UNSANCTIONED_PROGRAM,
                    severity=AnomalySeverity.CRITICAL,
                    details=(
                        f"Programme code '{student.program_id}' is not approved for institution "
                        f"{student.institution_id}. The enrolment cannot be regularised."
                    ),
                )
            )
        return out

    # ------------------------------------------------------------- layer 1

    def detect_invalid_apaar_format(
        self, snapshot: RegistrySnapshot
    ) -> list[DetectedAnomaly]:
        out: list[DetectedAnomaly] = []
        for student in snapshot.students:
            validation = apaar_validator.validate(student.apaar_id)
            if validation.is_structurally_valid:
                continue
            out.append(
                DetectedAnomaly(
                    student_apaar_id=student.apaar_id,
                    institution_id=student.institution_id,
                    program_id=student.program_id,
                    anomaly_type=AnomalyType.INVALID_APAAR_FORMAT,
                    severity=AnomalySeverity.CRITICAL,
                    details=(
                        validation.errors[0]
                        if validation.errors
                        else f"APAAR ID '{student.apaar_id}' does not conform to the "
                        "12-digit registry structure."
                    ),
                )
            )
        return out

    # ------------------------------------------------------------- layer 2

    def detect_cross_institution_duplicates(
        self, snapshot: RegistrySnapshot
    ) -> list[DetectedAnomaly]:
        active = [student for student in snapshot.students if student.is_active]
        out: list[DetectedAnomaly] = []
        for apaar_id, rows in _group_by(active, lambda s: s.apaar_id).items():
            institution_ids = {row.institution_id for row in rows}
            if len(institution_ids) <= 1:
                continue
            regular_hits = sum(1 for row in rows if row.admission_quota.is_regular)
            severity = (
                AnomalySeverity.CRITICAL if regular_hits >= 2 else AnomalySeverity.HIGH
            )
            for row in rows:
                out.append(
                    DetectedAnomaly(
                        student_apaar_id=apaar_id,
                        institution_id=row.institution_id,
                        program_id=row.program_id,
                        anomaly_type=AnomalyType.DUPLICATE_CROSS_COLLEGE,
                        severity=severity,
                        details=(
                            f"APAAR ID is concurrently active across {len(institution_ids)} "
                            f"institutions ({', '.join(sorted(institution_ids))}). One person "
                            "cannot hold concurrent regular full-time AICTE admissions."
                        ),
                    )
                )
        return out

    # ------------------------------------------------------------- layer 3

    def detect_same_institution_duplicates(
        self, snapshot: RegistrySnapshot
    ) -> list[DetectedAnomaly]:
        active = [student for student in snapshot.students if student.is_active]
        out: list[DetectedAnomaly] = []
        for (institution_id, apaar_id), rows in _group_by(
            active, lambda s: (s.institution_id, s.apaar_id)
        ).items():
            if len(rows) <= 1:
                continue
            programme_count = len({row.program_id for row in rows})
            severity = (
                AnomalySeverity.CRITICAL
                if programme_count > 1
                else AnomalySeverity.HIGH
            )
            for row in rows:
                if programme_count > 1:
                    details = (
                        f"APAAR ID is enrolled {len(rows)} times inside institution "
                        f"{institution_id} across {programme_count} different programmes. "
                        "A single student cannot hold two AICTE admissions in the same institute."
                    )
                else:
                    details = (
                        f"APAAR ID appears {len(rows)} times inside institution "
                        f"{institution_id} for the same programme '{row.program_id}'. "
                        "The row has been imported more than once."
                    )
                out.append(
                    DetectedAnomaly(
                        student_apaar_id=apaar_id,
                        institution_id=institution_id,
                        program_id=row.program_id,
                        anomaly_type=AnomalyType.DUPLICATE_SAME_INSTITUTION,
                        severity=severity,
                        details=details,
                    )
                )
        return out

    # ------------------------------------------------------------- layer 4

    def detect_duplicate_roll_numbers(
        self, snapshot: RegistrySnapshot
    ) -> list[DetectedAnomaly]:
        active = [
            student
            for student in snapshot.students
            if student.is_active and (student.student_institute_roll_no or "").strip()
        ]
        out: list[DetectedAnomaly] = []
        for _, rows in _group_by(
            active,
            lambda s: (s.institution_id, s.student_institute_roll_no.strip().upper()),
        ).items():
            apaar_ids = {row.apaar_id for row in rows}
            if len(apaar_ids) <= 1:
                continue
            roll_no = rows[0].student_institute_roll_no.strip()
            institution_id = rows[0].institution_id
            for row in rows:
                out.append(
                    DetectedAnomaly(
                        student_apaar_id=row.apaar_id,
                        institution_id=institution_id,
                        program_id=row.program_id,
                        anomaly_type=AnomalyType.DUPLICATE_ROLL_NUMBER,
                        severity=AnomalySeverity.HIGH,
                        details=(
                            f"Institute roll number '{roll_no}' is held by {len(apaar_ids)} "
                            f"different students in institution {institution_id} "
                            f"({', '.join(sorted(apaar_ids))}). Institute roll numbers must be "
                            "unique within an institution."
                        ),
                    )
                )
        return out

    # ------------------------------------------------------------- layer 5

    def detect_intake_breaches(self, snapshot: RegistrySnapshot) -> list[DetectedAnomaly]:
        out: list[DetectedAnomaly] = []
        for program in snapshot.programs:
            regular = sorted(
                (
                    student
                    for student in snapshot.students
                    if student.is_active
                    and student.institution_id == program.institution_id
                    and student.program_id == program.program_id
                    and student.admission_quota.is_regular
                ),
                key=lambda s: (s.enrollment_date, s.apaar_id),
            )
            overflow = len(regular) - program.approved_intake
            if overflow <= 0:
                continue
            for student in regular[program.approved_intake :]:
                out.append(
                    DetectedAnomaly(
                        student_apaar_id=student.apaar_id,
                        institution_id=program.institution_id,
                        program_id=program.program_id,
                        anomaly_type=AnomalyType.EXCESS_APPROVED_INTAKE,
                        severity=AnomalySeverity.CRITICAL,
                        details=(
                            f"{program.program_name} is over-admitted by {overflow} seat(s): "
                            f"{len(regular)} regular enrolments against a sanctioned intake of "
                            f"{program.approved_intake}."
                        ),
                    )
                )
        return out

    # ------------------------------------------------------------- layer 6

    def detect_supernumerary_breaches(
        self, snapshot: RegistrySnapshot
    ) -> list[DetectedAnomaly]:
        out: list[DetectedAnomaly] = []
        for program in snapshot.programs:
            bucket = [
                student
                for student in snapshot.students
                if student.is_active
                and student.institution_id == program.institution_id
                and student.program_id == program.program_id
            ]

            def flag(
                rows,
                cap: int,
                basis: str,
                citation: str,
                program=program,
            ) -> None:
                overflow = len(rows) - cap
                if overflow <= 0:
                    return
                severity = (
                    AnomalySeverity.CRITICAL
                    if overflow > ESCALATION_THRESHOLD
                    else AnomalySeverity.WARNING
                )
                for student in rows[cap:]:
                    out.append(
                        DetectedAnomaly(
                            student_apaar_id=student.apaar_id,
                            institution_id=program.institution_id,
                            program_id=program.program_id,
                            anomaly_type=AnomalyType.SUPERNUMERARY_BREACH,
                            severity=severity,
                            details=(
                                f"{basis} cap exceeded for {program.program_name}: "
                                f"{len(rows)} admitted against a ceiling of {cap} ({citation})."
                            ),
                        )
                    )

            flag(
                [s for s in bucket if s.admission_quota == AdmissionQuota.NRI],
                program.max_supernumerary_nri,
                "NRI supernumerary",
                "AICTE APH - max 5% of sanctioned intake",
            )
            flag(
                [
                    s
                    for s in bucket
                    if s.admission_quota in (AdmissionQuota.OCI, AdmissionQuota.FN)
                ],
                program.max_supernumerary_fn_oci,
                "OCI / Foreign National supernumerary",
                "AICTE APH - max 15% of sanctioned intake",
            )
            flag(
                [s for s in bucket if s.admission_quota == AdmissionQuota.TFW],
                program.max_supernumerary_tfw,
                "Tuition Fee Waiver supernumerary",
                "AICTE APH - max 5% of sanctioned intake",
            )
            flag(
                [s for s in bucket if s.admission_quota == AdmissionQuota.PMSSS],
                program.max_pmsss,
                "PMSSS",
                "AICTE APH - capped per course / institute",
            )
        return out

    # ------------------------------------------------------------- layer 7

    def detect_inconsistencies(self, snapshot: RegistrySnapshot) -> list[DetectedAnomaly]:
        out: list[DetectedAnomaly] = []
        for student in snapshot.students:
            nationality = (student.nationality or "").strip()
            missing: list[str] = []

            if student.admission_quota == AdmissionQuota.FN:
                if not (student.passport_number or "").strip():
                    missing.append("passport number")
                if not (student.country_of_origin or "").strip():
                    missing.append("country of origin")
                if not (student.visa_validity or "").strip():
                    missing.append("student visa validity")
            if (
                student.admission_quota == AdmissionQuota.OCI
                and nationality
                and not is_indian_nationality(nationality)
                and "OCI" not in nationality.upper()
            ):
                missing.append("OCI nationality declaration")

            if missing:
                out.append(
                    DetectedAnomaly(
                        student_apaar_id=student.apaar_id,
                        institution_id=student.institution_id,
                        program_id=student.program_id,
                        anomaly_type=AnomalyType.INCONSISTENT_CATEGORY,
                        severity=AnomalySeverity.WARNING,
                        details=(
                            f"Missing or contradictory documentation for "
                            f"{student.admission_quota.label}: {', '.join(missing)}."
                        ),
                    )
                )

            contradiction = quota_nationality_conflict(
                student.admission_quota, nationality
            )
            if contradiction:
                out.append(
                    DetectedAnomaly(
                        student_apaar_id=student.apaar_id,
                        institution_id=student.institution_id,
                        program_id=student.program_id,
                        anomaly_type=AnomalyType.INCONSISTENT_CATEGORY,
                        severity=(
                            AnomalySeverity.CRITICAL
                            if student.admission_quota == AdmissionQuota.FN
                            else AnomalySeverity.HIGH
                        ),
                        details=contradiction,
                    )
                )
        return out

    # ------------------------------------------------------------- layer 8

    def detect_impossible_dates(self, snapshot: RegistrySnapshot) -> list[DetectedAnomaly]:
        out: list[DetectedAnomaly] = []
        current_year = date.today().year

        for student in snapshot.students:
            dob_raw = (student.date_of_birth or "").strip()
            enrollment_raw = (student.enrollment_date or "").strip()

            dob = parse_date(dob_raw) if dob_raw else None
            enrollment = parse_date(enrollment_raw) if enrollment_raw else None
            dob_plausible = True

            def flag(
                details: str,
                severity: AnomalySeverity,
                student=student,
            ) -> None:
                out.append(
                    DetectedAnomaly(
                        student_apaar_id=student.apaar_id,
                        institution_id=student.institution_id,
                        program_id=student.program_id,
                        anomaly_type=AnomalyType.IMPOSSIBLE_DATE,
                        severity=severity,
                        details=details,
                    )
                )

            if dob_raw and dob is None:
                flag(
                    f"Date of birth '{dob_raw}' is not a valid calendar date.",
                    AnomalySeverity.CRITICAL,
                )
                dob_plausible = False
            elif dob is not None:
                if dob.year > current_year:
                    flag(
                        f"Date of birth '{dob_raw}' is in the future ({dob.year}).",
                        AnomalySeverity.CRITICAL,
                    )
                    dob_plausible = False
                elif dob.year < EARLIEST_PLAUSIBLE_BIRTH_YEAR:
                    flag(
                        f"Date of birth '{dob_raw}' is not a plausible birth year for an "
                        "enrolled student.",
                        AnomalySeverity.CRITICAL,
                    )
                    dob_plausible = False

            if enrollment_raw and enrollment is None:
                flag(
                    f"Enrolment date '{enrollment_raw}' is not a valid calendar date.",
                    AnomalySeverity.CRITICAL,
                )
            elif enrollment is not None:
                if enrollment.year > current_year:
                    flag(
                        f"Enrolment date '{enrollment_raw}' is in the future ({enrollment.year}).",
                        AnomalySeverity.CRITICAL,
                    )
                if dob is not None and dob_plausible and enrollment < dob:
                    flag(
                        f"Enrolment date '{enrollment_raw}' precedes the date of birth "
                        f"'{dob_raw}'.",
                        AnomalySeverity.CRITICAL,
                    )
                elif dob is not None and dob_plausible:
                    age = age_in_years(dob, enrollment)
                    if 0 <= age < MINIMUM_ENROLMENT_AGE:
                        flag(
                            f"Student was {age} year(s) old at enrolment on "
                            f"'{enrollment_raw}', which is below the plausible minimum of "
                            f"{MINIMUM_ENROLMENT_AGE} years.",
                            AnomalySeverity.HIGH,
                        )
        return out

    # ------------------------------------------------------------- layer 9

    def detect_missing_required_fields(
        self, snapshot: RegistrySnapshot
    ) -> list[DetectedAnomaly]:
        out: list[DetectedAnomaly] = []
        for student in snapshot.students:
            missing: list[str] = []
            if not (student.student_name or "").strip():
                missing.append("student name")
            if not (student.date_of_birth or "").strip():
                missing.append("date of birth")
            if not (student.student_institute_roll_no or "").strip():
                missing.append("institute roll number")
            if not (student.program_id or "").strip():
                missing.append("programme code")
            if not (student.institution_id or "").strip():
                missing.append("institution id")
            if not (student.academic_year or "").strip():
                missing.append("academic year")
            if not (student.enrollment_date or "").strip():
                missing.append("enrolment date")
            if not (student.nationality or "").strip():
                missing.append("nationality")
            if not missing:
                continue
            out.append(
                DetectedAnomaly(
                    student_apaar_id=student.apaar_id,
                    institution_id=student.institution_id,
                    program_id=student.program_id,
                    anomaly_type=AnomalyType.MISSING_REQUIRED_FIELD,
                    severity=AnomalySeverity.HIGH,
                    details=(
                        "Mandatory field(s) missing from the enrolment record: "
                        f"{', '.join(missing)}."
                    ),
                )
            )
        return out

    # ------------------------------------------------------------- helpers

    def build_snapshots(self, snapshot: RegistrySnapshot) -> list[IntakeSnapshot]:
        """Build the real-time utilisation snapshot for every programme."""
        active = [student for student in snapshot.students if student.is_active]
        out: list[IntakeSnapshot] = []
        for program in snapshot.programs:
            rows = [
                student
                for student in active
                if student.institution_id == program.institution_id
                and student.program_id == program.program_id
            ]
            out.append(
                IntakeSnapshot(
                    program=program,
                    regular_enrolled=sum(
                        1 for s in rows if s.admission_quota.is_regular
                    ),
                    supernumerary_enrolled=sum(
                        1 for s in rows if s.admission_quota.is_supernumerary
                    ),
                    total_enrolled=len(rows),
                    nri_enrolled=sum(
                        1 for s in rows if s.admission_quota == AdmissionQuota.NRI
                    ),
                    oci_fn_enrolled=sum(
                        1
                        for s in rows
                        if s.admission_quota in (AdmissionQuota.OCI, AdmissionQuota.FN)
                    ),
                    tfw_enrolled=sum(
                        1 for s in rows if s.admission_quota == AdmissionQuota.TFW
                    ),
                    pmsss_enrolled=sum(
                        1 for s in rows if s.admission_quota == AdmissionQuota.PMSSS
                    ),
                )
            )
        return out


# --------------------------------------------------------------- free funcs


def quota_nationality_conflict(
    quota: AdmissionQuota, nationality: str
) -> str | None:
    """Describe a quota / nationality contradiction, or ``None`` when coherent.

    * ``FN`` (Foreign National) must not be an Indian national.
    * ``NRI`` is by definition an Indian national — the seat exists for Indian
      citizens studying abroad, so a foreign nationality under an NRI bucket is
      a mis-bucketed foreign national.
    * ``OCI`` (Overseas Citizen of India) is an Indian national.
    * ``TFW`` and ``PMSSS`` are Government of India entitlements reserved for
      Indian students.
    """
    if not nationality.strip():
        return None
    indian = is_indian_nationality(nationality)

    if quota == AdmissionQuota.FN:
        if indian:
            return (
                "Quota category 'Foreign National' was declared against the Indian "
                f"nationality '{nationality}'. A foreign-national seat cannot be held "
                "by an Indian citizen."
            )
        return None

    if quota == AdmissionQuota.NRI:
        if not indian:
            return (
                "Quota category 'NRI Supernumerary' was declared against the non-Indian "
                f"nationality '{nationality}'. NRI seats are reserved for Indian nationals, "
                "so this admission belongs in the Foreign National bucket."
            )
        return None

    if quota == AdmissionQuota.TFW:
        if not indian:
            return (
                f"Tuition Fee Waiver was granted to a student of nationality "
                f"'{nationality}'. The TFW supernumerary is reserved for Indian nationals."
            )
        return None

    if quota == AdmissionQuota.PMSSS:
        if not indian:
            return (
                f"PMSSS scholarship was granted to a student of nationality "
                f"'{nationality}'. The PMSSS scheme is reserved for Indian nationals."
            )
        return None

    if quota == AdmissionQuota.OCI:
        return None

    # MERIT / MANAGEMENT
    if not indian:
        return (
            f"Regular-seat quota category '{quota.label}' was declared against a "
            f"non-Indian nationality ({nationality})."
        )
    return None


def is_indian_nationality(nationality: str) -> bool:
    """True when the declared nationality denotes an Indian national."""
    value = (nationality or "").strip()
    upper = value.upper()
    return (
        upper == "INDIAN"
        or upper == "INDIA"
        or "INDIAN" in upper
        or "OCI" in upper
    )


def parse_date(raw: str) -> date | None:
    """Parse ``yyyy-MM-dd`` (registry) or ``dd-MM-yyyy`` (visa documents)."""
    value = (raw or "").strip()
    parts = [part for part in value.replace("/", "-").replace(".", "-").split("-")]
    if len(parts) != 3:
        return None
    try:
        numbers = [int(part.strip()) for part in parts]
    except ValueError:
        return None
    if numbers[0] > 31:
        year, month, day = numbers[0], numbers[1], numbers[2]
    else:
        year, month, day = numbers[2], numbers[1], numbers[0]
    if not 1000 <= year <= 9999 or not 1 <= month <= 12 or not 1 <= day <= 31:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def age_in_years(dob: date, at: date) -> int:
    """Full years between two dates."""
    age = at.year - dob.year
    if (at.month, at.day) < (dob.month, dob.day):
        age -= 1
    return age


def _group_by(items: Iterable, key) -> dict:
    """Stable grouping helper that preserves insertion order."""
    grouped: dict = {}
    for item in items:
        grouped.setdefault(key(item), []).append(item)
    return grouped


#: A ready-to-use engine instance.
engine = AnomalyEngine()


def evaluate(snapshot: RegistrySnapshot) -> list[DetectedAnomaly]:
    """Convenience wrapper around the shared engine instance."""
    return engine.evaluate(snapshot)


def build_snapshots(snapshot: RegistrySnapshot) -> list[IntakeSnapshot]:
    """Convenience wrapper around the shared engine instance."""
    return engine.build_snapshots(snapshot)
