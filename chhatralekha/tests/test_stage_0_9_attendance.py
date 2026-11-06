"""Stage 0.9: Attendance Management System Tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import mongo
from app.main import app
from tests.test_stage_0_3_security_remediation import create_test_user


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_attendance_policy_lifecycle(async_client: AsyncClient):
    """1. Administrators can view and update institution attendance policy. Non-admins are rejected."""
    db = mongo.db()
    token_admin = await create_test_user(
        db, user_id="USR-ADM-ATT-01", role="school_admin", institution_id="INST-ATT-01"
    )
    token_student = await create_test_user(
        db, user_id="USR-STU-ATT-01", role="student", institution_id="INST-ATT-01"
    )

    # 1. Get default policy
    res = await async_client.get("/api/attendance/policy", headers=auth(token_admin))
    assert res.status_code == 200
    data = res.json()
    assert data["institution_id"] == "INST-ATT-01"
    assert data["minimum_attendance_percentage"] == 75.0

    # 2. Student attempt to update policy is rejected (403)
    res = await async_client.post(
        "/api/attendance/policy",
        json={
            "mode": "PERIOD_WISE",
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "periods_per_day": 8,
            "minimum_attendance_percentage": 80.0,
            "late_arrival_threshold_minutes": 10,
            "early_departure_threshold_minutes": 10,
            "consecutive_absent_alert_threshold": 2,
            "allowed_statuses": ["PRESENT", "ABSENT", "LATE", "EXCUSED", "ON_LEAVE", "HALF_DAY"],
        },
        headers=auth(token_student),
    )
    assert res.status_code == 403

    # 3. Admin successfully updates policy
    res = await async_client.post(
        "/api/attendance/policy",
        json={
            "mode": "PERIOD_WISE",
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "periods_per_day": 8,
            "minimum_attendance_percentage": 80.0,
            "late_arrival_threshold_minutes": 10,
            "early_departure_threshold_minutes": 10,
            "consecutive_absent_alert_threshold": 2,
            "allowed_statuses": ["PRESENT", "ABSENT", "LATE", "EXCUSED", "ON_LEAVE", "HALF_DAY"],
        },
        headers=auth(token_admin),
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["mode"] == "PERIOD_WISE"
    assert updated["minimum_attendance_percentage"] == 80.0
    assert updated["periods_per_day"] == 8


@pytest.mark.asyncio
async def test_record_attendance_session_tallies_and_records(async_client: AsyncClient):
    """2. Submitting an attendance session computes tallies and saves individual records."""
    db = mongo.db()
    inst_id = "INST-ATT-TALLIES"
    token_admin = await create_test_user(
        db, user_id="USR-ADM-TAL", role="school_admin", institution_id=inst_id
    )

    payload = {
        "session_date": "2026-03-10",
        "mode": "DAILY",
        "target_type": "CLASS",
        "target_id": "CLS-GRADE10-A",
        "target_label": "Grade 10 Section A",
        "subject_id": "SUB-MATH",
        "subject_name": "Mathematics",
        "academic_year_id": "AY-2025-26",
        "records": [
            {"student_id": "STU-01", "student_name": "Aarav Sharma", "status": "PRESENT", "remarks": None},
            {"student_id": "STU-02", "student_name": "Diya Sen", "status": "ABSENT", "remarks": "Uninformed absence"},
            {"student_id": "STU-03", "student_name": "Rohan Mehra", "status": "LATE", "remarks": "Bus delayed 15m"},
            {"student_id": "STU-04", "student_name": "Zara Khan", "status": "EXCUSED", "remarks": "Medical leave"},
        ],
    }

    res = await async_client.post("/api/attendance/sessions", json=payload, headers=auth(token_admin))
    assert res.status_code == 200
    session_data = res.json()
    assert session_data["total_students"] == 4
    assert session_data["present_count"] == 1
    assert session_data["absent_count"] == 1
    assert session_data["late_count"] == 1
    assert session_data["excused_count"] == 1

    # Verify session in DB
    session_id = session_data["session_id"]
    sess_doc = await db["attendance_sessions"].find_one({"session_id": session_id})
    assert sess_doc is not None
    assert sess_doc["target_id"] == "CLS-GRADE10-A"

    # Verify detail endpoint
    det_res = await async_client.get(f"/api/attendance/sessions/{session_id}", headers=auth(token_admin))
    assert det_res.status_code == 200
    records = det_res.json()["records"]
    assert len(records) == 4
    assert any(r["student_id"] == "STU-02" and r["status"] == "ABSENT" for r in records)


@pytest.mark.asyncio
async def test_duplicate_attendance_submission_rejected(async_client: AsyncClient):
    """3. Rejects duplicate attendance submissions for the same class and date with 409 Conflict."""
    db = mongo.db()
    inst_id = "INST-ATT-DUP"
    token_admin = await create_test_user(
        db, user_id="USR-ADM-DUP", role="school_admin", institution_id=inst_id
    )

    payload = {
        "session_date": "2026-03-12",
        "mode": "DAILY",
        "target_type": "CLASS",
        "target_id": "CLS-GRADE9-B",
        "target_label": "Grade 9 Section B",
        "records": [
            {"student_id": "STU-D1", "student_name": "Student One", "status": "PRESENT"},
        ],
    }

    # First submission succeeds
    res1 = await async_client.post("/api/attendance/sessions", json=payload, headers=auth(token_admin))
    assert res1.status_code == 200

    # Second submission on same date and target rejected with 409
    res2 = await async_client.post("/api/attendance/sessions", json=payload, headers=auth(token_admin))
    assert res2.status_code == 409
    assert "already submitted" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_teacher_assignment_authorization(async_client: AsyncClient):
    """4. Teachers can only submit attendance for classes assigned to them. Unassigned classes return 403."""
    db = mongo.db()
    inst_id = "INST-ATT-TEACHER"
    teacher_id = "TEA-AUTHORIZED-01"

    token_teacher = await create_test_user(
        db, user_id=teacher_id, role="teacher", institution_id=inst_id
    )

    # Seed an assignment for teacher to Class 10A
    await db["teacher_assignments"].insert_one({
        "institution_id": inst_id,
        "teacher_id": teacher_id,
        "teacher_name": "Prof. Assigned",
        "class_id": "CLS-10A",
        "subject_id": "SUB-CS-101",
        "role_in_course": "Primary Teacher",
    })

    # Also seed a different class 12B assigned to another teacher
    await db["teacher_assignments"].insert_one({
        "institution_id": inst_id,
        "teacher_id": "TEA-OTHER",
        "teacher_name": "Prof. Other",
        "class_id": "CLS-12B",
        "subject_id": "SUB-HIST",
        "role_in_course": "Primary Teacher",
    })

    # Submitting for assigned class CLS-10A succeeds
    res_ok = await async_client.post(
        "/api/attendance/sessions",
        json={
            "session_date": "2026-03-14",
            "mode": "DAILY",
            "target_type": "CLASS",
            "target_id": "CLS-10A",
            "target_label": "Class 10A",
            "records": [{"student_id": "STU-A1", "student_name": "Alice", "status": "PRESENT"}],
        },
        headers=auth(token_teacher),
    )
    assert res_ok.status_code == 200

    # Submitting for unassigned class CLS-12B is rejected with 403
    res_forbidden = await async_client.post(
        "/api/attendance/sessions",
        json={
            "session_date": "2026-03-14",
            "mode": "DAILY",
            "target_type": "CLASS",
            "target_id": "CLS-12B",
            "target_label": "Class 12B",
            "records": [{"student_id": "STU-B1", "student_name": "Bob", "status": "PRESENT"}],
        },
        headers=auth(token_teacher),
    )
    assert res_forbidden.status_code == 403
    assert "not assigned" in res_forbidden.json()["detail"].lower()


@pytest.mark.asyncio
async def test_absence_creates_attendance_notification(async_client: AsyncClient):
    """5. Marking student absent dispatches notification under ATTENDANCE category with safe preview."""
    db = mongo.db()
    inst_id = "INST-ATT-NOTIF"
    student_id = "STU-ABS-99"

    token_admin = await create_test_user(
        db, user_id="USR-ADM-NOTIF", role="school_admin", institution_id=inst_id
    )

    res = await async_client.post(
        "/api/attendance/sessions",
        json={
            "session_date": "2026-03-16",
            "mode": "DAILY",
            "target_type": "CLASS",
            "target_id": "CLS-8A",
            "target_label": "Class 8A",
            "records": [{"student_id": student_id, "student_name": "Rahul Verma", "status": "ABSENT", "remarks": "Unexcused"}],
        },
        headers=auth(token_admin),
    )
    assert res.status_code == 200

    # Check notification collection
    notif = await db["notifications"].find_one({
        "institution_id": inst_id,
        "student_id": student_id,
        "category": "ATTENDANCE",
    })
    assert notif is not None
    assert "absence" in notif["title"].lower() or "absent" in notif["title"].lower()
    assert student_id in notif["user_id"]
    # Verify no private clinical health data in message preview
    assert "Unexcused" not in notif["message"]


@pytest.mark.asyncio
async def test_attendance_roster_endpoint(async_client: AsyncClient):
    """6. Roster endpoint returns active student enrolments for the class."""
    db = mongo.db()
    inst_id = "INST-ATT-ROSTER"
    class_id = "CLS-ROSTER-10A"

    token_admin = await create_test_user(
        db, user_id="USR-ADM-ROST", role="school_admin", institution_id=inst_id
    )

    # Seed student enrolments
    await db["student_enrolments"].insert_many([
        {
            "institution_id": inst_id,
            "student_id": "STU-R1",
            "student_name": "Rohan Gupta",
            "enrolment_number": "ENR-R1",
            "roll_number": "101",
            "class_id": class_id,
            "section": "A",
            "status": "active",
            "is_current": True,
        },
        {
            "institution_id": inst_id,
            "student_id": "STU-R2",
            "student_name": "Simran Kaur",
            "enrolment_number": "ENR-R2",
            "roll_number": "102",
            "class_id": class_id,
            "section": "A",
            "status": "active",
            "is_current": True,
        },
    ])

    res = await async_client.get(f"/api/attendance/roster?class_id={class_id}", headers=auth(token_admin))
    assert res.status_code == 200
    roster = res.json()
    assert len(roster) >= 2
    assert any(s["student_name"] == "Rohan Gupta" for s in roster)


@pytest.mark.asyncio
async def test_attendance_correction_lifecycle_preserves_audit_trail(async_client: AsyncClient):
    """7. Attendance correction workflow preserves original records and maintains immutable audit history."""
    db = mongo.db()
    inst_id = "INST-ATT-CORR"
    student_id = "STU-CORR-01"

    token_admin = await create_test_user(
        db, user_id="USR-ADM-CORR", role="school_admin", institution_id=inst_id
    )
    token_teacher = await create_test_user(
        db, user_id="TEA-CORR-01", role="teacher", institution_id=inst_id
    )

    # 1. Record session where student is marked ABSENT
    sess_res = await async_client.post(
        "/api/attendance/sessions",
        json={
            "session_date": "2026-03-18",
            "mode": "DAILY",
            "target_type": "CLASS",
            "target_id": "CLS-CORR-1",
            "target_label": "Class 10C",
            "records": [{"student_id": student_id, "student_name": "Meera Joshi", "status": "ABSENT"}],
        },
        headers=auth(token_admin),
    )
    session_id = sess_res.json()["session_id"]

    # 2. Submit correction request to change ABSENT -> EXCUSED
    corr_res = await async_client.post(
        "/api/attendance/corrections",
        json={
            "session_id": session_id,
            "student_id": student_id,
            "requested_status": "EXCUSED",
            "reason": "Submitted verified medical certificate for dental treatment.",
        },
        headers=auth(token_teacher),
    )
    assert corr_res.status_code == 200
    corr_data = corr_res.json()
    corr_id = corr_data["id"]
    assert corr_data["status"] == "PENDING"
    assert corr_data["previous_status"] == "ABSENT"
    assert corr_data["requested_status"] == "EXCUSED"

    # 3. Non-admin attempt to approve correction is rejected (403)
    non_admin_rev = await async_client.post(
        f"/api/attendance/corrections/{corr_id}/review",
        json={"decision": "APPROVE", "review_notes": "Unauthorized approval"},
        headers=auth(token_teacher),
    )
    assert non_admin_rev.status_code == 403

    # 4. Admin approves correction
    admin_rev = await async_client.post(
        f"/api/attendance/corrections/{corr_id}/review",
        json={"decision": "APPROVE", "review_notes": "Medical certificate verified by nurse."},
        headers=auth(token_admin),
    )
    assert admin_rev.status_code == 200
    rev_data = admin_rev.json()
    assert rev_data["status"] == "APPROVED"

    # 5. Verify student record in database has status updated AND audit_trail preserved
    rec = await db["attendance_records"].find_one({
        "session_id": session_id,
        "student_id": student_id,
    })
    assert rec["status"] == "EXCUSED"
    assert len(rec["audit_trail"]) == 1
    audit_entry = rec["audit_trail"][0]
    assert audit_entry["previous_status"] == "ABSENT"
    assert audit_entry["new_status"] == "EXCUSED"
    assert "medical certificate" in audit_entry["reason"].lower()
    assert audit_entry["changed_by"] == "USR-ADM-CORR"

    # 6. Verify session tallies were recalculated
    sess = await db["attendance_sessions"].find_one({"session_id": session_id})
    assert sess["absent_count"] == 0
    assert sess["excused_count"] == 1


@pytest.mark.asyncio
async def test_attendance_correction_rejection(async_client: AsyncClient):
    """8. Admin can reject a correction request with review notes."""
    db = mongo.db()
    inst_id = "INST-ATT-REJ"
    student_id = "STU-REJ-01"

    token_admin = await create_test_user(
        db, user_id="USR-ADM-REJ", role="school_admin", institution_id=inst_id
    )

    sess_res = await async_client.post(
        "/api/attendance/sessions",
        json={
            "session_date": "2026-03-20",
            "mode": "DAILY",
            "target_type": "CLASS",
            "target_id": "CLS-REJ-1",
            "target_label": "Class 10D",
            "records": [{"student_id": student_id, "student_name": "Karan Roy", "status": "ABSENT"}],
        },
        headers=auth(token_admin),
    )
    session_id = sess_res.json()["session_id"]

    corr_res = await async_client.post(
        "/api/attendance/corrections",
        json={
            "session_id": session_id,
            "student_id": student_id,
            "requested_status": "PRESENT",
            "reason": "Student claims they were present in back row.",
        },
        headers=auth(token_admin),
    )
    corr_id = corr_res.json()["id"]

    # Reject correction
    rev_res = await async_client.post(
        f"/api/attendance/corrections/{corr_id}/review",
        json={"decision": "REJECT", "review_notes": "CCTV review confirms student was absent."},
        headers=auth(token_admin),
    )
    assert rev_res.status_code == 200
    assert rev_res.json()["status"] == "REJECTED"
    assert "cctv review" in rev_res.json()["review_notes"].lower()

    # Original attendance record remains unchanged as ABSENT
    rec = await db["attendance_records"].find_one({
        "session_id": session_id,
        "student_id": student_id,
    })
    assert rec["status"] == "ABSENT"


@pytest.mark.asyncio
async def test_attendance_reports_and_csv_export(async_client: AsyncClient):
    """9. Reports summary aggregates data, and CSV export returns protected spreadsheet."""
    db = mongo.db()
    inst_id = "INST-ATT-REPORT"
    token_admin = await create_test_user(
        db, user_id="USR-ADM-REP", role="school_admin", institution_id=inst_id
    )

    # Seed 2 sessions
    await async_client.post(
        "/api/attendance/sessions",
        json={
            "session_date": "2026-03-22",
            "mode": "DAILY",
            "target_type": "CLASS",
            "target_id": "CLS-REP-1",
            "target_label": "Class 10A",
            "records": [
                {"student_id": "S1", "student_name": "Student 1", "status": "PRESENT"},
                {"student_id": "S2", "student_name": "Student 2", "status": "PRESENT"},
            ],
        },
        headers=auth(token_admin),
    )

    # 1. Summary Report
    rep_res = await async_client.get("/api/attendance/reports/summary", headers=auth(token_admin))
    assert rep_res.status_code == 200
    summary = rep_res.json()
    assert summary["institution_id"] == inst_id
    assert summary["total_sessions"] >= 1
    assert summary["average_attendance_percentage"] >= 0

    # 2. CSV Export
    csv_res = await async_client.get("/api/attendance/reports/export-csv", headers=auth(token_admin))
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "attachment; filename=" in csv_res.headers["content-disposition"]
    csv_text = csv_res.text
    assert "Session Date,Target Class,Subject,Student ID" in csv_text
    assert "Student 1" in csv_text


@pytest.mark.asyncio
async def test_student_and_parent_ownership_isolation(async_client: AsyncClient):
    """10. Enforces that students and parents can only access authorized student attendance."""
    db = mongo.db()
    inst_id = "INST-ATT-OWNERSHIP"
    student_a_apaar = "999900000001"
    student_b_apaar = "999900000002"

    token_stu_a = await create_test_user(
        db, user_id="USR-STU-A9", role="student", institution_id=inst_id, apaar_id=student_a_apaar
    )

    # Student A can view own summary
    res_own = await async_client.get("/api/attendance/my-summary", headers=auth(token_stu_a))
    assert res_own.status_code == 200
    assert res_own.json()["student_id"] == student_a_apaar
    assert "minimum_required" in res_own.json()
    assert res_own.json()["minimum_required"] == 75.0

    # Student A attempting to access Student B is rejected (403)
    res_other = await async_client.get(
        f"/api/attendance/my-summary?student_id={student_b_apaar}", headers=auth(token_stu_a)
    )
    assert res_other.status_code == 403
    assert "own attendance record" in res_other.json()["detail"].lower()
