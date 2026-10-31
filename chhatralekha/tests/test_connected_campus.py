"""End-to-end tests for ChhatraLekha Connected Campus (Schools and Colleges).

Verifies the MVP modules:
1. Institution onboarding & verification review.
2. Academic structure setup (Academic Years, School Classes/Sections, Subjects, Teacher Allocations).
3. Teacher workspace & attendance tracking.
4. Examination setup, draft marks entry, moderation and publication.
5. Communication centre: targeted announcements and read acknowledgements.
6. Guardian / parent linking and verified child academic overview.
7. Public sustainability & transparency charter.
"""

from __future__ import annotations

import httpx
import pytest

from app.core.database import mongo
from app.core.security import hash_password

TEST_PW_HASH = hash_password("Test@1234")


@pytest.fixture
async def campus_db():
    db = mongo.db()

    # Seed an active school and active college
    await db["institutions"].insert_many([
        {
            "institution_id": "SCH-DEL-001",
            "name": "Delhi Public Model School",
            "category": "SCHOOL",
            "institution_type": "SCHOOL",
            "state": "Delhi",
            "city": "New Delhi",
            "is_active": True,
            "verification_status": "VERIFIED",
        },
        {
            "institution_id": "COL-PUN-002",
            "name": "Pune Institute of Science",
            "category": "COLLEGE",
            "institution_type": "COLLEGE",
            "state": "Maharashtra",
            "city": "Pune",
            "is_active": True,
            "verification_status": "VERIFIED",
        },
    ])

    # Seed users across roles
    await db["users"].insert_many([
        {
            "user_id": "USR-OP",
            "email": "operator@chhatralekha.test",
            "full_name": "Platform Operator",
            "role": "platform_operator",
            "institution_id": None,
            "password_hash": TEST_PW_HASH,
            "is_active": True,
        },
        {
            "user_id": "USR-SCH-ADMIN",
            "email": "principal@delhischool.test",
            "full_name": "School Principal",
            "role": "institution_admin",
            "institution_id": "SCH-DEL-001",
            "password_hash": TEST_PW_HASH,
            "is_active": True,
        },
        {
            "user_id": "USR-TEACHER",
            "email": "teacher.sharma@delhischool.test",
            "full_name": "Sunita Sharma",
            "role": "teacher",
            "institution_id": "SCH-DEL-001",
            "password_hash": TEST_PW_HASH,
            "is_active": True,
        },
        {
            "user_id": "USR-STUDENT-ANIL",
            "email": "anil.kumar@student.test",
            "full_name": "Anil Kumar",
            "role": "student",
            "institution_id": "SCH-DEL-001",
            "apaar_id": "984210357890",
            "password_hash": TEST_PW_HASH,
            "is_active": True,
        },
        {
            "user_id": "USR-PARENT",
            "email": "ramesh.kumar@parent.test",
            "full_name": "Ramesh Kumar (Father)",
            "role": "parent",
            "institution_id": None,
            "password_hash": TEST_PW_HASH,
            "is_active": True,
        },
    ])

    # Seed student record
    await db["students"].insert_one({
        "apaar_id": "984210357890",
        "student_name": "Anil Kumar",
        "date_of_birth": "2010-05-15",
        "gender": "M",
        "institution_id": "SCH-DEL-001",
        "program_id": "Class 10-A",
        "academic_year": "2025-26",
        "record_status": "ACTIVE",
        "is_active": True,
    })

    return db


