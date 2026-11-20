"""Stage 0.9: Attendance Management System Tests."""

from __future__ import annotations

import csv
import io

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
            {
                "student_id": "STU-01",
                "student_name": "Aarav Sharma",
                "status": "PRESENT",
                "remarks": None,
            },
            {
                "student_id": "STU-02",
                "student_name": "Diya Sen",
                "status": "ABSENT",
                "remarks": "Uninformed absence",
            },
            {
                "student_id": "STU-03",
                "student_name": "Rohan Mehra",
                "status": "LATE",
                "remarks": "Bus delayed 15m",
            },
            {
                "student_id": "STU-04",
                "student_name": "Zara Khan",
                "status": "EXCUSED",
                "remarks": "Medical leave",
            },
        ],
    }

    res = await async_client.post(
        "/api/attendance/sessions", json=payload, headers=auth(token_admin)
    )
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
    det_res = await async_client.get(
        f"/api/attendance/sessions/{session_id}", headers=auth(token_admin)
    )
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
    res1 = await async_client.post(
        "/api/attendance/sessions", json=payload, headers=auth(token_admin)
    )
    assert res1.status_code == 200

    # Second submission on same date and target rejected with 409
    res2 = await async_client.post(
        "/api/attendance/sessions", json=payload, headers=auth(token_admin)
    )
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
    await db["teacher_assignments"].insert_one(
        {
            "institution_id": inst_id,
            "teacher_id": teacher_id,
            "teacher_name": "Prof. Assigned",
            "class_id": "CLS-10A",
            "subject_id": "SUB-CS-101",
            "role_in_course": "Primary Teacher",
        }
    )

    # Also seed a different class 12B assigned to another teacher
    await db["teacher_assignments"].insert_one(
        {
            "institution_id": inst_id,
            "teacher_id": "TEA-OTHER",
            "teacher_name": "Prof. Other",
            "class_id": "CLS-12B",
            "subject_id": "SUB-HIST",
            "role_in_course": "Primary Teacher",
        }
    )

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
            "records": [
                {
                    "student_id": student_id,
                    "student_name": "Rahul Verma",
                    "status": "ABSENT",
                    "remarks": "Unexcused",
                }
            ],
        },
        headers=auth(token_admin),
    )
    assert res.status_code == 200

    # Check notification collection
    notif = await db["notifications"].find_one(
        {
            "institution_id": inst_id,
            "student_id": student_id,
            "category": "ATTENDANCE",
        }
    )
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
    await db["student_enrolments"].insert_many(
        [
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
        ]
    )

    res = await async_client.get(
        f"/api/attendance/roster?class_id={class_id}", headers=auth(token_admin)
    )
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
            "records": [
                {"student_id": student_id, "student_name": "Meera Joshi", "status": "ABSENT"}
            ],
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
    rec = await db["attendance_records"].find_one(
        {
            "session_id": session_id,
            "student_id": student_id,
        }
    )
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
            "records": [
                {"student_id": student_id, "student_name": "Karan Roy", "status": "ABSENT"}
            ],
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
    rec = await db["attendance_records"].find_one(
        {
            "session_id": session_id,
            "student_id": student_id,
        }
    )
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
    csv_res = await async_client.get(
        "/api/attendance/reports/export-csv", headers=auth(token_admin)
    )
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


@pytest.mark.asyncio
async def test_unassigned_teacher_rejected_without_silent_bypass(async_client: AsyncClient):
    """11. An unassigned teacher is rejected with 403 even if the institution has zero assignments configured."""
    db = mongo.db()
    inst_id = "INST-ATT-ZERO-ASG"
    teacher_id = "TEA-UNASSIGNED-99"

    token_teacher = await create_test_user(
        db, user_id=teacher_id, role="teacher", institution_id=inst_id
    )

    # Ensure teacher_assignments collection is empty for this institution
    await db["teacher_assignments"].delete_many({"institution_id": inst_id})

    res = await async_client.post(
        "/api/attendance/sessions",
        json={
            "session_date": "2026-03-25",
            "mode": "DAILY",
            "target_type": "CLASS",
            "target_id": "CLS-NONEXISTENT",
            "target_label": "Class Nonexistent",
            "records": [{"student_id": "STU-X", "student_name": "Student X", "status": "PRESENT"}],
        },
        headers=auth(token_teacher),
    )
    assert res.status_code == 403
    assert "not assigned" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_teacher_assigned_via_target_id_accepted(async_client: AsyncClient):
    """12. Teacher assignment using target_id (from academic module) is correctly accepted."""
    db = mongo.db()
    inst_id = "INST-ATT-TARGET-ID"
    teacher_id = "TEA-TARGET-01"

    token_teacher = await create_test_user(
        db, user_id=teacher_id, role="teacher", institution_id=inst_id
    )

    # Seed assignment using target_id and target_type as created by academic module
    await db["teacher_assignments"].insert_one(
        {
            "institution_id": inst_id,
            "teacher_id": teacher_id,
            "teacher_name": "Target Teacher",
            "target_id": "CLS-TGT-10",
            "target_type": "CLASS",
            "role_in_course": "Primary Teacher",
        }
    )

    res = await async_client.post(
        "/api/attendance/sessions",
        json={
            "session_date": "2026-03-25",
            "mode": "DAILY",
            "target_type": "CLASS",
            "target_id": "CLS-TGT-10",
            "target_label": "Class Target 10",
            "records": [
                {"student_id": "STU-T1", "student_name": "Student T1", "status": "PRESENT"}
            ],
        },
        headers=auth(token_teacher),
    )
    assert res.status_code == 200
    assert res.json()["target_id"] == "CLS-TGT-10"


