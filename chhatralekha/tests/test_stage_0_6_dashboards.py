"""Test suite for Stage 0.6: Role-Based Dashboards and Core Navigation Backend Endpoints.

Covers:
1. Student unified dashboard summary (`/api/me/dashboard`).
2. Student personal timetable schedule (`/api/me/timetable`).
3. Student coursework assignments (`/api/me/assignments`).
4. Teacher faculty dashboard summary (`/api/teacher/dashboard`).
5. Teacher coursework assignment creation and listing (`/api/teacher/assignments`).
6. Parent verified child timetable retrieval and security authorization enforcement (`/api/parent/children/{id}/timetable`).
7. Parent unauthorized child access rejection (403 Forbidden).
8. Institutional campus dashboard summary for school and college administrators (`/api/institutions/{id}/dashboard-summary`).
9. Cross-institution tenant scope isolation enforcement on institution dashboard.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.database import mongo
from app.core.security import create_access_token
from app.models.enums import GuardianVerificationStatus


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def seed_user_and_token(
    db,
    user_id: str,
    role: str,
    institution_id: str | None = None,
    apaar_id: str | None = None,
    email: str | None = None,
    full_name: str | None = None,
) -> str:
    email = email or f"{user_id.lower()}@chhatralekha.test"
    full_name = full_name or f"User {user_id}"
    await db["users"].replace_one(
        {"user_id": user_id},
        {
            "user_id": user_id,
            "email": email,
            "full_name": full_name,
            "role": role,
            "institution_id": institution_id,
            "apaar_id": apaar_id,
            "is_active": True,
        },
        upsert=True,
    )
    extra = {}
    if apaar_id:
        extra["apaar_id"] = apaar_id
    return create_access_token(
        subject=user_id,
        role=role,
        institution_id=institution_id,
        extra_claims=extra if extra else None,
    )


@pytest.mark.asyncio
async def test_student_dashboard_summary_and_timetable(client: AsyncClient):
    db = mongo.db()
    inst_id = "INST-STU-01"
    apaar = "987654321099"

    await db["institutions"].replace_one(
        {"institution_id": inst_id},
        {"institution_id": inst_id, "name": "Apex Engineering College"},
        upsert=True,
    )
    await db["students"].replace_one(
        {"apaar_id": apaar},
        {
            "apaar_id": apaar,
            "student_name": "Rohan Deshmukh",
            "institution_id": inst_id,
            "program_id": "B.Tech Computer Science",
            "student_institute_roll_no": "ROLL-CS-042",
            "record_status": "ACTIVE",
            "is_active": True,
        },
        upsert=True,
    )
    token = await seed_user_and_token(db, "USR-STU-01", role="student", institution_id=inst_id, apaar_id=apaar)

    # 1. Fetch unified dashboard
    resp = await client.get("/api/me/dashboard", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["student_profile"]["student_name"] == "Rohan Deshmukh"
    assert data["student_profile"]["institution_name"] == "Apex Engineering College"
    assert data["attendance_summary"]["attendance_rate"] >= 0
    assert "upcoming_examinations" in data

    # 2. Fetch timetable
    tt_resp = await client.get("/api/me/timetable", headers=auth_header(token))
    assert tt_resp.status_code == 200
    tt_data = tt_resp.json()
    assert len(tt_data) > 0
    assert "subject_name" in tt_data[0]

    # 3. Fetch assignments
    as_resp = await client.get("/api/me/assignments", headers=auth_header(token))
    assert as_resp.status_code == 200
    as_data = as_resp.json()
    assert len(as_data) > 0
    assert "title" in as_data[0]


@pytest.mark.asyncio
async def test_teacher_dashboard_and_assignments(client: AsyncClient):
    db = mongo.db()
    inst_id = "INST-TCH-01"
    teacher_id = "FAC-MATH-01"

    token = await seed_user_and_token(db, teacher_id, role="teacher", institution_id=inst_id, full_name="Prof. Sharma")

    # 1. Teacher dashboard
    dash_resp = await client.get("/api/teacher/dashboard", headers=auth_header(token))
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert dash_data["teacher_id"] == teacher_id
    assert "total_assigned_classes" in dash_data

    # 2. Create coursework assignment
    new_asn = {
        "target_id": "CLS-10A",
        "target_label": "Class 10-A",
        "subject_name": "Mathematics",
        "title": "Trigonometry Heights and Distances",
        "due_date": "2026-11-20",
        "max_marks": 25,
    }
    create_resp = await client.post("/api/teacher/assignments", json=new_asn, headers=auth_header(token))
    assert create_resp.status_code == 201
    created_id = create_resp.json()["assignment_id"]

    # 3. List assignments
    list_resp = await client.get("/api/teacher/assignments", headers=auth_header(token))
    assert list_resp.status_code == 200
    assignments = list_resp.json()
    assert any(a["assignment_id"] == created_id for a in assignments)


@pytest.mark.asyncio
async def test_parent_child_timetable_security(client: AsyncClient):
    db = mongo.db()
    inst_id = "INST-PAR-01"
    child_id = "STU-CHILD-7777"
    unlinked_child_id = "STU-CHILD-8888"
    parent_id = "USR-PARENT-99"

    # Seed verified link for child_id
    await db["guardian_relationships"].replace_one(
        {"parent_user_id": parent_id, "student_id": child_id},
        {
            "parent_user_id": parent_id,
            "student_id": child_id,
            "status": GuardianVerificationStatus.VERIFIED.value,
            "relationship": "Father",
            "institution_id": inst_id,
        },
        upsert=True,
    )

    token = await seed_user_and_token(db, parent_id, role="parent")

    # 1. Accessing verified child succeeds
    ok_resp = await client.get(f"/api/parent/children/{child_id}/timetable", headers=auth_header(token))
    assert ok_resp.status_code == 200
    assert len(ok_resp.json()) > 0

    # 2. Accessing unlinked student is rejected with 403 Forbidden
    forbidden_resp = await client.get(f"/api/parent/children/{unlinked_child_id}/timetable", headers=auth_header(token))
    assert forbidden_resp.status_code == 403
    assert "do not have verified guardian authorization" in forbidden_resp.json()["detail"]


@pytest.mark.asyncio
async def test_institution_dashboard_summary_and_scope_isolation(client: AsyncClient):
    db = mongo.db()
    inst_a = "INST-COLLEGE-A"
    inst_b = "INST-COLLEGE-B"

    await db["institutions"].replace_one(
        {"institution_id": inst_a},
        {
            "institution_id": inst_a,
            "name": "Delhi National College of Technology",
            "category": "COLLEGE",
            "city": "New Delhi",
            "state": "Delhi",
        },
        upsert=True,
    )
    await db["institutions"].replace_one(
        {"institution_id": inst_b},
        {
            "institution_id": inst_b,
            "name": "Mumbai Technical Institute",
            "category": "COLLEGE",
            "city": "Mumbai",
            "state": "Maharashtra",
        },
        upsert=True,
    )

    admin_a_token = await seed_user_and_token(db, "ADMIN-A", role="institution_admin", institution_id=inst_a)

    # 1. Admin A accesses their own institution summary
    ok_resp = await client.get(f"/api/institutions/{inst_a}/dashboard-summary", headers=auth_header(admin_a_token))
    assert ok_resp.status_code == 200
    data = ok_resp.json()
    assert data["institution_id"] == inst_a
    assert data["category"] == "COLLEGE"
    assert "metrics" in data
    assert data["metrics"]["enrolled_students"] > 0

    # 2. Admin A attempts to access Institution B summary -> rejected with 403 Forbidden
    forbidden_resp = await client.get(f"/api/institutions/{inst_b}/dashboard-summary", headers=auth_header(admin_a_token))
    assert forbidden_resp.status_code == 403
