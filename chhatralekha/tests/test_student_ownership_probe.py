"""Probe: can a student-role (or verifier-role) account reach another student's data?

Each test asserts the SECURE behaviour. A failing test means the gap is real.
"""

from __future__ import annotations

import pytest

from tests.conftest import login
from tests.test_api import auth, create_student

OTHER = "984210357890"


@pytest.fixture
async def student_token(client):
    return await login(client, "student@chhatralekha.test")


@pytest.fixture
async def record(client, institution_token):
    response = await create_student(
        client,
        institution_token,
        apaar_id=OTHER,
        contact_email="someone.else@example.test",
        contact_phone="9999999999",
    )
    assert response.status_code == 201, response.text
    return OTHER


async def test_student_cannot_read_another_students_record(client, student_token, record):
    response = await client.get(f"/api/students/{record}", headers=auth(student_token))
    assert response.status_code == 403


async def test_student_cannot_read_another_students_consents(client, student_token, record):
    response = await client.get(f"/api/consent/{record}", headers=auth(student_token))
    assert response.status_code == 403


async def test_student_cannot_write_consent_for_another_student(client, student_token, record):
    response = await client.post(
        "/api/consent",
        json={"apaar_id": record, "purpose": "CREDENTIAL_VERIFICATION",
              "status": "GRANTED", "channel": "WEB_PORTAL"},
        headers=auth(student_token),
    )
    assert response.status_code == 403


async def test_student_cannot_get_certificate_of_another_student(client, student_token, record):
    response = await client.get(f"/api/students/{record}/certificate.pdf", headers=auth(student_token))
    assert response.status_code == 403


async def test_student_cannot_issue_token_for_another_student(client, student_token, record):
    response = await client.post(f"/api/students/{record}/token", headers=auth(student_token))
    assert response.status_code == 403


async def test_student_cannot_get_qr_of_another_student(client, student_token, record):
    response = await client.get(f"/api/students/{record}/qr", headers=auth(student_token))
    assert response.status_code == 403


async def test_verifier_record_lookup_does_not_expose_contact_details(client, verifier_token, record):
    response = await client.get(f"/api/students/{record}", headers=auth(verifier_token))
    if response.status_code == 200:
        body = response.json()
        leaked = [k for k in ("contact_email", "contact_phone", "date_of_birth") if body.get(k)]
        assert not leaked, f"verifier received personal fields: {leaked}"
    else:
        assert response.status_code == 403


async def test_unauthenticated_cannot_read_record(client, record):
    response = await client.get(f"/api/students/{record}")
    assert response.status_code in (401, 403)


