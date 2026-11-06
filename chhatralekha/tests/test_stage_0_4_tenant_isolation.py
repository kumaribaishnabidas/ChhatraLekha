"""Stage 0.4: Tenant Isolation and Access Control Verification Tests.

Comprehensive cross-institution regression test suite for:
1. Missing institution context failing closed (HTTP 400).
2. Cross-institution isolation on academic setup, classes, and departments.
3. Cross-institution announcement isolation and acknowledgement rejection (HTTP 403).
4. Cross-institution reports, CSV exports, and data leak prevention.
5. Cross-institution attendance sessions, records, reports, and correction reviews.
6. Cross-institution student transfers and audit review tasks.
7. Cross-institution anomaly isolation and reviewer assignment.
8. Explicitly authorized platform administration (Directorate/AICTE Admin) access preserved.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import mongo
from app.core.security import create_access_token
from app.main import app

INST_A = "INST-AAA"
INST_B = "INST-BBB"


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http


@pytest.fixture
async def seeded_institutions():
    """Seed synthetic Institution A and Institution B and active users into the database."""
    db: AsyncIOMotorDatabase = mongo.db()
    await db["institutions"].insert_many([
        {
            "_id": INST_A,
            "institution_id": INST_A,
            "name": "Synthetic Institute Alpha",
            "institution_type": "ENGINEERING",
            "state": "Maharashtra",
            "city": "Mumbai",
            "is_active": True,
        },
        {
            "_id": INST_B,
            "institution_id": INST_B,
            "name": "Synthetic Institute Beta",
            "institution_type": "ENGINEERING",
            "state": "Karnataka",
            "city": "Bengaluru",
            "is_active": True,
        },
    ])
    await db["users"].insert_many([
        {"user_id": "USR-ADM-A", "email": "admin_a@alpha.test", "role": "institution_admin", "institution_id": INST_A, "is_active": True},
        {"user_id": "USR-ADM-B", "email": "admin_b@beta.test", "role": "institution_admin", "institution_id": INST_B, "is_active": True},
        {"user_id": "USR-ADM-NONE", "email": "admin_none@test.test", "role": "institution_admin", "institution_id": None, "is_active": True},
        {"user_id": "USR-TCH-A", "email": "teacher_a@alpha.test", "role": "teacher", "institution_id": INST_A, "is_active": True},
        {"user_id": "USR-TCH-B", "email": "teacher_b@beta.test", "role": "teacher", "institution_id": INST_B, "is_active": True},
        {"user_id": "USR-STU-A", "email": "student_a@alpha.test", "role": "student", "institution_id": INST_A, "apaar_id": "999900000001", "is_active": True},
        {"user_id": "USR-STU-B", "email": "student_b@beta.test", "role": "student", "institution_id": INST_B, "apaar_id": "999900000002", "is_active": True},
        {"user_id": "USR-AICTE", "email": "aicte@directorate.test", "role": "aicte_admin", "institution_id": None, "is_active": True},
        {"user_id": "USR-NAT", "email": "national@directorate.test", "role": "national_admin", "institution_id": None, "is_active": True},
    ])
    return db


@pytest.fixture
def tokens():
    return {
        "admin_a": create_access_token(subject="USR-ADM-A", role="institution_admin", institution_id=INST_A),
        "admin_b": create_access_token(subject="USR-ADM-B", role="institution_admin", institution_id=INST_B),
        "admin_unattached": create_access_token(subject="USR-ADM-NONE", role="institution_admin", institution_id=None),
        "teacher_a": create_access_token(subject="USR-TCH-A", role="teacher", institution_id=INST_A),
        "teacher_b": create_access_token(subject="USR-TCH-B", role="teacher", institution_id=INST_B),
        "student_a": create_access_token(subject="USR-STU-A", role="student", institution_id=INST_A),
        "student_b": create_access_token(subject="USR-STU-B", role="student", institution_id=INST_B),
        "aicte_admin": create_access_token(subject="USR-AICTE", role="aicte_admin", institution_id=None),
        "national_admin": create_access_token(subject="USR-NAT", role="national_admin", institution_id=None),
    }


# --------------------------------------------------------------------------
# 1. Missing Institution Context Fails Closed
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_missing_institution_context_fails_closed(client: AsyncClient, seeded_institutions, tokens):
    """Institutional users missing tenant context must fail closed with HTTP 400."""
    headers = auth_header(tokens["admin_unattached"])

    # Academic years listing
    resp = await client.get("/api/academic/years", headers=headers)
    assert resp.status_code == 400
    assert "institution" in resp.json()["detail"].lower()

    # Academic classes listing
    resp = await client.get("/api/academic/classes", headers=headers)
    assert resp.status_code == 400
    assert "institution" in resp.json()["detail"].lower()

    # Announcements listing
    resp = await client.get("/api/announcements", headers=headers)
    assert resp.status_code == 400
    assert "institution" in resp.json()["detail"].lower()

    # Attendance sessions
    resp = await client.get("/api/attendance/sessions", headers=headers)
    assert resp.status_code == 400
    assert "institution" in resp.json()["detail"].lower()

    # Attendance CSV export
    resp = await client.get("/api/attendance/reports/export-csv", headers=headers)
    assert resp.status_code == 400
    assert "institution" in resp.json()["detail"].lower()


# --------------------------------------------------------------------------
# 2. Cross-Institution Academic Setup Isolation
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_institution_academic_isolation(client: AsyncClient, seeded_institutions, tokens):
    """Users of Institution A cannot read or mutate academic resources of Institution B."""
    db: AsyncIOMotorDatabase = mongo.db()

    # Seed academic years in A and B
    await db["academic_years"].insert_many([
        {"_id": "AY-A-2026", "id": "AY-A-2026", "institution_id": INST_A, "name": "2026-27 Alpha", "code": "2026-27", "status": "UPCOMING", "is_current": False},
        {"_id": "AY-B-2026", "id": "AY-B-2026", "institution_id": INST_B, "name": "2026-27 Beta", "code": "2026-27", "status": "UPCOMING", "is_current": False},
    ])

    # Seed classes in A and B
    await db["classes"].insert_many([
        {"_id": "CLS-A-01", "class_id": "CLS-A-01", "institution_id": INST_A, "name": "Grade 10 Alpha", "grade_level": "10", "section": "A", "status": "ACTIVE"},
        {"_id": "CLS-B-01", "class_id": "CLS-B-01", "institution_id": INST_B, "name": "Grade 10 Beta", "grade_level": "10", "section": "B", "status": "ACTIVE"},
    ])

    # Admin A reads academic years
    res_a = await client.get("/api/academic/years", headers=auth_header(tokens["admin_a"]))
    assert res_a.status_code == 200
    years_a = res_a.json()
    assert len(years_a) == 1
    assert years_a[0]["institution_id"] == INST_A

    # Admin A attempts to bypass scope with query parameter institution_id=INST-BBB -> 403 Forbidden
    res_spoof = await client.get(f"/api/academic/years?institution_id={INST_B}", headers=auth_header(tokens["admin_a"]))
    assert res_spoof.status_code == 403

    # Admin A attempts to activate / archive Institution B's academic year -> 403 Forbidden
    res_act = await client.post("/api/academic/years/AY-B-2026/activate", headers=auth_header(tokens["admin_a"]))
    assert res_act.status_code == 403

    res_arch = await client.post("/api/academic/years/AY-B-2026/archive", headers=auth_header(tokens["admin_a"]))
    assert res_arch.status_code == 403

    # Admin A queries classes -> receives only A's classes
    res_cls = await client.get("/api/academic/classes", headers=auth_header(tokens["admin_a"]))
    assert res_cls.status_code == 200
    classes = res_cls.json()
    assert len(classes) == 1
    assert classes[0]["institution_id"] == INST_A


# --------------------------------------------------------------------------
# 3. Cross-Institution Announcements & Acknowledgement Isolation
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_institution_announcements_and_acknowledgement(client: AsyncClient, seeded_institutions, tokens):
    """Students/Staff of Institution A cannot read or acknowledge notices of Institution B."""
    db: AsyncIOMotorDatabase = mongo.db()

    # Seed announcement for B
    await db["announcements"].insert_one({
        "_id": "ANN-B-001",
        "announcement_id": "ANN-B-001",
        "institution_id": INST_B,
        "title": "Beta Internal Holiday Notice",
        "content": "Campus B will be closed on Friday.",
        "priority": "NORMAL",
        "target_scope": "ALL",
        "status": "PUBLISHED",
        "is_national": False,
        "acknowledgements": [],
    })

    # Student A reads announcements
    res_a = await client.get("/api/announcements", headers=auth_header(tokens["student_a"]))
    assert res_a.status_code == 200
    notices_a = res_a.json()
    assert all(n["institution_id"] == INST_A or n.get("is_national") for n in notices_a)
    assert not any(n["announcement_id"] == "ANN-B-001" for n in notices_a)

    # Student A attempts to acknowledge B's notice -> 403 Forbidden (Requirement 8)
    ack_res = await client.post("/api/announcements/ANN-B-001/acknowledge", headers=auth_header(tokens["student_a"]))
    assert ack_res.status_code == 403
    assert "not allowed" in ack_res.json()["detail"].lower()

    # Student B acknowledges B's notice -> 200 OK
    ack_ok = await client.post("/api/announcements/ANN-B-001/acknowledge", headers=auth_header(tokens["student_b"]))
    assert ack_ok.status_code == 200

    # Admin A attempts to view B's delivery summary -> 403 Forbidden
    sum_res = await client.get("/api/announcements/ANN-B-001/delivery-summary", headers=auth_header(tokens["admin_a"]))
    assert sum_res.status_code == 403


# --------------------------------------------------------------------------
# 4. Cross-Institution Reports and Safe Export Isolation
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_institution_reports_and_export_isolation(client: AsyncClient, seeded_institutions, tokens):
    """Institutional administrators cannot export other institutions' reports or data."""
    db: AsyncIOMotorDatabase = mongo.db()

    # Seed student in A and B
    await db["students"].insert_many([
        {"apaar_id": "999900000001", "student_name": "Student Alpha", "institution_id": INST_A, "record_status": "ACTIVE"},
        {"apaar_id": "999900000002", "student_name": "Student Beta", "institution_id": INST_B, "record_status": "ACTIVE"},
    ])

    # Admin A requests students CSV with ?institution_id=INST-BBB -> 403 Forbidden
    resp_cross = await client.get(f"/api/reports/students.csv?institution_id={INST_B}", headers=auth_header(tokens["admin_a"]))
    assert resp_cross.status_code == 403

    # Admin A requests own students CSV -> 200 OK with only Alpha students
    resp_csv = await client.get("/api/reports/students.csv", headers=auth_header(tokens["admin_a"]))
    assert resp_csv.status_code == 200
    csv_text = resp_csv.text
    assert "Student Alpha" in csv_text
    assert "Student Beta" not in csv_text

    # Seed anomaly in B
    await db["anomalies"].insert_one({
        "_id": "ANOM-B-01",
        "anomaly_id": "ANOM-B-01",
        "institution_id": INST_B,
        "rule_code": "INTAKE_BREACH",
        "severity": "CRITICAL",
        "status": "OPEN",
    })

    # Admin A attempts to export B's anomalies CSV -> 403 Forbidden
    resp_anom_csv = await client.get(f"/api/reports/anomalies.csv?institution_id={INST_B}", headers=auth_header(tokens["admin_a"]))
    assert resp_anom_csv.status_code == 403

    # Admin A attempts to export B's utilisation CSV -> 403 Forbidden
    resp_util = await client.get(f"/api/reports/utilisation.csv?institution_id={INST_B}", headers=auth_header(tokens["admin_a"]))
    assert resp_util.status_code == 403


