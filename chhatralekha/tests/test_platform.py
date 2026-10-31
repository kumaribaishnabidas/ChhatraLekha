"""Tests for the CSV writers, the consent policy, the audit chain and RBAC."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.core import rbac
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    hash_pin,
    new_salt,
    password_policy_violations,
    verify_api_key,
    verify_password,
    verify_pin,
)
from app.models.enums import (
    AdmissionQuota,
    ConsentChannel,
    ConsentPurpose,
    ConsentStatus,
    Gender,
    SocialCategory,
)
from app.services import audit_chain, consent_policy, csv_export


@dataclass
class FakeStudent:
    apaar_id: str = "984210357890"
    student_name: str = "Asha Ramesh Iyer"
    date_of_birth: str = "2005-04-17"
    gender: Gender = Gender.FEMALE
    institution_id: str = "INST-0421"
    program_id: str = "BTECH_CSE"
    academic_year: str = "2024-25"
    admission_quota: AdmissionQuota = AdmissionQuota.MERIT
    enrollment_date: str = "2024-08-01"
    student_institute_roll_no: str = "CSE-042"
    nationality: str = "Indian"
    passport_number: str | None = None
    visa_validity: str | None = None
    country_of_origin: str | None = None
    abc_account_id: str | None = None
    verification_status: str = "VERIFIED"
    is_active: bool = True
    social_category: SocialCategory = SocialCategory.GENERAL
    admission_date: str | None = "2024-08-01"
    contact_email: str | None = "asha.iyer@example.in"
    contact_phone: str | None = "+91 98450 11223"
    state_of_domicile: str | None = "Karnataka"


@dataclass
class FakeConsent:
    purpose: ConsentPurpose
    status: ConsentStatus = ConsentStatus.GRANTED
    recorded_at: datetime = datetime(2024, 1, 1, tzinfo=timezone.utc)
    channel: ConsentChannel = ConsentChannel.WEB_PORTAL


# ------------------------------------------------------------------- CSV


def test_the_student_export_writes_the_documented_header():
    csv = csv_export.students([FakeStudent()])
    assert csv.splitlines()[0] == ",".join(csv_export.STUDENT_COLUMNS)


def test_the_student_export_writes_every_extended_column():
    csv = csv_export.students([FakeStudent(social_category=SocialCategory.OBC)])
    row = csv.splitlines()[1].split(",")
    index = {name: position for position, name in enumerate(csv_export.STUDENT_COLUMNS)}
    assert row[index["APAAR_ID"]] == "984210357890"
    assert row[index["SOCIAL_CATEGORY"]] == "OBC"
    assert row[index["ADMISSION_DATE"]] == "2024-08-01"
    assert row[index["CONTACT_EMAIL"]] == "asha.iyer@example.in"
    assert row[index["STATE_OF_DOMICILE"]] == "Karnataka"


def test_the_export_can_be_fed_back_into_the_importer():
    from app.services import csv_ingestion

    csv = csv_export.students([FakeStudent()])
    report = csv_ingestion.validate_csv(
        csv,
        csv_ingestion.CsvValidationContext(
            programs=[
                type(
                    "P",
                    (),
                    {
                        "program_id": "BTECH_CSE",
                        "program_name": "B.Tech CSE",
                        "approved_intake": 60,
                        "max_supernumerary_nri": 3,
                        "max_supernumerary_fn_oci": 9,
                        "max_supernumerary_tfw": 3,
                        "max_pmsss": 6,
                    },
                )()
            ]
        ),
    )
    assert report.header_errors == []
    assert report.rows[0].apaar_id == "984210357890"
    assert report.rows[0].full_name == "Asha Ramesh Iyer"


def test_fields_with_a_separator_are_quoted():
    assert csv_export.escape("a,b") == '"a,b"'
    assert csv_export.escape('say "hi"') == '"say ""hi"""'
    assert csv_export.escape("plain") == "plain"
    assert csv_export.escape("line1\nline2") == '"line1\nline2"'


def test_the_header_can_be_omitted():
    assert len(csv_export.students([FakeStudent()], include_header=False).splitlines()) == 1


# --------------------------------------------------------------- consent


def test_an_explicit_purpose_is_blocked_without_consent():
    decision = consent_policy.evaluate(ConsentPurpose.CREDENTIAL_VERIFICATION, [])
    assert not decision.allowed
    assert decision.status == ConsentStatus.PENDING


def test_a_granted_purpose_is_allowed():
    decision = consent_policy.evaluate(
        ConsentPurpose.CREDENTIAL_VERIFICATION,
        [FakeConsent(ConsentPurpose.CREDENTIAL_VERIFICATION)],
    )
    assert decision.allowed


def test_a_revocation_blocks_the_purpose():
    decision = consent_policy.evaluate(
        ConsentPurpose.CREDENTIAL_VERIFICATION,
        [
            FakeConsent(
                ConsentPurpose.CREDENTIAL_VERIFICATION,
                ConsentStatus.REVOKED,
                datetime(2024, 6, 1, tzinfo=timezone.utc),
            )
        ],
    )
    assert not decision.allowed
    assert decision.status == ConsentStatus.REVOKED


def test_a_later_grant_reinstates_a_revoked_purpose():
    decision = consent_policy.evaluate(
        ConsentPurpose.CREDENTIAL_VERIFICATION,
        [
            FakeConsent(
                ConsentPurpose.CREDENTIAL_VERIFICATION,
                ConsentStatus.REVOKED,
                datetime(2024, 1, 1, tzinfo=timezone.utc),
            ),
            FakeConsent(
                ConsentPurpose.CREDENTIAL_VERIFICATION,
                ConsentStatus.GRANTED,
                datetime(2024, 6, 1, tzinfo=timezone.utc),
            ),
        ],
    )
    assert decision.allowed