async def test_linked_student_can_read_share_download_own_record(client, record):
    from app.core.database import mongo
    from app.core.security import create_access_token

    db = mongo.db()
    # Link a student user to the record
    await db["users"].insert_one({
        "user_id": "USR-OWNER-STU",
        "email": "owner.student@chhatralekha.test",
        "full_name": "Record Owner",
        "role": "student",
        "apaar_id": record,
        "institution_id": "INST-T1",
        "is_active": True,
    })

    token = create_access_token(
        subject="USR-OWNER-STU",
        role="student",
        institution_id="INST-T1",
        extra_claims={"apaar_id": record},
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Read own record
    res_record = await client.get(f"/api/students/{record}", headers=headers)
    assert res_record.status_code == 200
    assert res_record.json()["apaar_id"] == record

    # 2. Download own certificate
    res_cert = await client.get(f"/api/students/{record}/certificate.pdf", headers=headers)
    assert res_cert.status_code == 200
    assert res_cert.headers["content-type"] == "application/pdf"

    # 3. Issue own token
    res_tok = await client.post(f"/api/students/{record}/token", headers=headers)
    assert res_tok.status_code == 200
    assert "token" in res_tok.json()

    # 4. Fetch own QR badge
    res_qr = await client.get(f"/api/students/{record}/qr", headers=headers)
    assert res_qr.status_code == 200
    assert res_qr.headers["content-type"] == "image/png"

    # 5. Read own consent ledger
    res_consent = await client.get(f"/api/consent/{record}", headers=headers)
    assert res_consent.status_code == 200

    # 6. Write own consent
    res_grant = await client.post(
        "/api/consent",
        json={
            "apaar_id": record,
            "purpose": "CREDENTIAL_VERIFICATION",
            "status": "GRANTED",
            "channel": "WEB_PORTAL",
        },
        headers=headers,
    )
    assert res_grant.status_code == 201


async def test_student_with_institution_id_cannot_read_classmate(client, record):
    """Even if a student account has an institution id matching the target, they cannot read a classmate."""
    from app.core.database import mongo
    from app.core.security import create_access_token

    db = mongo.db()
    await db["users"].insert_one({
        "user_id": "USR-CLASSMATE-STU",
        "email": "classmate@chhatralekha.test",
        "full_name": "Classmate Student",
        "role": "student",
        "apaar_id": "111122223333",  # Different APAAR ID
        "institution_id": "INST-T1",  # Same institution as target record
        "is_active": True,
    })

    token = create_access_token(
        subject="USR-CLASSMATE-STU",
        role="student",
        institution_id="INST-T1",
        extra_claims={"apaar_id": "111122223333"},
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Must be rejected with 403 Forbidden
    res = await client.get(f"/api/students/{record}", headers=headers)
    assert res.status_code == 403

    res_consent = await client.get(f"/api/consent/{record}", headers=headers)
    assert res_consent.status_code == 403

    res_cert = await client.get(f"/api/students/{record}/certificate.pdf", headers=headers)
    assert res_cert.status_code == 403


async def test_institution_admin_cannot_read_another_institutions_student(client, institution_token):
    from app.core.database import mongo

    db = mongo.db()
    # Create student belonging to INST-T2
    other_inst_student = "222233334444"
    await db["students"].insert_one({
        "apaar_id": other_inst_student,
        "student_name": "Other Inst Student",
        "institution_id": "INST-T2",  # Different from institution_token (INST-T1)
        "program_id": "BTECH-CSE",
        "academic_year": "2024-2025",
        "is_active": True,
        "record_status": "ACTIVE",
    })

    # Institution admin of INST-T1 tries to read INST-T2 student
    res = await client.get(f"/api/students/{other_inst_student}", headers=auth(institution_token))
    assert res.status_code == 403

    res_consent = await client.get(f"/api/consent/{other_inst_student}", headers=auth(institution_token))
    assert res_consent.status_code == 403


async def test_national_admin_keeps_access_to_all_records(client, aicte_token, record):
    res_record = await client.get(f"/api/students/{record}", headers=auth(aicte_token))
    assert res_record.status_code == 200
    assert res_record.json()["apaar_id"] == record

    res_consent = await client.get(f"/api/consent/{record}", headers=auth(aicte_token))
    assert res_consent.status_code == 200


async def test_verifier_cannot_read_records_or_consent_directly(client, verifier_token, record):
    res_record = await client.get(f"/api/students/{record}", headers=auth(verifier_token))
    assert res_record.status_code == 403

    res_consent = await client.get(f"/api/consent/{record}", headers=auth(verifier_token))
    assert res_consent.status_code == 403

    res_list = await client.get("/api/students", headers=auth(verifier_token))
    assert res_list.status_code == 403


async def test_access_denied_writes_audit_log(client, student_token, record):
    from app.core.database import mongo
    from app.models.documents import redact_apaar

    db = mongo.db()
    await db["audit_events"].delete_many({"action": "ACCESS_DENIED"})

    res = await client.get(f"/api/students/{record}", headers=auth(student_token))
    assert res.status_code == 403

    denied_event = await db["audit_events"].find_one({
        "action": "ACCESS_DENIED",
        "subject": redact_apaar(record),
    })
    assert denied_event is not None
    assert denied_event["actor_role"] == "student"
    assert denied_event["category"] == "SECURITY"