# --------------------------------------------------------------------------
# 5. Cross-Institution Attendance Isolation and Correction Review
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_institution_attendance_isolation(client: AsyncClient, seeded_institutions, tokens):
    """Attendance sessions, records, corrections, and summaries are strictly tenant-isolated."""
    db: AsyncIOMotorDatabase = mongo.db()

    # Seed attendance session and record for Beta
    await db["attendance_sessions"].insert_one({
        "_id": "SES-B-001",
        "session_id": "SES-B-001",
        "institution_id": INST_B,
        "target_id": "CLS-B-01",
        "target_label": "Grade 10 Beta",
        "session_date": "2026-11-06",
        "status": "COMPLETED",
        "total_students": 1,
        "present_count": 1,
    })
    await db["attendance_records"].insert_one({
        "_id": "REC-B-001",
        "session_id": "SES-B-001",
        "student_id": "STU-B-01",
        "student_name": "Student Beta",
        "institution_id": INST_B,
        "status": "PRESENT",
        "session_date": "2026-11-06",
    })

    # Admin A queries session detail of B -> 403 Forbidden
    res_ses = await client.get("/api/attendance/sessions/SES-B-001", headers=auth_header(tokens["admin_a"]))
    assert res_ses.status_code == 403

    # Seed attendance correction in Beta
    await db["attendance_corrections"].insert_one({
        "_id": "CORR-B-001",
        "id": "CORR-B-001",
        "institution_id": INST_B,
        "session_id": "SES-B-001",
        "student_id": "STU-B-01",
        "student_name": "Student Beta",
        "previous_status": "PRESENT",
        "requested_status": "LATE",
        "status": "PENDING",
        "reason": "Medical leave",
        "session_date": "2026-11-06",
    })

    # Admin A attempts to review / approve Beta's correction -> 403 Forbidden
    rev_res = await client.post(
        "/api/attendance/corrections/CORR-B-001/review",
        json={"decision": "APPROVE", "review_notes": "Cross-institution review attempt"},
        headers=auth_header(tokens["admin_a"]),
    )
    assert rev_res.status_code == 403

    # Admin B approves Beta's correction -> 200 OK
    rev_ok = await client.post(
        "/api/attendance/corrections/CORR-B-001/review",
        json={"decision": "APPROVE", "review_notes": "Authorized review"},
        headers=auth_header(tokens["admin_b"]),
    )
    assert rev_ok.status_code == 200
    assert rev_ok.json()["status"] == "APPROVED"