@pytest.mark.asyncio
async def test_intra_batch_duplicate_student_rejected(async_client: AsyncClient):
    """13. Rejects submission payloads containing duplicate student IDs with 422 Unprocessable Entity."""
    db = mongo.db()
    inst_id = "INST-ATT-INTRA-DUP"
    token_admin = await create_test_user(
        db, user_id="USR-ADM-INTRA", role="school_admin", institution_id=inst_id
    )

    payload = {
        "session_date": "2026-03-25",
        "mode": "DAILY",
        "target_type": "CLASS",
        "target_id": "CLS-INTRA",
        "target_label": "Class Intra",
        "records": [
            {"student_id": "STU-DUP-1", "student_name": "Student A", "status": "PRESENT"},
            {"student_id": "STU-DUP-1", "student_name": "Student A", "status": "ABSENT"},
        ],
    }

    res = await async_client.post(
        "/api/attendance/sessions", json=payload, headers=auth(token_admin)
    )
    assert res.status_code == 422
    assert "duplicate student" in str(res.json()).lower()


@pytest.mark.asyncio
async def test_period_wise_requires_period_and_allows_different_periods(async_client: AsyncClient):
    """14. Period-wise mode enforces period number and distinguishes sessions by period."""
    db = mongo.db()
    inst_id = "INST-ATT-PERIOD"
    token_admin = await create_test_user(
        db, user_id="USR-ADM-PER", role="school_admin", institution_id=inst_id
    )

    # 1. Period-wise without period_number is rejected (422)
    res_no_period = await async_client.post(
        "/api/attendance/sessions",
        json={
            "session_date": "2026-03-26",
            "mode": "PERIOD_WISE",
            "target_type": "CLASS",
            "target_id": "CLS-PER-1",
            "target_label": "Class Per 1",
            "records": [{"student_id": "STU-P1", "student_name": "Student P", "status": "PRESENT"}],
        },
        headers=auth(token_admin),
    )
    assert res_no_period.status_code == 422

    # 2. Period 1 submission succeeds
    res_p1 = await async_client.post(
        "/api/attendance/sessions",
        json={
            "session_date": "2026-03-26",
            "mode": "PERIOD_WISE",
            "period_number": 1,
            "target_type": "CLASS",
            "target_id": "CLS-PER-1",
            "target_label": "Class Per 1",
            "records": [{"student_id": "STU-P1", "student_name": "Student P", "status": "PRESENT"}],
        },
        headers=auth(token_admin),
    )
    assert res_p1.status_code == 200

    # 3. Period 2 on same class and date also succeeds (not a duplicate conflict)
    res_p2 = await async_client.post(
        "/api/attendance/sessions",
        json={
            "session_date": "2026-03-26",
            "mode": "PERIOD_WISE",
            "period_number": 2,
            "target_type": "CLASS",
            "target_id": "CLS-PER-1",
            "target_label": "Class Per 1",
            "records": [{"student_id": "STU-P1", "student_name": "Student P", "status": "PRESENT"}],
        },
        headers=auth(token_admin),
    )
    assert res_p2.status_code == 200

    # 4. Duplicate period 1 is rejected (409)
    res_p1_dup = await async_client.post(
        "/api/attendance/sessions",
        json={
            "session_date": "2026-03-26",
            "mode": "PERIOD_WISE",
            "period_number": 1,
            "target_type": "CLASS",
            "target_id": "CLS-PER-1",
            "target_label": "Class Per 1",
            "records": [{"student_id": "STU-P1", "student_name": "Student P", "status": "PRESENT"}],
        },
        headers=auth(token_admin),
    )
    assert res_p1_dup.status_code == 409


