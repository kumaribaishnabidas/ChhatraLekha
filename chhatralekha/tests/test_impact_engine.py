"""Tests for the Academic Record Change Impact Detector."""

from __future__ import annotations

import pytest

from app.services import impact_engine
from app.services.policy import DEFAULT_POLICY, Policy, policy_from_document


def student(**overrides):
    document = {
        "_id": "rec-1",
        "apaar_id": "984210357890",
        "student_name": "Rahul Kumar",
        "date_of_birth": "2004-03-12",
        "gender": "M",
        "institution_id": "INST-A",
        "program_id": "BTECH_CSE",
        "academic_year": "2024-25",
        "admission_quota": "REGULAR_MERIT",
        "enrollment_date": "2024-07-01",
        "student_institute_roll_no": "CSE-0001",
        "nationality": "Indian",
        "record_status": "ACTIVE",
        "is_active": True,
        "version": 1,
    }
    document.update(overrides)
    return document


def programme(**overrides):
    document = {
        "institution_id": "INST-A",
        "program_id": "BTECH_CSE",
        "program_name": "B.Tech CSE",
        "academic_year": "2024-25",
        "approved_intake": 60,
        "max_supernumerary_nri": 3,
        "max_supernumerary_fn_oci": 9,
        "max_supernumerary_tfw": 3,
        "max_pmsss": 6,
        "total_sanctioned": 81,
    }
    document.update(overrides)
    return document


@pytest.fixture
def policy():
    return policy_from_document(dict(DEFAULT_POLICY))


def assess(current, proposed, students, programs, **kwargs):
    return impact_engine.assess(
        current,
        proposed,
        students=students,
        programs=programs,
        policy=kwargs.pop("policy", None),
        **kwargs,
    )


# ------------------------------------------------------------- the basics


def test_no_change_produces_no_finding():
    result = assess(student(), {"academic_year": "2024-25"}, [student()], [programme()])
    assert result.findings == []
    assert result.changed_fields == []


def test_only_correctable_fields_are_considered():
    changes = impact_engine.changed_fields(student(), {"is_active": False, "record_status": "X"})
    assert changes == {}


def test_the_changed_fields_are_reported():
    result = assess(
        student(), {"academic_year": "2025-26"}, [student()], [programme()]
    )
    assert result.changed_fields == ["academic_year"]


# --------------------------------------------------------------- rule A


def test_an_invalid_new_identifier_is_critical():
    result = assess(
        student(), {"apaar_id": "12345"}, [student()], [programme()]
    )
    finding = next(f for f in result.findings if f.rule_id == "CIA-A")
    assert finding.severity == "CRITICAL"
    assert finding.certainty == "confirmed"


def test_a_duplicate_in_the_same_institution_is_critical():
    other = student(_id="rec-2", apaar_id="984210357891")
    result = assess(
        student(),
        {"apaar_id": "984210357891"},
        [student(), other],
        [programme()],
    )
    finding = next(f for f in result.findings if f.rule_id == "CIA-A")
    assert finding.severity == "CRITICAL"
    assert "already used in this institution" in finding.title


def test_a_collision_with_another_institution_is_a_review_not_a_fraud():
    other = student(_id="rec-2", institution_id="INST-B", apaar_id="984210357891")
    result = assess(
        student(),
        {"apaar_id": "984210357891"},
        [student(), other],
        [programme()],
    )
    finding = next(f for f in result.findings if f.rule_id == "CIA-A")
    assert finding.severity == "HIGH"
    assert finding.certainty == "suspected"
    assert "not, by itself, evidence of anything" in finding.explanation
    assert "never treated as fraud by the system" in finding.explanation


def test_the_stale_anomalies_of_the_old_identifier_are_reported():
    anomalies = [{"_id": "an-1", "student_apaar_id": "984210357890"}]
    result = assess(
        student(),
        {"apaar_id": "984210357899"},
        [student()],
        [programme()],
        anomalies=anomalies,
    )
    finding = next(f for f in result.findings if f.rule_id == "CIA-A")
    assert "still point at the old identifier" in finding.title


def test_a_revoked_credential_of_the_old_identifier_is_reported():
    revoked = [{"_id": "rv-1", "apaar_id": "984210357890"}]
    result = assess(
        student(),
        {"apaar_id": "984210357899"},
        [student()],
        [programme()],
        revoked=revoked,
    )
    titles = [f.title for f in result.findings if f.rule_id == "CIA-A"]
    assert any("revocation list" in title for title in titles)