# --------------------------------------------------------------------------
# 6. Cross-Institution Student Transfers & Review Tasks Isolation
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_institution_transfers_and_review_tasks(client: AsyncClient, seeded_institutions, tokens):
    """Transfer requests and audit review tasks are strictly tenant-isolated."""
    db: AsyncIOMotorDatabase = mongo.db()

    # Seed transfer from Beta to another institution
    await db["transfers"].insert_one({
        "_id": "TRF-B-001",
        "transfer_id": "TRF-B-001",
        "from_institution_id": INST_B,
        "to_institution_id": "INST-OTHER",
        "student_id": "STU-B-01",
        "status": "SUBMITTED",
    })

    # Admin A attempts to view B's transfer -> 403 Forbidden
    res_trf = await client.get("/api/transfers/TRF-B-001", headers=auth_header(tokens["admin_a"]))
    assert res_trf.status_code == 403

    # Admin A attempts to review B's transfer -> 403 Forbidden
    res_rev_trf = await client.post(
        "/api/transfers/TRF-B-001/review",
        json={"decision": "APPROVED", "notes": "Unauthorized review attempt"},
        headers=auth_header(tokens["admin_a"]),
    )
    assert res_rev_trf.status_code == 403

    # Seed review task in Beta
    await db["review_tasks"].insert_one({
        "_id": "TASK-B-001",
        "task_id": "TASK-B-001",
        "institution_id": INST_B,
        "status": "PENDING",
        "review_type": "DATA_AUDIT",
    })

    # Admin A lists review tasks with query ?institution_id=INST-BBB -> 403 Forbidden
    res_tasks = await client.get(f"/api/review-tasks?institution_id={INST_B}", headers=auth_header(tokens["admin_a"]))
    assert res_tasks.status_code == 403

    # Admin A attempts to update Beta's task -> 403 Forbidden
    res_task_upd = await client.patch(
        "/api/review-tasks/TASK-B-001",
        json={"status": "APPROVED", "notes": "Unauthorized attempt"},
        headers=auth_header(tokens["admin_a"]),
    )
    assert res_task_upd.status_code == 403