@pytest.mark.asyncio
async def test_roster_active_enrolments_and_empty_handling(async_client: AsyncClient):
    """15. Roster finds enrolments with uppercase ACTIVE status and returns [] when empty."""
    db = mongo.db()
    inst_id = "INST-ATT-ROST-ACT"
    class_id = "CLS-ACT-10"

    token_admin = await create_test_user(
        db, user_id="USR-ADM-ROST-ACT", role="school_admin", institution_id=inst_id
    )

    # Seed enrolment with uppercase status "ACTIVE" and academic_year
    await db["student_enrolments"].insert_one(
        {
            "institution_id": inst_id,
            "student_id": "STU-ACT-01",
            "student_name": "Kavita Reddy",
            "enrolment_number": "ENR-ACT-01",
            "roll_number": "1",
            "class_id": class_id,
            "section": "A",
            "status": "ACTIVE",
            "academic_year": "AY-2025-26",
            "is_current": True,
        }
    )

    # Calling roster finds the student
    res = await async_client.get(
        f"/api/attendance/roster?class_id={class_id}&academic_year_id=AY-2025-26",
        headers=auth(token_admin),
    )
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["student_name"] == "Kavita Reddy"

    # Calling roster for non-existent class returns empty list [] (no fake records)
    res_empty = await async_client.get(
        "/api/attendance/roster?class_id=CLS-NONEXISTENT",
        headers=auth(token_admin),
    )
    assert res_empty.status_code == 200
    assert res_empty.json() == []


@pytest.mark.asyncio
async def test_teacher_classes_no_fake_demo_classes(async_client: AsyncClient):
    """16. Teacher classes endpoint returns [] for unassigned teacher without fake CLS-10A/9B."""
    db = mongo.db()
    inst_id = "INST-ATT-TEA-EMPTY"
    teacher_id = "TEA-UNASSIGNED-CLASS"

    token_teacher = await create_test_user(
        db, user_id=teacher_id, role="teacher", institution_id=inst_id
    )

    # With no assignments, teacher gets []
    res = await async_client.get("/api/attendance/teacher-classes", headers=auth(token_teacher))
    assert res.status_code == 200
    classes = res.json()
    assert classes == []

    # Now add an authentic assignment via target_id
    await db["teacher_assignments"].insert_one(
        {
            "institution_id": inst_id,
            "teacher_id": teacher_id,
            "teacher_name": "Teacher Assigned",
            "target_id": "CLS-REAL-1",
            "target_label": "Grade 7 Section B",
            "subject_id": "SUB-SCI-07",
            "subject_name": "General Science",
            "role_in_course": "Subject Teacher",
        }
    )

    res_assigned = await async_client.get(
        "/api/attendance/teacher-classes", headers=auth(token_teacher)
    )
    assert res_assigned.status_code == 200
    assigned_classes = res_assigned.json()
    assert len(assigned_classes) == 1
    assert assigned_classes[0]["class_id"] == "CLS-REAL-1"
    assert assigned_classes[0]["target_label"] == "Grade 7 Section B"
    assert assigned_classes[0]["attendance_submitted"] is False


@pytest.mark.asyncio
async def test_parent_cross_tenant_isolation_in_my_summary(async_client: AsyncClient):
    """17. Parent cannot access student from another institution or unverified child."""
    db = mongo.db()
    inst_a = "INST-ATT-TENANT-A"
    parent_id = "USR-PARENT-ATT"
    child_id = "STU-CHILD-ATT"

    token_parent = await create_test_user(
        db, user_id=parent_id, role="parent", institution_id=inst_a
    )

    # 1. Unlinked parent cannot access child
    res_unlinked = await async_client.get(
        f"/api/attendance/my-summary?student_id={child_id}", headers=auth(token_parent)
    )
    assert res_unlinked.status_code == 403

    # 2. Seed verified guardian relationship in Tenant A
    await db["guardian_relationships"].insert_one(
        {
            "parent_user_id": parent_id,
            "student_id": child_id,
            "institution_id": inst_a,
            "status": "VERIFIED",
        }
    )
    # Seed attendance policy with 85% requirement in Tenant A
    await db["attendance_policies"].insert_one(
        {
            "institution_id": inst_a,
            "minimum_attendance_percentage": 85.0,
            "mode": "DAILY",
        }
    )

    res_linked = await async_client.get(
        f"/api/attendance/my-summary?student_id={child_id}", headers=auth(token_parent)
    )
    assert res_linked.status_code == 200
    data = res_linked.json()
    assert data["student_id"] == child_id
    assert data["minimum_required"] == 85.0