# --------------------------------------------------------------- rule B


def test_a_change_to_an_unsanctioned_programme_is_critical():
    result = assess(
        student(),
        {"program_id": "BTECH_NAVAL"},
        [student()],
        [programme()],
    )
    finding = next(f for f in result.findings if f.rule_id == "CIA-B")
    assert finding.severity == "CRITICAL"
    assert "not sanctioned" in finding.title


def test_the_seats_of_both_programmes_have_to_be_recalculated():
    result = assess(
        student(),
        {"program_id": "BTECH_ECE"},
        [student()],
        [programme(), programme(program_id="BTECH_ECE")],
    )
    titles = [f.title for f in result.findings if f.rule_id == "CIA-B"]
    assert any("destination" in title for title in titles)
    assert any("source programme" in title for title in titles)


def test_a_roll_number_clash_at_the_destination_is_reported():
    other = student(
        _id="rec-2", institution_id="INST-B", student_institute_roll_no="CSE-0001"
    )
    result = assess(
        student(),
        {"institution_id": "INST-B"},
        [student(), other],
        [programme(), programme(institution_id="INST-B")],
    )
    finding = next(
        f for f in result.findings if f.rule_id == "CIA-B" and "roll number" in f.title
    )
    assert finding.severity == "HIGH"


# --------------------------------------------------------------- rule C


def test_an_academic_year_change_recalculates_both_years():
    result = assess(
        student(), {"academic_year": "2025-26"}, [student()], [programme()]
    )
    finding = next(f for f in result.findings if f.rule_id == "CIA-C")
    assert "both academic years" in finding.title
    assert finding.rule_data["old_academic_year"] == "2024-25"
    assert finding.rule_data["new_academic_year"] == "2025-26"


def test_an_enrolment_date_before_the_date_of_birth_is_critical():
    result = assess(
        student(),
        {"enrollment_date": "2003-01-01"},
        [student()],
        [programme()],
    )
    finding = next(
        f for f in result.findings if f.rule_id == "CIA-C" and "precedes" in f.title
    )
    assert finding.severity == "CRITICAL"


def test_an_enrolment_date_in_another_academic_year_is_reported():
    result = assess(
        student(),
        {"enrollment_date": "2025-07-01"},
        [student()],
        [programme()],
    )
    finding = next(
        f for f in result.findings if f.rule_id == "CIA-C" and "different academic year" in f.title
    )
    assert finding.severity == "HIGH"


# --------------------------------------------------------------- rule D


def test_a_quota_change_re_runs_the_supernumerary_ceiling(policy):
    others = [
        student(_id=f"rec-{index}", apaar_id=f"98421035789{index}")
        for index in range(6)
    ]
    for other in others:
        other["admission_quota"] = "SUPERNUMERARY_NRI"
    result = assess(
        student(),
        {"admission_quota": "SUPERNUMERARY_NRI"},
        [student(), *others],
        [programme(approved_intake=60)],
        policy=policy,
    )
    finding = next(
        f for f in result.findings if f.rule_id == "CIA-D" and "ceiling" in f.title
    )
    assert finding.rule_data["bucket"] == "NRI"
    assert finding.rule_data["cap"] == 3


def test_an_unsupported_policy_case_is_review_only():
    partial = Policy(
        policy_id="aph-partial",
        version="partial",
        seats={},
        supported_categories=["NRI"],
    )
    others = [
        student(_id=f"rec-{index}", apaar_id=f"98421035789{index}")
        for index in range(6)
    ]
    for other in others:
        other["admission_quota"] = "SUPERNUMERARY_NRI"
    result = assess(
        student(),
        {"admission_quota": "SUPERNUMERARY_NRI"},
        [student(), *others],
        [programme()],
        policy=partial,
    )
    finding = next(
        f for f in result.findings if f.rule_id == "CIA-D" and "does not define" in f.title
    )
    assert finding.certainty == "review_only"


def test_a_foreign_national_seat_for_an_indian_citizen_is_critical():
    result = assess(
        student(),
        {"admission_quota": "SUPERNUMERARY_FN"},
        [student()],
        [programme()],
    )
    finding = next(
        f for f in result.findings if f.rule_id == "CIA-D" and "contradict" in f.title
    )
    assert finding.severity == "CRITICAL"


