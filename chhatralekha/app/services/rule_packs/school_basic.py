"""School Basic Rule Pack (school_basic).

Implements school-specific regulatory validation:
1. MINOR_GUARDIAN_REQUIRED — Students under 18 must have registered guardian contact.
2. INVALID_AGE_FOR_GRADE — Age must be compatible with grade/class level.
3. DUPLICATE_SCHOOL_ENROLMENT — A student cannot be actively enrolled in multiple schools.
4. SECTION_CAPACITY_EXCEEDED — Class sections must not exceed standard capacity (45).
5. MISSING_UDISE_CODE — Schools must register a UDISE+ identifier.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from typing import Any

from app.models.enums import AnomalySeverity, AnomalyType


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    value = raw.strip()
    parts = [p.strip() for p in value.replace("/", "-").replace(".", "-").split("-")]
    if len(parts) != 3:
        return None
    try:
        numbers = [int(p) for p in parts]
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


def _calculate_age(dob: date, reference_date: date | None = None) -> int:
    ref = reference_date or date.today()
    years = ref.year - dob.year
    if (ref.month, ref.day) < (dob.month, dob.day):
        years -= 1
    return max(0, years)


def _extract_grade_number(grade_str: str | None) -> int | None:
    if not grade_str:
        return None
    match = re.search(r"\b(1[0-2]|[1-9])\b", grade_str)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


class SchoolBasicPack:
    """Regulatory validation rules for primary, middle, and secondary schools."""

    name = "school_basic"

    def evaluate(self, snapshot: Any) -> list[Any]:
        # Avoid circular imports at module load time
        from app.services.anomaly_engine import DetectedAnomaly

        anomalies: list[DetectedAnomaly] = []

        school_inst_ids: set[str] = set()
        for inst in getattr(snapshot, "institutions", ()):
            category = getattr(inst, "category", None) or getattr(inst, "institution_type", None)
            kind = getattr(inst, "kind", None)
            rule_pack = getattr(inst, "rule_pack", None)
            if (
                rule_pack == "school_basic"
                or str(category).upper() in ("SCHOOL", "K12")
                or str(kind).upper() in ("SCHOOL", "SENIOR_SECONDARY_SCHOOL", "JUNIOR_COLLEGE")
            ):
                school_inst_ids.add(inst.institution_id)

                # Check 5: MISSING_UDISE_CODE
                identifiers = getattr(inst, "identifiers", []) or []
                has_udise = any(
                    isinstance(item, dict) and item.get("scheme") == "UDISE_PLUS" and item.get("code")
                    for item in identifiers
                )
                if not has_udise:
                    anomalies.append(
                        DetectedAnomaly(
                            student_apaar_id="",
                            institution_id=inst.institution_id,
                            program_id=None,
                            anomaly_type=AnomalyType.MISSING_UDISE_CODE,
                            severity=AnomalySeverity.WARNING,
                            details=f"School institution '{getattr(inst, 'name', inst.institution_id)}' has no declared UDISE+ identifier.",
                        )
                    )

        # Map students
        students = getattr(snapshot, "students", ())
        section_counts: dict[tuple[str, str, str, str], list[Any]] = defaultdict(list)
        active_school_enrolments: dict[str, list[Any]] = defaultdict(list)

        for student in students:
            is_school_student = (
                student.institution_id in school_inst_ids
                or getattr(student, "grade_level", None) is not None
                or getattr(student, "education_level", None) is not None
            )

            if not is_school_student:
                continue

            dob = _parse_date(getattr(student, "date_of_birth", None))
            enrollment_dt = _parse_date(getattr(student, "enrollment_date", None))
            age = _calculate_age(dob, enrollment_dt) if dob else None

            # Check 1: MINOR_GUARDIAN_REQUIRED (< 18 years)
            is_minor = getattr(student, "is_minor", None)
            if is_minor is True or (age is not None and age < 18):
                guardian_name = getattr(student, "guardian_name", None)
                guardian_contact = getattr(student, "guardian_contact", None)
                if not guardian_name or not guardian_contact:
                    anomalies.append(
                        DetectedAnomaly(
                            student_apaar_id=student.apaar_id,
                            institution_id=student.institution_id,
                            program_id=student.program_id,
                            anomaly_type=AnomalyType.MINOR_GUARDIAN_REQUIRED,
                            severity=AnomalySeverity.CRITICAL,
                            details=(
                                f"Minor student '{student.student_name}' (age {age or '<18'}) is missing "
                                f"mandatory parent/guardian name or contact details under child data protection rules."
                            ),
                        )
                    )

            # Check 2: INVALID_AGE_FOR_GRADE
            grade_str = getattr(student, "grade_level", None) or getattr(student, "program_id", None)
            grade_num = _extract_grade_number(grade_str)
            if grade_num is not None and age is not None:
                # Class 1 expected ~6 years (min 4, max 9), Class 10 expected ~15 years (min 13, max 19)
                min_expected_age = grade_num + 3
                max_expected_age = grade_num + 9
                if age < min_expected_age or age > max_expected_age:
                    anomalies.append(
                        DetectedAnomaly(
                            student_apaar_id=student.apaar_id,
                            institution_id=student.institution_id,
                            program_id=student.program_id,
                            anomaly_type=AnomalyType.INVALID_AGE_FOR_GRADE,
                            severity=AnomalySeverity.HIGH,
                            details=(
                                f"Student age {age} is incompatible with enrolled grade {grade_num} "
                                f"(expected range: {min_expected_age} to {max_expected_age} years)."
                            ),
                        )
                    )

            # Collect for Check 3: DUPLICATE_SCHOOL_ENROLMENT
            if getattr(student, "is_active", True):
                active_school_enrolments[student.apaar_id].append(student)

            # Collect for Check 4: SECTION_CAPACITY_EXCEEDED
            grade = getattr(student, "grade_level", None) or student.program_id
            section = getattr(student, "section", None)
            year = getattr(student, "academic_year", "2024-25")
            if section and getattr(student, "is_active", True):
                section_counts[(student.institution_id, year, grade, section)].append(student)

        # Evaluate Check 3: DUPLICATE_SCHOOL_ENROLMENT
        for apaar_id, records in active_school_enrolments.items():
            distinct_schools = {r.institution_id for r in records}
            if len(distinct_schools) > 1:
                for r in records:
                    anomalies.append(
                        DetectedAnomaly(
                            student_apaar_id=apaar_id,
                            institution_id=r.institution_id,
                            program_id=r.program_id,
                            anomaly_type=AnomalyType.DUPLICATE_SCHOOL_ENROLMENT,
                            severity=AnomalySeverity.CRITICAL,
                            details=(
                                f"Student is concurrently enrolled across {len(distinct_schools)} "
                                f"active school institutions ({', '.join(sorted(distinct_schools))}) "
                                f"in the same academic year."
                            ),
                        )
                    )

        # Evaluate Check 4: SECTION_CAPACITY_EXCEEDED
        for (inst_id, _yr, gr, sec), class_students in section_counts.items():
            if len(class_students) > 45:
                sev = AnomalySeverity.CRITICAL if len(class_students) > 50 else AnomalySeverity.WARNING
                for st in class_students:
                    anomalies.append(
                        DetectedAnomaly(
                            student_apaar_id=st.apaar_id,
                            institution_id=inst_id,
                            program_id=st.program_id,
                            anomaly_type=AnomalyType.SECTION_CAPACITY_EXCEEDED,
                            severity=sev,
                            details=(
                                f"Section {gr}-{sec} enrolment count ({len(class_students)}) "
                                f"exceeds standard classroom ceiling of 45 students."
                            ),
                        )
                    )

        return anomalies