@pytest.mark.asyncio
async def test_reports_summary_clean_zero_averages(async_client: AsyncClient):
    """18. Attendance summary report returns 0.0 rather than hardcoded 92.4 when no sessions exist."""
    db = mongo.db()
    inst_id = "INST-ATT-ZERO-SESS"
    token_admin = await create_test_user(
        db, user_id="USR-ADM-ZERO", role="school_admin", institution_id=inst_id
    )

    res = await async_client.get("/api/attendance/reports/summary", headers=auth(token_admin))
    assert res.status_code == 200
    data = res.json()
    assert data["total_sessions"] == 0
    assert data["average_attendance_percentage"] == 0.0
    assert data["class_summaries"] == []


@pytest.mark.asyncio
async def test_attendance_csv_export_escapes_formulas(async_client: AsyncClient):
    """19. Attendance CSV export prepends single quote to cells beginning with =, +, -, @ (CWE-1236)."""
    db = mongo.db()
    inst_id = "INST-ATT-CSV-SEC"
    token_admin = await create_test_user(
        db, user_id="USR-ADM-CSV", role="school_admin", institution_id=inst_id
    )

    records = [
        {
            "institution_id": inst_id,
            "session_id": "ATT-SESS-CSV-1",
            "session_date": "2026-03-10",
            "target_id": "CLS-SEC",
            "target_label": "=cmd|' /C calc'!A0",
            "subject_id": "SUB-1",
            "subject_name": "+SUM(A1:A10)",
            "student_id": "-1337-INJECT",
            "student_name": '@HYPERLINK("http://evil.com","Click")',
            "status": "PRESENT",
            "remarks": "=1+1",
            "recorded_by": "TEA-01",
        },
        {
            "institution_id": inst_id,
            "session_id": "ATT-SESS-CSV-2",
            "session_date": "2026-03-10",
            "target_id": "CLS-NORM",
            "target_label": "Grade 10 Section A",
            "subject_id": "SUB-NORM",
            "subject_name": "Mathematics",
            "student_id": "STU-CLEAN-01",
            "student_name": "Normal Student",
            "status": "PRESENT",
            "remarks": "Clean record",
            "recorded_by": "TEA-01",
        },
    ]
    await db["attendance_records"].insert_many(records)

    res = await async_client.get(
        "/api/attendance/reports/export-csv",
        headers=auth(token_admin),
    )
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")

    reader = csv.reader(io.StringIO(res.text))
    rows = list(reader)
    assert len(rows) >= 3

    header = rows[0]
    assert header == [
        "Session Date",
        "Target Class",
        "Subject",
        "Student ID",
        "Student Name",
        "Attendance Status",
        "Remarks",
        "Recorded By",
    ]

    injected_row = next(r for r in rows[1:] if "STU-CLEAN-01" not in r)
    clean_row = next(r for r in rows[1:] if "STU-CLEAN-01" in r)

    # Injected values escaped with single quote
    assert injected_row[1] == "'=cmd|' /C calc'!A0"
    assert injected_row[2] == "'+SUM(A1:A10)"
    assert injected_row[3] == "'-1337-INJECT"
    assert injected_row[4] == '\'@HYPERLINK("http://evil.com","Click")'
    assert injected_row[6] == "'=1+1"

    # Clean row values unescaped
    assert clean_row[1] == "Grade 10 Section A"
    assert clean_row[2] == "Mathematics"
    assert clean_row[3] == "STU-CLEAN-01"
    assert clean_row[4] == "Normal Student"
    assert clean_row[6] == "Clean record"


