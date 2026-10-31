"""Tests for the multi-layer anomaly detection engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pytest

from app.models.enums import (
    AdmissionQuota,
    AnomalySeverity,
    AnomalyType,
    Gender,
    InstitutionType,
    SocialCategory,
)
from app.services.anomaly_engine import (
    AnomalyEngine,
    RegistrySnapshot,
    is_indian_nationality,
    quota_nationality_conflict,
)


@dataclass
class FakeInstitution:
    institution_id: str = "INST-A"
    name: str = "Alpha Institute of Technology"
    institution_type: InstitutionType = InstitutionType.ENGINEERING
    state: str = "Karnataka"
    city: str = "Bengaluru"
    affiliation_university: str = "Test University"
    approval_year: int = 2012
    naac_grade: str = "A++"


@dataclass
class FakeProgramme:
    program_id: str = "BTECH_CSE"
    institution_id: str = "INST-A"
    program_name: str = "B.Tech Computer Science"
    program_level: str = "UG"
    approved_intake: int = 60
    max_supernumerary_nri: int = 3
    max_supernumerary_fn_oci: int = 9
    max_supernumerary_tfw: int = 3
    max_pmsss: int = 6
    total_sanctioned: int = 81


@dataclass
class FakeStudent:
    apaar_id: str = "984210357890"
    student_name: str = "Aakash Verma"
    date_of_birth: str = "2004-03-12"
    gender: Gender = Gender.MALE
    institution_id: str = "INST-A"
    program_id: str = "BTECH_CSE"
    academic_year: str = "2024-25"
    admission_quota: AdmissionQuota = AdmissionQuota.MERIT
    enrollment_date: str = "2024-08-01"
    student_institute_roll_no: str = "CSE-0001"
    nationality: str = "Indian"
    passport_number: Optional[str] = None
    visa_validity: Optional[str] = None
    country_of_origin: Optional[str] = None
    is_active: bool = True
    social_category: SocialCategory = SocialCategory.GENERAL
    extra: dict = field(default_factory=dict)


@pytest.fixture
def engine():
    return AnomalyEngine()


def snapshot(students, programmes=None, institutions=None):
    return RegistrySnapshot(
        institutions=institutions or [FakeInstitution()],
        programs=programmes or [FakeProgramme()],
        students=students,
    )


def types_of(findings):
    return {finding.anomaly_type for finding in findings}


# ------------------------------------------------------------ layer 1

def test_a_malformed_apaar_id_is_critical(engine):
    findings = engine.evaluate(snapshot([FakeStudent(apaar_id="12345")]))
    assert AnomalyType.INVALID_APAAR_FORMAT in types_of(findings)
    finding = next(f for f in findings if f.anomaly_type == AnomalyType.INVALID_APAAR_FORMAT)
    assert finding.severity == AnomalySeverity.CRITICAL


def test_a_valid_apaar_id_is_accepted(engine):
    findings = engine.evaluate(snapshot([FakeStudent()]))
    assert AnomalyType.INVALID_APAAR_FORMAT not in types_of(findings)


# ------------------------------------------------------------ layer 2

def test_a_cross_institution_duplicate_is_detected(engine):
    students = [
        FakeStudent(apaar_id="984210357890", institution_id="INST-A"),
        FakeStudent(apaar_id="984210357890", institution_id="INST-B", student_institute_roll_no="CSE-0002"),
    ]
    findings = engine.evaluate(snapshot(students))
    assert AnomalyType.DUPLICATE_CROSS_COLLEGE in types_of(findings)


def test_two_regular_seats_make_the_duplicate_critical(engine):
    students = [
        FakeStudent(apaar_id="984210357890", institution_id="INST-A"),
        FakeStudent(apaar_id="984210357890", institution_id="INST-B", student_institute_roll_no="CSE-0002"),
    ]
    findings = engine.evaluate(snapshot(students))
    finding = next(
        f for f in findings if f.anomaly_type == AnomalyType.DUPLICATE_CROSS_COLLEGE
    )
    assert finding.severity == AnomalySeverity.CRITICAL


def test_an_inactive_record_does_not_count_as_a_duplicate(engine):
    students = [
        FakeStudent(apaar_id="984210357890", institution_id="INST-A"),
        FakeStudent(
            apaar_id="984210357890",
            institution_id="INST-B",
            student_institute_roll_no="CSE-0002",
            is_active=False,
        ),
    ]
    findings = engine.evaluate(snapshot(students))
    assert AnomalyType.DUPLICATE_CROSS_COLLEGE not in types_of(findings)


# ------------------------------------------------------------ layer 3

def test_a_same_institution_duplicate_is_detected(engine):
    students = [
        FakeStudent(apaar_id="984210357890"),
        FakeStudent(apaar_id="984210357890", student_institute_roll_no="CSE-0002"),
    ]
    findings = engine.evaluate(snapshot(students))
    assert AnomalyType.DUPLICATE_SAME_INSTITUTION in types_of(findings)


def test_a_duplicate_across_two_programmes_is_critical(engine):
    students = [
        FakeStudent(apaar_id="984210357890", program_id="BTECH_CSE"),
        FakeStudent(apaar_id="984210357890", program_id="BTECH_ECE", student_institute_roll_no="ECE-1"),
    ]
    findings = engine.evaluate(snapshot(students))
    finding = next(
        f for f in findings if f.anomaly_type == AnomalyType.DUPLICATE_SAME_INSTITUTION
    )
    assert finding.severity == AnomalySeverity.CRITICAL


# ------------------------------------------------------------ layer 4

def test_a_duplicate_roll_number_is_detected(engine):
    students = [
        FakeStudent(apaar_id="984210357890", student_institute_roll_no="CSE-0001"),
        FakeStudent(apaar_id="984210357891", student_institute_roll_no="cse-0001"),
    ]
    findings = engine.evaluate(snapshot(students))
    assert AnomalyType.DUPLICATE_ROLL_NUMBER in types_of(findings)


def test_the_same_roll_number_in_two_institutions_is_fine(engine):
    students = [
        FakeStudent(apaar_id="984210357890", institution_id="INST-A", student_institute_roll_no="CSE-1"),
        FakeStudent(apaar_id="984210357891", institution_id="INST-B", student_institute_roll_no="CSE-1"),
    ]
    findings = engine.evaluate(snapshot(students))
    assert AnomalyType.DUPLICATE_ROLL_NUMBER not in types_of(findings)


# ------------------------------------------------------------ layer 5

def test_over_admission_is_critical(engine):
    students = [
        FakeStudent(apaar_id=f"9842103578{index:02d}", student_institute_roll_no=f"R{index}")
        for index in range(5)
    ]
    findings = engine.evaluate(
        snapshot(students, programmes=[FakeProgramme(approved_intake=2)])
    )
    assert AnomalyType.EXCESS_APPROVED_INTAKE in types_of(findings)
    finding = next(
        f for f in findings if f.anomaly_type == AnomalyType.EXCESS_APPROVED_INTAKE
    )
    assert finding.severity == AnomalySeverity.CRITICAL


def test_within_the_sanctioned_intake_is_clean(engine):
    students = [
        FakeStudent(apaar_id=f"9842103578{index:02d}", student_institute_roll_no=f"R{index}")
        for index in range(2)
    ]
    findings = engine.evaluate(
        snapshot(students, programmes=[FakeProgramme(approved_intake=2)])
    )
    assert AnomalyType.EXCESS_APPROVED_INTAKE not in types_of(findings)


def test_supernumerary_seats_do_not_consume_the_regular_intake(engine):
    students = [
        FakeStudent(
            apaar_id=f"9842103578{index:02d}",
            student_institute_roll_no=f"R{index}",
            admission_quota=AdmissionQuota.NRI,
        )
        for index in range(3)
    ]
    findings = engine.evaluate(
        snapshot(students, programmes=[FakeProgramme(approved_intake=2)])
    )
    assert AnomalyType.EXCESS_APPROVED_INTAKE not in types_of(findings)


# ------------------------------------------------------------ layer 6

def test_the_nri_ceiling_is_enforced(engine):
    students = [
        FakeStudent(
            apaar_id=f"9842103578{index:02d}",
            student_institute_roll_no=f"R{index}",
            admission_quota=AdmissionQuota.NRI,
        )
        for index in range(5)
    ]
    findings = engine.evaluate(
        snapshot(students, programmes=[FakeProgramme(max_supernumerary_nri=2)])
    )
    assert AnomalyType.SUPERNUMERARY_BREACH in types_of(findings)


def test_a_small_ceiling_breach_is_a_warning(engine):
    students = [
        FakeStudent(
            apaar_id=f"9842103578{index:02d}",
            student_institute_roll_no=f"R{index}",
            admission_quota=AdmissionQuota.NRI,
        )
        for index in range(4)
    ]
    findings = engine.evaluate(
        snapshot(students, programmes=[FakeProgramme(max_supernumerary_nri=3)])
    )
    finding = next(
        f for f in findings if f.anomaly_type == AnomalyType.SUPERNUMERARY_BREACH
    )
    assert finding.severity == AnomalySeverity.WARNING


def test_a_large_ceiling_breach_is_critical(engine):
    students = [
        FakeStudent(
            apaar_id=f"9842103578{index:02d}",
            student_institute_roll_no=f"R{index}",
            admission_quota=AdmissionQuota.NRI,
        )
        for index in range(9)
    ]
    findings = engine.evaluate(
        snapshot(students, programmes=[FakeProgramme(max_supernumerary_nri=3)])
    )
    finding = next(
        f for f in findings if f.anomaly_type == AnomalyType.SUPERNUMERARY_BREACH
    )
    assert finding.severity == AnomalySeverity.CRITICAL


def test_the_pmsss_ceiling_is_enforced(engine):
    students = [
        FakeStudent(
            apaar_id=f"9842103578{index:02d}",
            student_institute_roll_no=f"R{index}",
            admission_quota=AdmissionQuota.PMSSS,
        )
        for index in range(4)
    ]
    findings = engine.evaluate(
        snapshot(students, programmes=[FakeProgramme(max_pmsss=2)])
    )
    assert AnomalyType.SUPERNUMERARY_BREACH in types_of(findings)


# ------------------------------------------------------------ layer 7

def test_a_foreign_national_without_documents_is_flagged(engine):
    student = FakeStudent(
        admission_quota=AdmissionQuota.FN,
        nationality="China",
        passport_number=None,
        visa_validity=None,
        country_of_origin=None,
    )
    findings = engine.evaluate(snapshot([student]))
    finding = next(
        f for f in findings if f.anomaly_type == AnomalyType.INCONSISTENT_CATEGORY
    )
    assert finding.severity == AnomalySeverity.WARNING
    assert "passport" in finding.details


def test_a_foreign_national_seat_held_by_an_indian_is_critical(engine):
    student = FakeStudent(admission_quota=AdmissionQuota.FN, nationality="Indian")
    findings = engine.evaluate(snapshot([student]))
    finding = next(
        f
        for f in findings
        if f.anomaly_type == AnomalyType.INCONSISTENT_CATEGORY
        and "Indian" in f.details
    )
    assert finding.severity == AnomalySeverity.CRITICAL


def test_an_nri_seat_held_by_a_non_indian_is_high(engine):
    student = FakeStudent(admission_quota=AdmissionQuota.NRI, nationality="Chinese")
    findings = engine.evaluate(snapshot([student]))
    finding = next(
        f
        for f in findings
        if f.anomaly_type == AnomalyType.INCONSISTENT_CATEGORY
        and "NRI" in f.details
    )
    assert finding.severity == AnomalySeverity.HIGH


def test_an_nri_seat_held_by_an_indian_is_correct(engine):
    student = FakeStudent(admission_quota=AdmissionQuota.NRI, nationality="Indian")
    findings = engine.evaluate(snapshot([student]))
    assert AnomalyType.INCONSISTENT_CATEGORY not in types_of(findings)


def test_a_tfw_seat_held_by_a_non_indian_is_flagged(engine):
    student = FakeStudent(admission_quota=AdmissionQuota.TFW, nationality="Nepali")
    findings = engine.evaluate(snapshot([student]))
    assert AnomalyType.INCONSISTENT_CATEGORY in types_of(findings)


def test_a_regular_seat_held_by_a_non_indian_is_flagged(engine):
    student = FakeStudent(admission_quota=AdmissionQuota.MERIT, nationality="German")
    findings = engine.evaluate(snapshot([student]))
    assert AnomalyType.INCONSISTENT_CATEGORY in types_of(findings)


def test_the_quota_nationality_conflict_helper():
    assert quota_nationality_conflict(AdmissionQuota.FN, "Indian") is not None
    assert quota_nationality_conflict(AdmissionQuota.FN, "Chinese") is None
    assert quota_nationality_conflict(AdmissionQuota.NRI, "Indian") is None
    assert quota_nationality_conflict(AdmissionQuota.NRI, "Chinese") is not None
    assert quota_nationality_conflict(AdmissionQuota.OCI, "Chinese") is None
    assert quota_nationality_conflict(AdmissionQuota.PMSSS, "") is None


def test_is_indian_nationality():
    assert is_indian_nationality("Indian")
    assert is_indian_nationality("India")
    assert is_indian_nationality("OCI")
    assert not is_indian_nationality("Chinese")


# ------------------------------------------------------------ layer 8

def test_a_future_date_of_birth_is_critical(engine):
    student = FakeStudent(date_of_birth="2099-01-01", enrollment_date="2099-06-01")
    findings = engine.evaluate(snapshot([student]))
    finding = next(f for f in findings if f.anomaly_type == AnomalyType.IMPOSSIBLE_DATE)
    assert finding.severity == AnomalySeverity.CRITICAL


def test_an_unparseable_date_is_critical(engine):
    student = FakeStudent(date_of_birth="not-a-date")
    findings = engine.evaluate(snapshot([student]))
    finding = next(f for f in findings if f.anomaly_type == AnomalyType.IMPOSSIBLE_DATE)
    assert finding.severity == AnomalySeverity.CRITICAL


def test_enrolment_before_birth_is_critical(engine):
    student = FakeStudent(date_of_birth="2006-01-01", enrollment_date="2005-01-01")
    findings = engine.evaluate(snapshot([student]))
    finding = next(f for f in findings if f.anomaly_type == AnomalyType.IMPOSSIBLE_DATE)
    assert finding.severity == AnomalySeverity.CRITICAL


def test_a_child_at_enrolment_is_high(engine):
    student = FakeStudent(date_of_birth="2015-01-01", enrollment_date="2024-08-01")
    findings = engine.evaluate(snapshot([student]))
    finding = next(f for f in findings if f.anomaly_type == AnomalyType.IMPOSSIBLE_DATE)
    assert finding.severity == AnomalySeverity.HIGH


# ------------------------------------------------------------ layer 9

def test_missing_mandatory_fields_are_high(engine):
    student = FakeStudent(student_name="", academic_year="", nationality="")
    findings = engine.evaluate(snapshot([student]))
    finding = next(
        f for f in findings if f.anomaly_type == AnomalyType.MISSING_REQUIRED_FIELD
    )
    assert finding.severity == AnomalySeverity.HIGH
    assert "student name" in finding.details


# ------------------------------------------------------------ layer 10

def test_an_unsanctioned_programme_is_critical(engine):
    student = FakeStudent(program_id="BTECH_NAVAL_ARCH")
    findings = engine.evaluate(snapshot([student]))
    finding = next(
        f for f in findings if f.anomaly_type == AnomalyType.UNSANCTIONED_PROGRAM
    )
    assert finding.severity == AnomalySeverity.CRITICAL


# ------------------------------------------------------------ snapshots

def test_the_snapshots_report_the_utilisation(engine):
    students = [
        FakeStudent(apaar_id="984210357890", admission_quota=AdmissionQuota.MERIT),
        FakeStudent(apaar_id="984210357891", student_institute_roll_no="R2", admission_quota=AdmissionQuota.NRI),
        FakeStudent(apaar_id="984210357892", student_institute_roll_no="R3", admission_quota=AdmissionQuota.TFW),
    ]
    snapshots = engine.build_snapshots(snapshot(students))
    assert len(snapshots) == 1
    result = snapshots[0]
    assert result.regular_enrolled == 1
    assert result.supernumerary_enrolled == 2
    assert result.total_enrolled == 3
    assert result.nri_enrolled == 1
    assert result.tfw_enrolled == 1
    assert not result.has_breach


def test_a_clean_registry_produces_no_findings(engine):
    students = [
        FakeStudent(apaar_id=f"9842103578{index:02d}", student_institute_roll_no=f"R{index}")
        for index in range(5)
    ]
    findings = engine.evaluate(snapshot(students))
    assert findings == []
