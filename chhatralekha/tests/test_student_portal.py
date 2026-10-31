"""Tests for Phase 0: Student ownership security and authorization tightening."""

from __future__ import annotations

import pytest

from app.core.security import hash_password


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
TEST_PASSWORD_HASH = hash_password("Test@1234")


@pytest.fixture
async def multi_students_setup(client, seeded, users):
    """Seed two students at the same institution and one student at another institution."""
    db = client._transport.app.state.db if hasattr(client._transport.app.state, "db") else None
    from app.core.database import mongo
    db = mongo.db()

    # Second institution
    await db["institutions"].insert_one({
        "institution_id": "INST-T2",
        "name": "Second Tech Institute",
        "institution_type": "ENGINEERING",
        "is_active": True,
    })
    await db["programmes"].insert_one({
        "institution_id": "INST-T2",
        "program_id": "BTECH_ECE",
        "program_name": "ECE",
        "approved_intake": 10,
        "is_active": True,
    })

    # Student 1 at INST-T1 (Aakash Verma)
    await db["students"].insert_one({
        "apaar_id": "984210357890",
        "student_name": "Aakash Verma",
        "date_of_birth": "2004-03-12",
        "gender": "M",
        "institution_id": "INST-T1",
        "program_id": "BTECH_CSE",
        "academic_year": "2024-25",
        "admission_quota": "REGULAR_MERIT",
        "enrollment_date": "2024-08-01",
        "record_status": "ACTIVE",
        "student_institute_roll_no": "CSE-0001",
    })

    # Student 2 at INST-T1 (Priya Sharma - same institution)
    await db["students"].insert_one({
        "apaar_id": "841295304812",
        "student_name": "Priya Sharma",
        "date_of_birth": "2004-07-22",
        "gender": "F",
        "institution_id": "INST-T1",
        "program_id": "BTECH_CSE",
        "academic_year": "2024-25",
        "admission_quota": "REGULAR_MERIT",
        "enrollment_date": "2024-08-01",
        "record_status": "ACTIVE",
        "student_institute_roll_no": "CSE-0002",
    })

    # Student 3 at INST-T2 (Rahul Sen - different institution)
    await db["students"].insert_one({
        "apaar_id": "713490285167",
        "student_name": "Rahul Sen",
        "date_of_birth": "2003-11-05",
        "gender": "M",
        "institution_id": "INST-T2",
        "program_id": "BTECH_ECE",
        "academic_year": "2024-25",
        "admission_quota": "REGULAR_MERIT",
        "enrollment_date": "2024-08-01",
        "record_status": "ACTIVE",
        "student_institute_roll_no": "ECE-0001",
    })

    # User account for Student A (Aakash Verma, linked to 984210357890, institution INST-T1)
    await db["users"].insert_one({
        "user_id": "USR-STU-A",
        "email": "aakash@student.test",
        "full_name": "Aakash Verma",
        "role": "student",
        "institution_id": "INST-T1",
        "apaar_id": "984210357890",
        "password_hash": TEST_PASSWORD_HASH,
        "is_active": True,
    })

    # User account for Student B (Priya Sharma, linked to 841295304812, institution INST-T1)
    await db["users"].insert_one({
        "user_id": "USR-STU-B",
        "email": "priya@student.test",
        "full_name": "Priya Sharma",
        "role": "student",
        "institution_id": "INST-T1",
        "apaar_id": "841295304812",
        "password_hash": TEST_PASSWORD_HASH,
        "is_active": True,
    })

    # User account for Unlinked Student (no institution_id, no apaar_id)
    await db["users"].insert_one({
        "user_id": "USR-STU-UNLINKED",
        "email": "unlinked@student.test",
        "full_name": "Unlinked Student",
        "role": "student",
        "institution_id": None,
        "apaar_id": None,
        "password_hash": TEST_PASSWORD_HASH,
        "is_active": True,
    })

    return db


