"""Comprehensive cross-institution isolation tests.

Verifies Epic A5, A6, A7 security guarantees:
1. Strict institutional tenant boundary on student records (read, update, lifecycle transitions).
2. Inter-institutional transfer workflow authorization (receiving inst requests, only relieving inst can release).
3. Anomaly reviewer assignment, case notes, and review decision tenant isolation.
4. Public credential verification PII allowlist and raw identifier suppression.
"""

from __future__ import annotations

import httpx
import pytest

from app.core.database import mongo
from app.core.security import hash_password
from app.models.enums import InstitutionType

TEST_PW_HASH = hash_password("Test@1234")

INST_A = "INST-ALPHA"
INST_B = "INST-BETA"
INST_C = "INST-GAMMA"

STUDENT_A_APAAR = "984210357890"
STUDENT_B_APAAR = "912345678901"


@pytest.fixture
async def multi_inst_db():
    db = mongo.db()

    # Seed institutions
    await db["institutions"].insert_many([
        {
            "institution_id": INST_A,
            "name": "Alpha Institute of Engineering",
            "institution_type": InstitutionType.ENGINEERING.value,
            "state": "Karnataka",
            "city": "Bengaluru",
            "affiliation_university": "VTU",
            "approval_year": 2010,
            "naac_grade": "A+",
            "is_active": True,
        },
        {
            "institution_id": INST_B,
            "name": "Beta College of Technology",
            "institution_type": InstitutionType.ENGINEERING.value,
            "state": "Maharashtra",
            "city": "Pune",
            "affiliation_university": "Pune University",
            "approval_year": 2012,
            "naac_grade": "A",
            "is_active": True,
        },
        {
            "institution_id": INST_C,
            "name": "Gamma Polytechnic",
            "institution_type": InstitutionType.POLYTECHNIC.value,
            "state": "Delhi",
            "city": "New Delhi",
            "affiliation_university": "BTE",
            "approval_year": 2015,
            "naac_grade": "B++",
            "is_active": True,
        },
    ])

    # Seed programmes
    await db["programmes"].insert_many([
        {
            "institution_id": INST_A,
            "program_id": "BTECH_CSE",
            "program_name": "B.Tech Computer Science",
            "program_level": "UG",
            "academic_year": "2024-25",
            "approved_intake": 60,
            "max_supernumerary_nri": 3,
            "max_supernumerary_fn_oci": 6,
            "max_supernumerary_tfw": 3,
            "max_pmsss": 3,
            "total_sanctioned": 75,
        },
        {
            "institution_id": INST_B,
            "program_id": "BTECH_IT",
            "program_name": "B.Tech Information Technology",
            "program_level": "UG",
            "academic_year": "2024-25",
            "approved_intake": 60,
            "max_supernumerary_nri": 3,
            "max_supernumerary_fn_oci": 6,
            "max_supernumerary_tfw": 3,
            "max_pmsss": 3,
            "total_sanctioned": 75,
        },
    ])

    # Seed users
    await db["users"].insert_many([
        {
            "user_id": "USR-ALPHA",
            "email": "alpha_admin@inst.test",
            "full_name": "Alpha Admin",
            "role": "institution_admin",
            "institution_id": INST_A,
            "password_hash": TEST_PW_HASH,
            "is_active": True,
        },
        {
            "user_id": "USR-BETA",
            "email": "beta_admin@inst.test",
            "full_name": "Beta Admin",
            "role": "institution_admin",
            "institution_id": INST_B,
            "password_hash": TEST_PW_HASH,
            "is_active": True,
        },
        {
            "user_id": "USR-GAMMA",
            "email": "gamma_admin@inst.test",
            "full_name": "Gamma Admin",
            "role": "institution_admin",
            "institution_id": INST_C,
            "password_hash": TEST_PW_HASH,
            "is_active": True,
        },
        {
            "user_id": "USR-AICTE-NAT",
            "email": "national@aicte.test",
            "full_name": "National Director",
            "role": "aicte_admin",
            "institution_id": None,
            "password_hash": TEST_PW_HASH,
            "is_active": True,
        },
    ])

    # Seed students
    await db["students"].insert_many([
        {
            "apaar_id": STUDENT_A_APAAR,
            "student_name": "Aarav Sharma",
            "date_of_birth": "2004-05-15",
            "gender": "M",
            "institution_id": INST_A,
            "program_id": "BTECH_CSE",
            "academic_year": "2024-25",
            "admission_quota": "REGULAR_MERIT",
            "enrollment_date": "2024-08-01",
            "student_institute_roll_no": "ALPHA-CSE-01",
            "nationality": "Indian",
            "social_category": "GENERAL",
            "record_status": "ACTIVE",
            "is_active": True,
            "contact_email": "aarav.sharma@example.com",
            "contact_phone": "+919876543210",
        },
        {
            "apaar_id": STUDENT_B_APAAR,
            "student_name": "Bhavna Patel",
            "date_of_birth": "2004-08-20",
            "gender": "F",
            "institution_id": INST_B,
            "program_id": "BTECH_IT",
            "academic_year": "2024-25",
            "admission_quota": "REGULAR_MERIT",
            "enrollment_date": "2024-08-01",
            "student_institute_roll_no": "BETA-IT-01",
            "nationality": "Indian",
            "social_category": "OBC",
            "record_status": "ACTIVE",
            "is_active": True,
            "contact_email": "bhavna.patel@example.com",
            "contact_phone": "+919876543211",
        },
    ])

    return db