def test_an_nri_seat_for_a_non_indian_is_high_not_critical():
    result = assess(
        student(),
        {"admission_quota": "SUPERNUMERARY_NRI", "nationality": "Chinese"},
        [student()],
        [programme()],
    )
    finding = next(
        f for f in result.findings if f.rule_id == "CIA-D" and "contradict" in f.title
    )
    assert finding.severity == "HIGH"


# --------------------------------------------------------------- rule E


def test_the_intake_is_compared_per_programme_year_and_category(policy):
    # Sixty regular enrolments already sit in the 2024-25 programme, and the
    # sanctioned intake is sixty, so moving one more admission into that year
    # breaches it.
    others = [
        student(
            _id=f"other-{index}",
            apaar_id=f"9842103578{index:02d}",
            student_institute_roll_no=f"R{index}",
        )
        for index in range(60)
    ]
    result = assess(
        student(academic_year="2023-24", enrollment_date="2023-07-01"),
        {"academic_year": "2024-25"},
        [student(academic_year="2023-24", enrollment_date="2023-07-01"), *others],
        [programme(approved_intake=60)],
        policy=policy,
    )
    finding = next(
        f for f in result.findings if f.rule_id == "CIA-E" and "exceed" in f.title
    )
    assert finding.severity == "CRITICAL"
    assert finding.rule_data["approved"] == 60
    assert finding.rule_data["projected"] == 61
    assert finding.rule_data["academic_year"] == "2024-25"


def test_a_different_year_is_not_counted_against_the_same_intake(policy):
    others = [
        student(
            _id=f"rec-{index}",
            apaar_id=f"9842103578{index:02d}",
            student_institute_roll_no=f"R{index}",
            academic_year="2023-24",
        )
        for index in range(60)
    ]
    result = assess(
        student(),
        {"academic_year": "2024-25"},
        [student(), *others],
        [programme(approved_intake=60)],
        policy=policy,
    )
    assert not [f for f in result.findings if f.rule_id == "CIA-E"]


def test_the_pmsss_ceiling_is_compared_per_programme(policy):
    others = [
        student(
            _id=f"other-{index}",
            apaar_id=f"9842103578{index:02d}",
            student_institute_roll_no=f"R{index}",
            admission_quota="PMSSS",
        )
        for index in range(6)
    ]
    result = assess(
        student(),
        {"admission_quota": "PMSSS"},
        [student(), *others],
        [programme()],
        policy=policy,
    )
    finding = next(
        f for f in result.findings if f.rule_id == "CIA-E" and "PMSSS" in f.title
    )
    assert finding.rule_data["bucket"] == "PMSSS"
    assert finding.rule_data["cap"] == 6


# --------------------------------------------------------------- rule F


def test_a_change_to_a_seal_bound_field_makes_the_tokens_stale():
    tokens = [{"_id": "tk-1", "student_record_id": "rec-1", "revoked": False}]
    result = assess(
        student(),
        {"student_name": "Rahul K."},
        [student()],
        [programme()],
        tokens=tokens,
    )
    finding = next(f for f in result.findings if f.rule_id == "CIA-F")
    assert "out of date" in finding.title
    assert finding.rule_data["fields"] == ["student_name"]


def test_a_change_to_a_field_outside_the_seal_does_not_stale_the_tokens():
    tokens = [{"_id": "tk-1", "student_record_id": "rec-1", "revoked": False}]
    result = assess(
        student(),
        {"contact_email": "new@example.in"},
        [student()],
        [programme()],
        tokens=tokens,
    )
    assert not [f for f in result.findings if f.rule_id == "CIA-F"]


def test_a_harmless_correction_produces_no_finding_at_all():
    result = assess(
        student(),
        {"contact_email": "new@example.in", "contact_phone": "+91 90000 00000"},
        [student()],
        [programme()],
    )
    assert result.findings == []
    assert result.highest_severity == "INFO"
    assert not result.requires_review


# --------------------------------------------------------------- helpers


def test_the_academic_year_follows_the_july_to_june_convention():
    assert impact_engine._academic_year_of("2024-07-01") == "2024-25"
    assert impact_engine._academic_year_of("2025-03-15") == "2024-25"
    assert impact_engine._academic_year_of("2025-06-30") == "2024-25"
    assert impact_engine._academic_year_of("2025-07-01") == "2025-26"