async def _login(client, email):
    res = await client.post("/api/auth/login", json={"email": email, "password": "Test@1234"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


async def test_student_cannot_read_another_students_record_same_institution(client, multi_students_setup):
    token_a = await _login(client, "aakash@student.test")
    # Student A requests Student B's record (Priya: 841295304812) at the same institution (INST-T1)
    res = await client.get("/api/students/841295304812", headers=auth(token_a))
    # Must fail with 403 Forbidden!
    assert res.status_code == 403


async def test_student_cannot_read_another_students_record_diff_institution(client, multi_students_setup):
    token_a = await _login(client, "aakash@student.test")
    # Student A requests Student C's record (Rahul: 713490285167) at different institution (INST-T2)
    res = await client.get("/api/students/713490285167", headers=auth(token_a))
    assert res.status_code == 403


async def test_unlinked_student_cannot_read_anyone_else_record(client, multi_students_setup):
    token_unlinked = await _login(client, "unlinked@student.test")
    # Unlinked student requests Student A's record
    res = await client.get("/api/students/984210357890", headers=auth(token_unlinked))
    assert res.status_code == 403


async def test_student_cannot_generate_another_students_certificate(client, multi_students_setup):
    token_a = await _login(client, "aakash@student.test")
    # Student A tries to generate certificate for Student B (Priya, same institution)
    res = await client.get("/api/students/841295304812/certificate.pdf", headers=auth(token_a))
    assert res.status_code == 403


async def test_student_can_read_own_record_and_certificate(client, multi_students_setup):
    token_a = await _login(client, "aakash@student.test")
    res_get = await client.get("/api/students/984210357890", headers=auth(token_a))
    assert res_get.status_code == 200
    assert res_get.json()["student_name"] == "Aakash Verma"

    res_cert = await client.get("/api/students/984210357890/certificate.pdf", headers=auth(token_a))
    assert res_cert.status_code == 200
    assert res_cert.headers["content-type"] == "application/pdf"


async def test_student_cannot_issue_another_students_token_or_badge(client, multi_students_setup):
    token_a = await _login(client, "aakash@student.test")
    # Student A tries to issue token for Student B (Priya, same institution)
    res_tok = await client.post("/api/students/841295304812/token", headers=auth(token_a))
    assert res_tok.status_code == 403

    # Student A tries to fetch badge/qr for Student B
    res_badge = await client.get("/api/students/841295304812/qr", headers=auth(token_a))
    assert res_badge.status_code == 403

    # Student A can issue token and badge for self
    res_own_tok = await client.post("/api/students/984210357890/token", headers=auth(token_a))
    assert res_own_tok.status_code == 200
    assert "token" in res_own_tok.json()

    res_own_badge = await client.get("/api/students/984210357890/qr", headers=auth(token_a))
    assert res_own_badge.status_code == 200
    assert res_own_badge.headers["content-type"] == "image/png"


async def test_institution_keeps_access_to_own_students(client, multi_students_setup, institution_token):
    # Principal of INST-T1 can read students at INST-T1
    res = await client.get("/api/students/984210357890", headers=auth(institution_token))
    assert res.status_code == 200
    # Principal of INST-T1 cannot read student at INST-T2
    res_diff = await client.get("/api/students/713490285167", headers=auth(institution_token))
    assert res_diff.status_code == 403



# ------------------------------------------------------------------- Phase 0.3: Claim Flow


async def test_claim_flow(client, multi_students_setup, institution_token):
    # 1. Institution generates claim code for Student 2 (Priya Sharma, 841295304812)
    res_code = await client.post(
        "/api/students/841295304812/claim-code", headers=auth(institution_token)
    )
    assert res_code.status_code == 200, res_code.text
    claim_code = res_code.json()["claim_code"]
    assert claim_code.startswith("CL-")

    # 2. Unlinked student claims code
    token_unlinked = await _login(client, "unlinked@student.test")
    res_claim = await client.post(
        "/api/me/claim", json={"claim_code": claim_code}, headers=auth(token_unlinked)
    )
    assert res_claim.status_code == 200, res_claim.text
    assert res_claim.json()["apaar_id"] == "841295304812"

    # 3. Trying to reuse same claim code fails
    res_reuse = await client.post(
        "/api/me/claim", json={"claim_code": claim_code}, headers=auth(token_unlinked)
    )
    assert res_reuse.status_code == 400

    # 4. Profile now resolves to Priya Sharma
    res_profile = await client.get("/api/me/profile", headers=auth(token_unlinked))
    assert res_profile.status_code == 200
    assert res_profile.json()["student_name"] == "Priya Sharma"


# ------------------------------------------------------------------- Phase 1: ID Card


async def test_student_id_card(client, multi_students_setup):
    token_a = await _login(client, "aakash@student.test")
    res = await client.get("/api/me/id-card", headers=auth(token_a))
    assert res.status_code == 200
    card = res.json()
    assert card["student_name"] == "Aakash Verma"
    assert card["chhatralekha_student_id"].startswith("CL-STU-")
    assert card["token"]
    assert "/verify/t/" in card["token_url"]


# ------------------------------------------------------------------- Phase 2: Share Links


async def test_student_controlled_share_links(client, multi_students_setup):
    token_a = await _login(client, "aakash@student.test")

    # Create 24h share with default fields (no name)
    res_share = await client.post(
        "/api/me/shares",
        json={"expiry_hours": 24, "allowed_fields": ["programme", "status"], "include_name": False},
        headers=auth(token_a),
    )
    assert res_share.status_code == 200
    share_data = res_share.json()
    token_val = share_data["token"]
    token_id = share_data["token_id"]

    # Public verification allows programme and status, suppresses institution
    res_pub = await client.get(f"/api/verify/token/{token_val}")
    assert res_pub.status_code == 200
    pub = res_pub.json()
    assert pub["valid"] is True
    assert pub["verdict"] == "VALID"
    assert pub["programme"] == "BTECH_CSE"
    assert pub["institution"] == ""

    # Revoke share link
    res_rev = await client.post(f"/api/me/shares/{token_id}/revoke", headers=auth(token_a))
    assert res_rev.status_code == 200
    assert res_rev.json()["status"] == "REVOKED"

    # Public verification immediately reflects REVOKED
    res_pub_after = await client.get(f"/api/verify/token/{token_val}")
    assert res_pub_after.status_code == 200
    assert res_pub_after.json()["valid"] is False
    assert res_pub_after.json()["verdict"] == "REVOKED"


# ------------------------------------------------------------------- Phase 3: Wallet


async def test_student_wallet(client, multi_students_setup):
    token_a = await _login(client, "aakash@student.test")
    res = await client.get("/api/me/wallet", headers=auth(token_a))
    assert res.status_code == 200
    body = res.json()
    assert len(body["credentials"]) >= 2
    types = [c["type"] for c in body["credentials"]]
    assert "BONAFIDE" in types
    assert "DEGREE" in types


# ------------------------------------------------------------------- Phase 4: Consent


async def test_student_consent_centre(client, multi_students_setup):
    token_a = await _login(client, "aakash@student.test")

    # 1. Read current consent status
    res_get = await client.get("/api/me/consent", headers=auth(token_a))
    assert res_get.status_code == 200
    assert len(res_get.json()["purposes"]) >= 4

    # 2. Revoke a consent
    res_post = await client.post(
        "/api/me/consent",
        json={"purpose": "EMPLOYMENT_VERIFICATION", "status": "REVOKED"},
        headers=auth(token_a),
    )
    assert res_post.status_code == 200
    assert res_post.json()["new_status"] == "REVOKED"

    # 3. Grant it back
    res_grant = await client.post(
        "/api/me/consent",
        json={"purpose": "EMPLOYMENT_VERIFICATION", "status": "GRANTED"},
        headers=auth(token_a),
    )
    assert res_grant.status_code == 200
    assert res_grant.json()["new_status"] == "GRANTED"


# ------------------------------------------------------------------- Phase 5: Uploads & OCR Review


async def test_student_upload_and_institutional_review(client, multi_students_setup, institution_token):
    token_a = await _login(client, "aakash@student.test")

    # 1. Student uploads marksheet
    sample_marksheet = b"""
    DELHI INSTITUTE OF TECHNOLOGY
    OFFICIAL TRANSCRIPT OF GRADES
    Student Name: Aakash Verma
    APAAR ID: 984210357890
    Roll Number: CSE-0001
    Programme: BTECH_CSE
    CGPA: 8.75
    """
    res_upload = await client.post(
        "/api/me/uploads",
        files={"file": ("transcript.txt", sample_marksheet, "text/plain")},
        headers=auth(token_a),
    )
    assert res_upload.status_code == 200
    data = res_upload.json()
    upload_id = data["upload_id"]
    assert data["status"] == "PENDING_REVIEW"
    assert data["requires_human_approval"] is True
    assert "student_name" in data["matched_fields"]

    # 2. Student lists uploads
    res_list = await client.get("/api/me/uploads", headers=auth(token_a))
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 3. Institution approves submission
    res_review = await client.post(
        f"/api/students/submissions/{upload_id}/review",
        json={"decision": "APPROVED", "notes": "Verified against physical grade ledger."},
        headers=auth(institution_token),
    )
    assert res_review.status_code == 200
    assert res_review.json()["status"] == "APPROVED"

    # 4. Approved document now appears in student wallet
    res_wallet = await client.get("/api/me/wallet", headers=auth(token_a))
    assert res_wallet.status_code == 200
    wallet_creds = res_wallet.json()["credentials"]
    assert any(c["type"] == "VERIFIED_MARKSHEET" for c in wallet_creds)


# ------------------------------------------------------------------- Phase 6: Notifications & Activity


async def test_student_notifications_and_activity(client, multi_students_setup):
    token_a = await _login(client, "aakash@student.test")

    # Notifications
    res_notifs = await client.get("/api/me/notifications", headers=auth(token_a))
    assert res_notifs.status_code == 200

    # Activity timeline
    res_act = await client.get("/api/me/activity", headers=auth(token_a))
    assert res_act.status_code == 200
    assert isinstance(res_act.json(), list)


# ------------------------------------------------------------------- Phase 7: Results & Analytics


async def test_student_results_and_cgpa(client, multi_students_setup):
    token_a = await _login(client, "aakash@student.test")
    res = await client.get("/api/me/results", headers=auth(token_a))
    assert res.status_code == 200
    data = res.json()
    assert "cgpa" in data
    assert data["cgpa"] > 0
    assert len(data["semesters"]) >= 1
    assert data["total_credits_earned"] > 0