# --------------------------------------------------------------------------
# 7. Cross-Institution Anomaly Isolation
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_institution_anomaly_isolation(client: AsyncClient, seeded_institutions, tokens):
    """Anomalies of Institution B cannot be inspected or reviewed by Institution A."""
    db: AsyncIOMotorDatabase = mongo.db()

    await db["anomalies"].insert_one({
        "_id": "ANOM-B-99",
        "anomaly_id": "ANOM-B-99",
        "institution_id": INST_B,
        "rule_code": "INTAKE_BREACH",
        "severity": "HIGH",
        "status": "OPEN",
    })

    # Admin A attempts to list anomalies -> 403 Forbidden (Institution Admin lacks REVIEW_ANOMALIES)
    res_anom = await client.get(f"/api/anomalies?institution_id={INST_B}", headers=auth_header(tokens["admin_a"]))
    assert res_anom.status_code == 403

    # Admin A attempts to assign reviewer to Beta anomaly -> 403 Forbidden
    res_assign = await client.post(
        "/api/anomalies/ANOM-B-99/assign",
        json={"assigned_to": "USR-ADM-A", "notes": "Unauthorized assignment"},
        headers=auth_header(tokens["admin_a"]),
    )
    assert res_assign.status_code == 403

    # Admin A attempts to append case note to Beta anomaly -> 403 Forbidden
    res_note = await client.post(
        "/api/anomalies/ANOM-B-99/notes",
        json={"note": "Unauthorized case note"},
        headers=auth_header(tokens["admin_a"]),
    )
    assert res_note.status_code == 403