async def _login(client: httpx.AsyncClient, email: str) -> str:
    res = await client.post("/api/auth/login", json={"email": email, "password": "Test@1234"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
async def http_client(campus_db):
    from app.main import app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


# -----------------------------------------------------------------------------
# 1. Institution Onboarding & Platform Review
# -----------------------------------------------------------------------------
async def test_institution_registration_and_review(http_client):
    operator_token = await _login(http_client, "operator@chhatralekha.test")

    # 1. Public self-registration for a new rural school
    reg_res = await http_client.post(
        "/api/institutions/register",
        json={
            "name": "Saraswati Vidya Mandir",
            "category": "SCHOOL",
            "institution_type": "SCHOOL",
            "state": "Odisha",
            "city": "Cuttack",
            "address": "Bidanasi, Cuttack",
            "affiliation": "BSE Odisha",
            "contact_email": "admin@svm-cuttack.org",
            "contact_phone": "+919876543299",
            "admin_name": "Headmaster Mohanty",
            "admin_password": "SecurePassword@123",
        },
    )
    assert reg_res.status_code == 201, reg_res.text
    reg_data = reg_res.json()
    new_inst_id = reg_data["institution_id"]
    assert reg_data["verification_status"] == "PENDING_REVIEW"
    assert new_inst_id.startswith("SCH-CUT-")

    # 2. Platform operator reviews and approves the institution
    review_res = await http_client.post(
        f"/api/institutions/{new_inst_id}/review",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={
            "decision": "VERIFIED",
            "notes": "Verified against state school education directory.",
        },
    )
    assert review_res.status_code == 200
    assert review_res.json()["is_active"] is True
    assert review_res.json()["verification_status"] == "VERIFIED"


# -----------------------------------------------------------------------------
# 2. Academic Setup (Years, Classes, Subjects, Teacher Assignment)
# -----------------------------------------------------------------------------
async def test_academic_setup_workflow(http_client):
    admin_token = await _login(http_client, "principal@delhischool.test")
    auth_header = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create Academic Year
    ay_res = await http_client.post(
        "/api/academic/years",
        headers=auth_header,
        json={
            "year_label": "2025-26",
            "start_date": "2025-04-01",
            "end_date": "2026-03-31",
            "is_current": True,
            "terms": ["Term 1", "Term 2"],
        },
    )
    assert ay_res.status_code == 200
    assert ay_res.json()["year_label"] == "2025-26"

    # 2. Create Class 10 Section A
    cls_res = await http_client.post(
        "/api/academic/classes",
        headers=auth_header,
        json={
            "grade_level": "Class 10",
            "section": "A",
            "academic_year": "2025-26",
            "capacity": 45,
            "room_number": "Room 101",
            "class_teacher_id": "USR-TEACHER",
            "class_teacher_name": "Sunita Sharma",
        },
    )
    assert cls_res.status_code == 200
    class_id = cls_res.json()["class_id"]

    # 3. Create Subject Mathematics
    sub_res = await http_client.post(
        "/api/academic/subjects",
        headers=auth_header,
        json={
            "subject_code": "MATH-10",
            "subject_name": "Mathematics",
            "category": "CORE",
            "applicable_to": "Class 10",
        },
    )
    assert sub_res.status_code == 200
    subject_id = sub_res.json()["subject_id"]

    # 4. Assign Teacher to Class 10-A Mathematics
    asn_res = await http_client.post(
        "/api/academic/teacher-assignments",
        headers=auth_header,
        json={
            "teacher_id": "USR-TEACHER",
            "teacher_name": "Sunita Sharma",
            "subject_id": subject_id,
            "subject_name": "Mathematics",
            "target_type": "CLASS",
            "target_id": class_id,
            "target_label": "Class 10-A",
        },
    )
    assert asn_res.status_code == 200
    assert asn_res.json()["target_label"] == "Class 10-A"


# -----------------------------------------------------------------------------
# 3. Attendance Tracking & Teacher Workspace
# -----------------------------------------------------------------------------
async def test_teacher_workspace_and_attendance(http_client):
    teacher_token = await _login(http_client, "teacher.sharma@delhischool.test")
    student_token = await _login(http_client, "anil.kumar@student.test")
    teacher_auth = {"Authorization": f"Bearer {teacher_token}"}
    student_auth = {"Authorization": f"Bearer {student_token}"}

    # 1. Teacher views assigned classes
    classes_res = await http_client.get("/api/teacher/classes", headers=teacher_auth)
    assert classes_res.status_code == 200

    # 2. Teacher submits attendance for Class 10-A
    att_res = await http_client.post(
        "/api/attendance/sessions",
        headers=teacher_auth,
        json={
            "session_date": "2026-10-31",
            "mode": "DAILY",
            "target_type": "CLASS",
            "target_id": "CLS-CLASS-10-A",
            "target_label": "Class 10-A",
            "records": [
                {
                    "student_id": "984210357890",
                    "student_name": "Anil Kumar",
                    "status": "PRESENT",
                    "remarks": "On time",
                }
            ],
        },
    )
    assert att_res.status_code == 200
    assert att_res.json()["present_count"] == 1

    # 3. Student views their attendance summary
    summary_res = await http_client.get("/api/attendance/my-summary", headers=student_auth)
    assert summary_res.status_code == 200
    summary_data = summary_res.json()
    assert summary_data["present_sessions"] >= 1
    assert summary_data["attendance_rate"] == 100.0


# -----------------------------------------------------------------------------
# 4. Examination, Draft Marks & Publishing
# -----------------------------------------------------------------------------
async def test_assessment_draft_marks_and_publication(http_client):
    admin_token = await _login(http_client, "principal@delhischool.test")
    teacher_token = await _login(http_client, "teacher.sharma@delhischool.test")
    student_token = await _login(http_client, "anil.kumar@student.test")

    # 1. Admin creates Assessment
    asm_res = await http_client.post(
        "/api/assessments",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Mid-Term Mathematics",
            "academic_year": "2025-26",
            "term": "Term 1",
            "target_type": "CLASS",
            "target_id": "CLS-CLASS-10-A",
            "target_label": "Class 10-A",
            "subject_id": "SUB-MATH-10",
            "subject_name": "Mathematics",
            "max_marks": 100.0,
            "passing_marks": 35.0,
        },
    )
    assert asm_res.status_code == 200
    asm_id = asm_res.json()["assessment_id"]
    assert asm_res.json()["status"] == "DRAFT"

    # 2. Teacher records draft marks
    marks_res = await http_client.post(
        f"/api/assessments/{asm_id}/marks",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "marks": [
                {
                    "student_id": "984210357890",
                    "student_name": "Anil Kumar",
                    "marks_obtained": 88.5,
                    "remarks": "Excellent problem solving",
                }
            ]
        },
    )
    assert marks_res.status_code == 200

    # 3. Before publication: student queries results -> unpublished marks remain private!
    res_before = await http_client.get(
        "/api/assessments/my-results",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_before.status_code == 200
    # Must not contain unpublished marks
    assert not any(r["assessment_id"] == asm_id for r in res_before.json())

    # 4. Admin reviews & publishes assessment
    pub_res = await http_client.post(
        f"/api/assessments/{asm_id}/publish",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "PUBLISHED"

    # 5. After publication: student sees their verified score
    res_after = await http_client.get(
        "/api/assessments/my-results",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_after.status_code == 200
    user_results = res_after.json()
    assert any(r["assessment_id"] == asm_id and r["grade"] == "A" for r in user_results)


# -----------------------------------------------------------------------------
# 5. Communication Centre (Targeted Announcements)
# -----------------------------------------------------------------------------
async def test_communication_centre_announcements(http_client):
    admin_token = await _login(http_client, "principal@delhischool.test")
    student_token = await _login(http_client, "anil.kumar@student.test")

    # Admin posts high-priority notice
    post_res = await http_client.post(
        "/api/announcements",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Winter Uniform Transition Notice",
            "content": "All students are requested to switch to winter uniform starting Monday.",
            "priority": "HIGH",
            "target_scope": "ALL",
        },
    )
    assert post_res.status_code == 200
    ann_id = post_res.json()["announcement_id"]

    # Student views notices
    list_res = await http_client.get(
        "/api/announcements",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert list_res.status_code == 200
    notices = list_res.json()
    assert any(n["announcement_id"] == ann_id for n in notices)

    # Student acknowledges notice
    ack_res = await http_client.post(
        f"/api/announcements/{ann_id}/acknowledge",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert ack_res.status_code == 200


# -----------------------------------------------------------------------------
# 6. Guardian / Parent Linking & Overview
# -----------------------------------------------------------------------------
async def test_guardian_link_and_child_overview(http_client):
    parent_token = await _login(http_client, "ramesh.kumar@parent.test")
    admin_token = await _login(http_client, "principal@delhischool.test")

    # 1. Parent requests link
    link_res = await http_client.post(
        "/api/parent/link",
        headers={"Authorization": f"Bearer {parent_token}"},
        json={
            "student_identifier": "984210357890",
            "student_dob": "2010-05-15",
            "relationship": "FATHER",
            "guardian_phone": "+919876543200",
        },
    )
    assert link_res.status_code == 200
    link_id = link_res.json()["link_id"]

    # 2. Institution approves relationship
    verify_res = await http_client.post(
        f"/api/parent/link/{link_id}/verify",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"verification_status": "VERIFIED"},
    )
    assert verify_res.status_code == 200

    # 3. Parent views linked child overview
    children_res = await http_client.get(
        "/api/parent/children",
        headers={"Authorization": f"Bearer {parent_token}"},
    )
    assert children_res.status_code == 200
    children = children_res.json()
    assert len(children) >= 1
    child = children[0]
    assert child["student_id"] == "984210357890"
    assert child["student_name"] == "Anil Kumar"
    assert child["verification_status"] == "VERIFIED"


# -----------------------------------------------------------------------------
# 7. Public Sustainability & Transparency Charter
# -----------------------------------------------------------------------------
async def test_public_transparency_charter(http_client):
    res = await http_client.get("/api/transparency")
    assert res.status_code == 200
    body = res.json()
    assert body["business_model"]["is_free"] is True
    assert body["business_model"]["has_ads"] is False
    assert body["business_model"]["sells_student_data"] is False
    assert len(body["sustainability_sources"]) >= 3
    assert len(body["operating_cost_categories"]) >= 3