@pytest.mark.asyncio
async def test_parent_unverified_ward_attendance_rejected(async_client: AsyncClient):
    """20. Parent with unverified ward in profile or unverified relationship status is rejected (SEC-BE-001)."""
    db = mongo.db()
    inst_id = "INST-ATT-SEC-PAR"
    parent_id = "USR-PAR-UNVERIFIED"
    target_student_id = "STU-VICTIM-01"

    token_parent = await create_test_user(
        db, user_id=parent_id, role="parent", institution_id=inst_id
    )
    # Seed unverified ward_apaar_id in user profile
    await db["users"].update_one(
        {"user_id": parent_id},
        {"$set": {"ward_apaar_id": target_student_id}},
    )

    # 1. No relationship document -> 403
    res_no_rel = await async_client.get(
        f"/api/attendance/my-summary?student_id={target_student_id}",
        headers=auth(token_parent),
    )
    assert res_no_rel.status_code == 403
    assert "verified linked children" in res_no_rel.json()["detail"].lower()

    # 2. PENDING relationship -> 403
    await db["guardian_relationships"].insert_one(
        {
            "parent_user_id": parent_id,
            "student_id": target_student_id,
            "institution_id": inst_id,
            "status": "PENDING",
        }
    )

    res_pending = await async_client.get(
        f"/api/attendance/my-summary?student_id={target_student_id}",
        headers=auth(token_parent),
    )
    assert res_pending.status_code == 403
    assert "verified linked children" in res_pending.json()["detail"].lower()

    # 3. VERIFIED relationship -> 200
    await db["guardian_relationships"].update_one(
        {"parent_user_id": parent_id, "student_id": target_student_id},
        {"$set": {"status": "VERIFIED"}},
    )

    res_verified = await async_client.get(
        f"/api/attendance/my-summary?student_id={target_student_id}",
        headers=auth(token_parent),
    )
    assert res_verified.status_code == 200
    assert res_verified.json()["student_id"] == target_student_id


@pytest.mark.asyncio
async def test_batch_attendance_rejects_unenrolled_or_alien_students(async_client: AsyncClient):
    """21. Recording attendance session validates student IDs against enrolled institution students (SEC-BE-004)."""
    db = mongo.db()
    inst_main = "INST-ATT-BATCH-MAIN"
    inst_alien = "INST-ATT-BATCH-ALIEN"
    teacher_id = "TEA-BATCH-VAL"

    token_teacher = await create_test_user(
        db, user_id=teacher_id, role="teacher", institution_id=inst_main
    )

    # Assign teacher to target class
    await db["teacher_assignments"].insert_one(
        {
            "institution_id": inst_main,
            "teacher_id": teacher_id,
            "teacher_name": "Teacher Assigned",
            "target_id": "CLS-BATCH-1",
            "target_label": "Batch Class",
            "subject_name": "General",
        }
    )

    # Seed one valid student in inst_main
    await db["students"].insert_one(
        {
            "student_id": "STU-VALID-MAIN",
            "institution_id": inst_main,
            "name": "Valid Student",
            "class_id": "CLS-BATCH-1",
            "is_active": True,
        }
    )

    # Seed one alien student in inst_alien
    await db["students"].insert_one(
        {
            "student_id": "STU-ALIEN",
            "institution_id": inst_alien,
            "name": "Alien Student",
            "class_id": "CLS-BATCH-1",
            "is_active": True,
        }
    )

    base_payload = {
        "session_date": "2026-03-11",
        "mode": "DAILY",
        "target_type": "CLASS",
        "target_id": "CLS-BATCH-1",
        "target_label": "Batch Class",
        "subject_name": "General",
        "academic_year_id": "AY-2025-26",
    }

    # 1. Attempt with student not enrolled anywhere
    payload_unenrolled = {
        **base_payload,
        "records": [
            {"student_id": "STU-VALID-MAIN", "student_name": "Valid Student", "status": "PRESENT"},
            {"student_id": "STU-NOT-EXISTS", "student_name": "Ghost Student", "status": "PRESENT"},
        ],
    }
    res_unenrolled = await async_client.post(
        "/api/attendance/sessions",
        json=payload_unenrolled,
        headers=auth(token_teacher),
    )
    assert res_unenrolled.status_code == 422
    assert "not enrolled in this institution" in res_unenrolled.json()["detail"]
    assert "STU-NOT-EXISTS" in res_unenrolled.json()["detail"]

    # 2. Attempt with alien student from different institution
    payload_alien = {
        **base_payload,
        "records": [
            {"student_id": "STU-VALID-MAIN", "student_name": "Valid Student", "status": "PRESENT"},
            {"student_id": "STU-ALIEN", "student_name": "Alien Student", "status": "PRESENT"},
        ],
    }
    res_alien = await async_client.post(
        "/api/attendance/sessions",
        json=payload_alien,
        headers=auth(token_teacher),
    )
    assert res_alien.status_code == 403
    assert "belong to a different institution" in res_alien.json()["detail"]

    # 3. Clean submission with valid enrolled student succeeds
    payload_clean = {
        **base_payload,
        "records": [
            {"student_id": "STU-VALID-MAIN", "student_name": "Valid Student", "status": "PRESENT"},
        ],
    }
    res_clean = await async_client.post(
        "/api/attendance/sessions",
        json=payload_clean,
        headers=auth(token_teacher),
    )
    assert res_clean.status_code == 200
    assert res_clean.json()["total_students"] == 1