# --------------------------------------------------------------------------
# 8. Platform Administration (Directorate) Cross-Tenant Access Preserved
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_platform_administration_cross_tenant_access_preserved(client: AsyncClient, seeded_institutions, tokens):
    """Directorate administrators (AICTE / National Admin) retain authorized cross-tenant access."""
    db: AsyncIOMotorDatabase = mongo.db()

    # Seed data across both institutions
    await db["academic_years"].insert_many([
        {"_id": "AY-A-DIR", "id": "AY-A-DIR", "institution_id": INST_A, "name": "2026-27 Alpha", "code": "2026-27", "status": "UPCOMING", "is_current": False},
        {"_id": "AY-B-DIR", "id": "AY-B-DIR", "institution_id": INST_B, "name": "2026-27 Beta", "code": "2026-27", "status": "UPCOMING", "is_current": False},
    ])
    await db["anomalies"].insert_one({
        "_id": "ANOM-DIR-01",
        "anomaly_id": "ANOM-DIR-01",
        "institution_id": INST_B,
        "rule_code": "COMPLIANCE_REVIEW",
        "severity": "CRITICAL",
        "status": "OPEN",
    })

    dir_headers = auth_header(tokens["aicte_admin"])

    # Directorate can query Institution A's academic years
    res_a = await client.get(f"/api/academic/years?institution_id={INST_A}", headers=dir_headers)
    assert res_a.status_code == 200
    years_a = res_a.json()
    assert any(y["institution_id"] == INST_A for y in years_a)
    assert not any(y["institution_id"] == INST_B for y in years_a)

    # Directorate can query Institution B's academic years
    res_b = await client.get(f"/api/academic/years?institution_id={INST_B}", headers=dir_headers)
    assert res_b.status_code == 200
    years_b = res_b.json()
    assert any(y["institution_id"] == INST_B for y in years_b)
    assert not any(y["institution_id"] == INST_A for y in years_b)

    # Directorate can export anomalies report for Institution B
    res_anom = await client.get(f"/api/reports/anomalies.csv?institution_id={INST_B}", headers=dir_headers)
    assert res_anom.status_code == 200

    # Directorate can view national KPIs dashboard
    res_kpi = await client.get("/api/dashboard/national", headers=dir_headers)
    assert res_kpi.status_code == 200
    assert "total_approved_intake" in res_kpi.json()