async def _get_token(client: httpx.AsyncClient, email: str) -> str:
    res = await client.post("/api/auth/login", json={"email": email, "password": "Test@1234"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
async def http_client(multi_inst_db):
    from app.main import app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
async def token_alpha(http_client):
    return await _get_token(http_client, "alpha_admin@inst.test")


@pytest.fixture
async def token_beta(http_client):
    return await _get_token(http_client, "beta_admin@inst.test")


@pytest.fixture
async def token_gamma(http_client):
    return await _get_token(http_client, "gamma_admin@inst.test")


@pytest.fixture
async def token_aicte(http_client):
    return await _get_token(http_client, "national@aicte.test")


# -----------------------------------------------------------------------------
# Test 1: Cross-institution read isolation
# -----------------------------------------------------------------------------

async def test_cross_institution_read_isolation(http_client, token_alpha, token_beta, token_aicte):
    # Alpha reading Alpha's student -> OK
    res = await http_client.get(
        f"/api/students/{STUDENT_A_APAAR}",
        headers={"Authorization": f"Bearer {token_alpha}"},
    )
    assert res.status_code == 200
    assert res.json()["apaar_id"] == STUDENT_A_APAAR

    # Alpha reading Beta's student -> 403 Forbidden
    res = await http_client.get(
        f"/api/students/{STUDENT_B_APAAR}",
        headers={"Authorization": f"Bearer {token_alpha}"},
    )
    assert res.status_code == 403
    assert "another institution" in res.json()["detail"].lower()

    # Beta reading Alpha's student -> 403 Forbidden
    res = await http_client.get(
        f"/api/students/{STUDENT_A_APAAR}",
        headers={"Authorization": f"Bearer {token_beta}"},
    )
    assert res.status_code == 403

    # Beta reading Beta's student -> OK
    res = await http_client.get(
        f"/api/students/{STUDENT_B_APAAR}",
        headers={"Authorization": f"Bearer {token_beta}"},
    )
    assert res.status_code == 200

    # AICTE admin can read both
    res_a = await http_client.get(
        f"/api/students/{STUDENT_A_APAAR}",
        headers={"Authorization": f"Bearer {token_aicte}"},
    )
    res_b = await http_client.get(
        f"/api/students/{STUDENT_B_APAAR}",
        headers={"Authorization": f"Bearer {token_aicte}"},
    )
    assert res_a.status_code == 200
    assert res_b.status_code == 200


# -----------------------------------------------------------------------------
# Test 2: Cross-institution lifecycle transition and update isolation
# -----------------------------------------------------------------------------

async def test_cross_institution_update_and_lifecycle_isolation(http_client, token_alpha, token_beta):
    # Alpha attempting to update Beta's student -> 403
    update_res = await http_client.put(
        f"/api/students/{STUDENT_B_APAAR}",
        headers={"Authorization": f"Bearer {token_alpha}"},
        json={"student_name": "Hacked Name"},
    )
    assert update_res.status_code == 403

    # Alpha attempting lifecycle status change on Beta's student -> 403
    status_res = await http_client.post(
        f"/api/students/{STUDENT_B_APAAR}/status",
        headers={"Authorization": f"Bearer {token_alpha}"},
        json={"record_status": "ON_LEAVE", "reason": "Medical leave"},
    )
    assert status_res.status_code == 403

    # Alpha updating Alpha's student lifecycle status -> 200 OK
    status_ok = await http_client.post(
        f"/api/students/{STUDENT_A_APAAR}/status",
        headers={"Authorization": f"Bearer {token_alpha}"},
        json={"record_status": "ON_LEAVE", "reason": "Authorized research semester leave"},
    )
    assert status_ok.status_code == 200
    data = status_ok.json()
    assert data["record_status"] == "ON_LEAVE"


# -----------------------------------------------------------------------------
# Test 3: Inter-institutional transfer workflow & access controls
# -----------------------------------------------------------------------------

async def test_transfer_workflow_tenant_isolation(http_client, token_alpha, token_beta, token_gamma):
    # Beta initiates transfer request to receive Student A (currently in Alpha) into Beta's BTECH_IT program
    transfer_res = await http_client.post(
        "/api/transfers",
        headers={"Authorization": f"Bearer {token_beta}"},
        json={
            "apaar_id": STUDENT_A_APAAR,
            "to_institution_id": INST_B,
            "to_program_id": "BTECH_IT",
            "reason": "Family relocation from Bengaluru to Pune",
        },
    )
    assert transfer_res.status_code == 200, transfer_res.text
    transfer_data = transfer_res.json()
    transfer_id = transfer_data["transfer_id"]
    assert transfer_data["from_institution_id"] == INST_A
    assert transfer_data["to_institution_id"] == INST_B
    assert transfer_data["status"] == "SUBMITTED"

    # Gamma (third party) tries to view the transfer -> 403 Forbidden
    gamma_view = await http_client.get(
        f"/api/transfers/{transfer_id}",
        headers={"Authorization": f"Bearer {token_gamma}"},
    )
    assert gamma_view.status_code == 403

    # Beta (receiving inst) tries to approve the release -> 403 Forbidden
    # Only relieving institution (Alpha) can approve the student release!
    beta_approve = await http_client.post(
        f"/api/transfers/{transfer_id}/review",
        headers={"Authorization": f"Bearer {token_beta}"},
        json={"decision": "APPROVED", "notes": "Premature approval by receiving college"},
    )
    assert beta_approve.status_code == 403
    assert "relieving institution" in beta_approve.json()["detail"].lower()

    # Alpha (relieving inst) reviews and approves the transfer
    alpha_approve = await http_client.post(
        f"/api/transfers/{transfer_id}/review",
        headers={"Authorization": f"Bearer {token_alpha}"},
        json={"decision": "APPROVED", "notes": "No dues pending. NOC granted."},
    )
    assert alpha_approve.status_code == 200
    assert alpha_approve.json()["status"] == "APPROVED"

    # Verify that Student A's active record now belongs to INST-B with BTECH_IT
    student_record = await http_client.get(
        f"/api/students/{STUDENT_A_APAAR}",
        headers={"Authorization": f"Bearer {token_beta}"},
    )
    assert student_record.status_code == 200
    record_data = student_record.json()
    assert record_data["institution_id"] == INST_B
    assert record_data["program_id"] == "BTECH_IT"
    assert record_data["record_status"] == "ACTIVE"


# -----------------------------------------------------------------------------
# Test 4: Anomaly reviewer assignment, case notes, and review isolation
# -----------------------------------------------------------------------------

async def test_anomaly_case_management_isolation(http_client, token_alpha, token_beta, token_aicte):
    db = mongo.db()
    # Seed an anomaly belonging to Beta's student
    anomaly_obj = await db["anomalies"].insert_one({
        "anomaly_type": "EXCESS_APPROVED_INTAKE",
        "severity": "HIGH",
        "institution_id": INST_B,
        "program_id": "BTECH_IT",
        "apaar_id": STUDENT_B_APAAR,
        "description": "IT intake capacity exceeded by 1 student.",
        "status": "OPEN",
    })
    anomaly_id = str(anomaly_obj.inserted_id)

    # Institution Admins do not have national anomaly review privilege -> 403
    assign_fail = await http_client.post(
        f"/api/anomalies/{anomaly_id}/assign",
        headers={"Authorization": f"Bearer {token_alpha}"},
        json={"assignee_id": "USR-ALPHA", "assignee_name": "Alpha Staff"},
    )
    assert assign_fail.status_code == 403

    note_fail = await http_client.post(
        f"/api/anomalies/{anomaly_id}/notes",
        headers={"Authorization": f"Bearer {token_beta}"},
        json={"note_text": "Institution inquiry"},
    )
    assert note_fail.status_code == 403

    # AICTE admin reviewer assigns case
    assign_ok = await http_client.post(
        f"/api/anomalies/{anomaly_id}/assign",
        headers={"Authorization": f"Bearer {token_aicte}"},
        json={"assignee_id": "USR-AICTE-NAT", "assignee_name": "National Lead Reviewer"},
    )
    assert assign_ok.status_code == 200
    assert assign_ok.json()["assigned_to"] == "USR-AICTE-NAT"

    # AICTE admin reviewer adds case note
    note_ok = await http_client.post(
        f"/api/anomalies/{anomaly_id}/notes",
        headers={"Authorization": f"Bearer {token_aicte}"},
        json={"note_text": "Investigating supernumerary TFW allotment quota."},
    )
    assert note_ok.status_code == 200
    assert len(note_ok.json()["case_notes"]) >= 1

    # AICTE admin resolves with structured dismissal reason
    review_ok = await http_client.post(
        f"/api/anomalies/{anomaly_id}/review",
        headers={"Authorization": f"Bearer {token_aicte}"},
        json={"review_status": "DISMISSED", "reason": "SANCTIONED_SUPERNUMERARY", "explanation": "Verified under sanctioned TFW quota."},
    )
    assert review_ok.status_code == 200
    assert review_ok.json()["review_status"] == "DISMISSED"
    assert review_ok.json()["dismissal_reason"] == "SANCTIONED_SUPERNUMERARY"


# -----------------------------------------------------------------------------
# Test 5: Public verification PII allowlist and raw identifier suppression
# -----------------------------------------------------------------------------

async def test_public_verification_pii_suppression(http_client, token_beta):
    # Fetch Student B to get the mongo record_id
    student_res = await http_client.get(
        f"/api/students/{STUDENT_B_APAAR}",
        headers={"Authorization": f"Bearer {token_beta}"},
    )
    assert student_res.status_code == 200
    record_id = student_res.json()["record_id"]

    # Issue an opaque verification token for Student B
    token_resp = await http_client.post(
        "/api/verification-tokens",
        headers={"Authorization": f"Bearer {token_beta}"},
        json={"student_record_id": record_id},
    )
    assert token_resp.status_code == 201, token_resp.text
    raw_token = token_resp.json()["token"]

    # Public verification lookup (unauthenticated external verifier)
    verify_resp = await http_client.get(f"/api/verify/token/{raw_token}")
    assert verify_resp.status_code == 200
    body = verify_resp.json()

    # Verified payload MUST NOT expose raw APAAR ID or sensitive personal data
    assert body.get("valid") is True
    assert body.get("verdict") == "VALID"
    assert body.get("institution") == INST_B
    assert body.get("programme") == "BTECH_IT"

    # Strictly verify suppression of private personal data
    serialised = verify_resp.text
    assert STUDENT_B_APAAR not in serialised
    assert "2004-08-20" not in serialised
    assert "Bhavna Patel" not in serialised
    assert "+919876543211" not in serialised
    assert "bhavna.patel@example.com" not in serialised
    assert "apaar_id" not in body
    assert "date_of_birth" not in body

    # Allowlist check: returned keys must be a subset of safe metadata keys
    assert set(body) <= {
        "valid",
        "verdict",
        "reason",
        "record_status",
        "institution",
        "programme",
        "academic_year",
        "issued_at",
        "expires_at",
        "needs_refresh",
        "notice",
    }