def test_a_non_explicit_purpose_is_allowed_by_default():
    decision = consent_policy.evaluate(ConsentPurpose.ANALYTICS_AND_REPORTING, [])
    assert decision.allowed


def test_full_consent_requires_every_explicit_purpose():
    explicit = [
        purpose for purpose in ConsentPurpose if purpose.requires_explicit_consent
    ]
    assert not consent_policy.is_fully_consented([])
    assert consent_policy.is_fully_consented(
        [FakeConsent(purpose) for purpose in explicit]
    )


def test_the_blocking_purposes_are_listed():
    blocking = consent_policy.blocking_purposes(
        [FakeConsent(ConsentPurpose.CREDENTIAL_VERIFICATION)]
    )
    assert ConsentPurpose.CREDENTIAL_VERIFICATION not in blocking
    assert ConsentPurpose.DATA_SHARING_WITH_EMPLOYER in blocking


# ------------------------------------------------------------ audit chain


@dataclass
class FakeAudit:
    log_id: int = 1
    timestamp: datetime = datetime(2024, 1, 1, tzinfo=timezone.utc)
    actor: str = "aicte_admin"
    action: str = "LOGIN"
    subject: str = "USR-AICTE"
    details: str = "signed in"
    category: str = "SECURITY"
    prev_hash: str = ""
    hash: str = ""


def test_the_first_entry_links_to_the_genesis_hash():
    chained = audit_chain.chain([FakeAudit()])
    assert chained[0].prev_hash == audit_chain.GENESIS_HASH
    assert len(chained[0].hash) == 64


def test_a_freshly_chained_trail_verifies():
    chained = audit_chain.chain(
        [FakeAudit(log_id=index, details=f"event {index}") for index in range(1, 6)]
    )
    assert audit_chain.verify(chained)
    assert audit_chain.first_break(chained) is None


def test_an_altered_entry_breaks_the_chain():
    chained = audit_chain.chain(
        [FakeAudit(log_id=index, details=f"event {index}") for index in range(1, 6)]
    )
    chained[2].details = "tampered"
    assert not audit_chain.verify(chained)
    assert "altered" in audit_chain.first_break(chained)


def test_a_removed_entry_breaks_the_chain():
    chained = audit_chain.chain(
        [FakeAudit(log_id=index, details=f"event {index}") for index in range(1, 6)]
    )
    del chained[2]
    assert not audit_chain.verify(chained)


# ------------------------------------------------------------------- RBAC


def test_the_directorate_sees_the_national_picture():
    assert rbac.has_permission("aicte_admin", rbac.Permission.VIEW_NATIONAL_DASHBOARD)
    assert rbac.has_permission("aicte_admin", rbac.Permission.REVIEW_ANOMALIES)
    # The Directorate is the national authority, so it verifies credentials.
    assert rbac.has_permission("aicte_admin", rbac.Permission.VERIFY_CREDENTIAL)
    assert not rbac.has_permission("aicte_admin", rbac.Permission.ONBOARD_STUDENTS)
    # Institutions issue the certificates, not the regulator.
    assert not rbac.has_permission("aicte_admin", rbac.Permission.GENERATE_CERTIFICATE)


def test_an_institution_onboards_but_cannot_audit_the_nation():
    assert rbac.has_permission("institution_admin", rbac.Permission.ONBOARD_STUDENTS)
    assert rbac.has_permission("institution_admin", rbac.Permission.IMPORT_CSV)
    assert rbac.has_permission("institution_admin", rbac.Permission.GENERATE_CERTIFICATE)
    assert not rbac.has_permission("institution_admin", rbac.Permission.VIEW_NATIONAL_DASHBOARD)


def test_a_verifier_may_only_verify():
    assert rbac.has_permission("verifier", rbac.Permission.VERIFY_CREDENTIAL)
    assert not rbac.has_permission("verifier", rbac.Permission.EXPORT_REPORTS)


def test_a_student_sees_only_their_own_record():
    assert rbac.has_permission("student", rbac.Permission.VIEW_OWN_RECORD)
    assert not rbac.has_permission("student", rbac.Permission.VIEW_STUDENT_REGISTER)


def test_an_unknown_role_has_no_permissions():
    assert rbac.permissions_for("wizard") == frozenset()


# --------------------------------------------------------------- security


def test_a_password_round_trips():
    hashed = hash_password("Test@1234")
    assert hashed != "Test@1234"
    assert verify_password("Test@1234", hashed)
    assert not verify_password("wrong", hashed)


def test_the_password_policy_is_enforced():
    assert password_policy_violations("short")
    assert password_policy_violations("alllettersonly")
    assert password_policy_violations("12345678")
    assert password_policy_violations("Test@1234") == []


def test_a_pin_round_trips():
    salt = new_salt()
    hashed = hash_pin("Acadentrix2024", salt)
    assert verify_pin("Acadentrix2024", salt, hashed)
    assert not verify_pin("wrong", salt, hashed)


def test_two_salts_produce_two_hashes():
    assert hash_pin("Acadentrix2024", new_salt()) != hash_pin("Acadentrix2024", new_salt())


def test_an_access_token_round_trips():
    token = create_access_token("USR-AICTE", "aicte_admin", "INST-0421")
    claims = decode_token(token)
    assert claims["sub"] == "USR-AICTE"
    assert claims["role"] == "aicte_admin"
    assert claims["institution_id"] == "INST-0421"
    assert claims["type"] == "access"


def test_an_api_key_round_trips():
    from app.core.security import generate_api_key

    plain, hashed = generate_api_key()
    assert verify_api_key(plain, hashed)
    assert not verify_api_key("wrong", hashed)
