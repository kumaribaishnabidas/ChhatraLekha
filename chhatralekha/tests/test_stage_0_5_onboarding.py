"""Test suite for Stage 0.5: User Onboarding, Role Selection, and Institution Joining.

Covers:
1. Onboarding status retrieval for newly registered users.
2. Updating basic profile (name, language, phone, avatar) during onboarding.
3. Institution discovery, search by query, and category filtering.
4. Privilege escalation rejection (403) on self-service join request.
5. Student join request submission and duplicate conflict prevention (409).
6. Parent-student verification: DOB mismatch rejection (400) vs valid match.
7. Teacher and institution admin join request submission.
8. Listing institution join requests scoped to authorized administrator.
9. Self-approval prevention invariant (admin cannot approve own request).
10. Administrative approval: institutional membership creation and notification.
11. Administrative rejection: status update and notification dispatch.
12. Onboarding completion and role-based dashboard routing.
13. Onboarding completion privilege escalation prevention.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.database import mongo
from app.core.security import create_access_token


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def create_user_helper(
    db,
    user_id: str,
    role: str = "verifier",
    institution_id: str | None = None,
    email: str | None = None,
    full_name: str | None = None,
    phone: str | None = None,
) -> str:
    email = email or f"{user_id.lower()}@chhatralekha.test"
    full_name = full_name or f"Test User {user_id}"
    await db["users"].insert_one({
        "user_id": user_id,
        "email": email,
        "full_name": full_name,
        "role": role,
        "institution_id": institution_id,
        "phone": phone,
        "is_active": True,
    })
    return create_access_token(
        subject=user_id,
        role=role,
        institution_id=institution_id,
        extra_claims={"display_name": full_name, "email": email},
    )


async def seed_institution_and_student(db):
    inst_id = "INST-TEST-001"
    await db["institutions"].replace_one(
        {"institution_id": inst_id},
        {
            "institution_id": inst_id,
            "name": "Delhi Institute of Technology",
            "category": "COLLEGE",
            "institution_type": "ENGINEERING",
            "city": "New Delhi",
            "state": "Delhi",
            "verification_status": "APPROVED",
            "is_active": True,
        },
        upsert=True,
    )
    student_id = "STU-APAAR-9999"
    await db["students"].replace_one(
        {"apaar_id": student_id},
        {
            "apaar_id": student_id,
            "student_name": "Aarav Sharma",
            "date_of_birth": "2005-08-15",
            "institution_id": inst_id,
            "student_institute_roll_no": "ROLL-2024-001",
        },
        upsert=True,
    )
    return inst_id, student_id


@pytest.mark.asyncio
async def test_onboarding_status_new_user(client: AsyncClient):
    db = mongo.db()
    token = await create_user_helper(db, "NEW-USER-01", role="student", full_name="Riya Sen")

    resp = await client.get("/api/onboarding/status", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "NEW-USER-01"
    assert data["full_name"] == "Riya Sen"
    assert data["profile_completed"] is False
    assert data["memberships_count"] == 0
    assert data["can_proceed_to_dashboard"] is False


@pytest.mark.asyncio
async def test_onboarding_profile_update(client: AsyncClient):
    db = mongo.db()
    token = await create_user_helper(db, "NEW-USER-02", role="verifier")

    payload = {
        "full_name": "Riya Sen",
        "preferred_language": "hi",
        "phone": "+919876543210",
        "avatar_url": "/avatars/avatar-1.png",
    }
    resp = await client.post("/api/onboarding/profile", json=payload, headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["full_name"] == "Riya Sen"
    assert data["preferred_language"] == "hi"

    user_doc = await db["users"].find_one({"user_id": "NEW-USER-02"})
    assert user_doc["full_name"] == "Riya Sen"
    assert user_doc["phone"] == "+919876543210"
    assert user_doc["preferred_language"] == "hi"


@pytest.mark.asyncio
async def test_institution_discovery_search_and_filter(client: AsyncClient):
    db = mongo.db()
    inst_id, _ = await seed_institution_and_student(db)
    token = await create_user_helper(db, "SEARCHER-01")

    # Search with query matching name
    resp = await client.get("/api/onboarding/institutions?q=Delhi", headers=auth_header(token))
    assert resp.status_code == 200
    items = resp.json()
    assert any(i["institution_id"] == inst_id for i in items)

    # Search with category filter
    resp_college = await client.get("/api/onboarding/institutions?category=COLLEGE", headers=auth_header(token))
    assert resp_college.status_code == 200
    assert all(i["category"] == "COLLEGE" for i in resp_college.json())


@pytest.mark.asyncio
async def test_join_request_privilege_escalation_forbidden(client: AsyncClient):
    db = mongo.db()
    inst_id, _ = await seed_institution_and_student(db)
    token = await create_user_helper(db, "ATTACKER-01")

    for restricted_role in ("university_admin", "academic_admin", "verifier"):
        payload = {
            "institution_id": inst_id,
            "requested_role": restricted_role,
        }
        resp = await client.post("/api/onboarding/join-request", json=payload, headers=auth_header(token))
        assert resp.status_code == 403
        assert "Security violation" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_join_request_student_and_duplicate_conflict(client: AsyncClient):
    db = mongo.db()
    inst_id, _ = await seed_institution_and_student(db)
    token = await create_user_helper(db, "STU-APPLICANT-01", full_name="Karan Verma")

    payload = {
        "institution_id": inst_id,
        "requested_role": "student",
        "course_name": "B.Tech Computer Science",
        "class_grade": "3rd Year",
        "academic_year": "2024-25",
        "student_identifier": "ROLL-2024-001",
    }
    # 1. First submission succeeds
    resp1 = await client.post("/api/onboarding/join-request", json=payload, headers=auth_header(token))
    assert resp1.status_code == 201
    data1 = resp1.json()
    assert data1["status"] == "PENDING"
    assert data1["institution_id"] == inst_id
    assert data1["requested_role"] == "student"

    # 2. Duplicate submission triggers 409 Conflict
    resp2 = await client.post("/api/onboarding/join-request", json=payload, headers=auth_header(token))
    assert resp2.status_code == 409
    assert "already have a pending join request" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_parent_linking_dob_verification(client: AsyncClient):
    db = mongo.db()
    inst_id, student_apaar = await seed_institution_and_student(db)
    token = await create_user_helper(db, "PARENT-APPLICANT-01", role="parent", full_name="Sunita Sharma")

    # 1. Mismatched Date of Birth -> Rejected
    bad_payload = {
        "institution_id": inst_id,
        "requested_role": "parent",
        "student_identifier": student_apaar,
        "student_dob": "2000-01-01",  # Real is 2005-08-15
        "relationship": "Mother",
    }
    resp_bad = await client.post("/api/onboarding/join-request", json=bad_payload, headers=auth_header(token))
    assert resp_bad.status_code == 400
    assert "unable to verify" in resp_bad.json()["detail"].lower()

    # 2. Matching Date of Birth -> Accepted into pending state
    good_payload = {
        "institution_id": inst_id,
        "requested_role": "parent",
        "student_identifier": student_apaar,
        "student_dob": "2005-08-15",
        "relationship": "Mother",
    }
    resp_good = await client.post("/api/onboarding/join-request", json=good_payload, headers=auth_header(token))
    assert resp_good.status_code == 201
    data = resp_good.json()
    assert data["status"] == "PENDING"

    # Verify pending relationship created
    glink = await db["guardian_relationships"].find_one({"parent_user_id": "PARENT-APPLICANT-01"})
    assert glink is not None
    assert glink["status"] == "PENDING"
    assert glink["student_name"] == "Aarav Sharma"
    assert glink["institution_id"] == inst_id
    assert glink["student_id"] == student_apaar


@pytest.mark.asyncio
async def test_parent_join_request_requires_identifier_and_dob(client: AsyncClient):
    db = mongo.db()
    inst_id, student_apaar = await seed_institution_and_student(db)
    token = await create_user_helper(db, "PARENT-MISSING-DATA", role="parent")
    payload = {
        "institution_id": inst_id,
        "requested_role": "parent",
        "student_identifier": student_apaar,
        "student_dob": "2005-08-15",
        "relationship": "Guardian",
    }

    missing_identifier = await client.post(
        "/api/onboarding/join-request",
        json={key: value for key, value in payload.items() if key != "student_identifier"},
        headers=auth_header(token),
    )
    missing_dob = await client.post(
        "/api/onboarding/join-request",
        json={key: value for key, value in payload.items() if key != "student_dob"},
        headers=auth_header(token),
    )

    assert missing_identifier.status_code == missing_dob.status_code == 400
    assert missing_identifier.json()["detail"] == missing_dob.json()["detail"]
    assert await db["guardian_relationships"].count_documents({"parent_user_id": "PARENT-MISSING-DATA"}) == 0


@pytest.mark.asyncio
async def test_parent_join_request_is_scoped_to_institution_and_uses_uniform_failure(client: AsyncClient):
    db = mongo.db()
    inst_id, student_apaar = await seed_institution_and_student(db)
    other_inst_id = "INST-TEST-002"
    await db["institutions"].insert_one({"institution_id": other_inst_id, "name": "Other Institute"})
    token = await create_user_helper(db, "PARENT-SCOPE-01", role="parent")

    base_payload = {
        "institution_id": inst_id,
        "requested_role": "parent",
        "student_identifier": student_apaar,
        "student_dob": "2005-08-15",
        "relationship": "Guardian",
    }
    wrong_tenant = await client.post(
        "/api/onboarding/join-request",
        json={**base_payload, "institution_id": other_inst_id},
        headers=auth_header(token),
    )
    nonexistent_identifier = await client.post(
        "/api/onboarding/join-request",
        json={**base_payload, "student_identifier": "NO-SUCH-STUDENT"},
        headers=auth_header(token),
    )
    wrong_dob = await client.post(
        "/api/onboarding/join-request",
        json={**base_payload, "student_dob": "2000-01-01"},
        headers=auth_header(token),
    )

    assert [wrong_tenant.status_code, nonexistent_identifier.status_code, wrong_dob.status_code] == [400, 400, 400]
    assert wrong_tenant.json()["detail"] == nonexistent_identifier.json()["detail"] == wrong_dob.json()["detail"]
    assert await db["guardian_relationships"].count_documents({"parent_user_id": "PARENT-SCOPE-01"}) == 0


@pytest.mark.asyncio
async def test_guardian_verification_and_portal_fail_closed_for_cross_tenant_links(client: AsyncClient):
    db = mongo.db()
    _inst_id, student_apaar = await seed_institution_and_student(db)
    other_inst_id = "INST-OTHER-002"
    admin_token = await create_user_helper(
        db, "OTHER-INST-ADMIN", role="institution_admin", institution_id=other_inst_id
    )
    parent_token = await create_user_helper(db, "PARENT-CROSS-TENANT", role="parent")
    await db["guardian_relationships"].insert_one({
        "_id": "GLINK-CROSS-TENANT",
        "link_id": "GLINK-CROSS-TENANT",
        "parent_user_id": "PARENT-CROSS-TENANT",
        "student_id": student_apaar,
        "institution_id": other_inst_id,
        "status": "PENDING",
    })

    verify = await client.post(
        "/api/parent/link/GLINK-CROSS-TENANT/verify",
        json={"verification_status": "VERIFIED"},
        headers=auth_header(admin_token),
    )
    assert verify.status_code == 404
    link = await db["guardian_relationships"].find_one({"_id": "GLINK-CROSS-TENANT"})
    assert link["status"] == "PENDING"

    link["status"] = "VERIFIED"
    await db["guardian_relationships"].replace_one({"_id": link["_id"]}, link)
    children = await client.get("/api/parent/children", headers=auth_header(parent_token))
    assert children.status_code == 200
    assert children.json() == []


@pytest.mark.asyncio
async def test_guardian_portal_scopes_academic_records_to_linked_institution(client: AsyncClient):
    db = mongo.db()
    inst_id, student_apaar = await seed_institution_and_student(db)
    other_inst_id = "INST-ACADEMIC-OTHER"
    parent_token = await create_user_helper(db, "PARENT-ACADEMIC-SCOPE", role="parent")
    await db["students"].update_one(
        {"apaar_id": student_apaar},
        {"$set": {"academic_year": "2024-25", "program_id": "Synthetic test programme"}},
    )
    await db["guardian_relationships"].insert_one({
        "_id": "GLINK-ACADEMIC-SCOPE",
        "parent_user_id": "PARENT-ACADEMIC-SCOPE",
        "student_id": student_apaar,
        "student_name": "Aarav Sharma",
        "institution_id": inst_id,
        "relationship": "Guardian",
        "status": "VERIFIED",
    })
    await db["attendance_records"].insert_many([
        {"institution_id": inst_id, "student_id": student_apaar, "status": "PRESENT"},
        {"institution_id": other_inst_id, "student_id": student_apaar, "status": "ABSENT"},
    ])
    await db["assessments"].insert_one({
        "_id": "ASM-FOREIGN-TENANT",
        "institution_id": other_inst_id,
        "name": "Foreign synthetic assessment",
        "term": "Test term",
        "subject_name": "Test subject",
        "status": "PUBLISHED",
    })
    await db["assessment_marks"].insert_one({
        "institution_id": other_inst_id,
        "assessment_id": "ASM-FOREIGN-TENANT",
        "student_id": student_apaar,
        "is_published": True,
        "marks_obtained": 99.0,
        "max_marks": 100.0,
        "passing_marks": 35.0,
        "percentage": 99.0,
        "grade": "A+",
        "status": "PASS",
    })

    response = await client.get(
        "/api/parent/children",
        headers=auth_header(parent_token),
    )
    assert response.status_code == 200
    overview = response.json()[0]
    assert overview["total_sessions"] == 1
    assert overview["present_sessions"] == 1
    assert overview["attendance_percentage"] == 100.0
    assert overview["published_results"] == []


@pytest.mark.asyncio
async def test_admin_join_request_lifecycle_and_self_approval_prevention(client: AsyncClient):
    db = mongo.db()
    inst_id, _ = await seed_institution_and_student(db)

    # Institution admin user
    admin_token = await create_user_helper(
        db,
        "INST-ADMIN-01",
        role="institution_admin",
        institution_id=inst_id,
        full_name="Principal Rajesh Gupta",
    )

    # Applicant user
    applicant_token = await create_user_helper(
        db,
        "TEACHER-APPLICANT-01",
        role="verifier",
        full_name="Dr. Meera Nambiar",
    )

    # 1. Applicant submits join request for teacher
    t_payload = {
        "institution_id": inst_id,
        "requested_role": "teacher",
        "department": "Computer Science",
        "subject_specialization": "Distributed Systems",
        "employee_id": "FAC-CS-88",
    }
    sub_resp = await client.post("/api/onboarding/join-request", json=t_payload, headers=auth_header(applicant_token))
    assert sub_resp.status_code == 201
    request_id = sub_resp.json()["request_id"]

    # 2. Institution admin lists join requests
    list_resp = await client.get(f"/api/institutions/{inst_id}/join-requests", headers=auth_header(admin_token))
    assert list_resp.status_code == 200
    requests = list_resp.json()
    assert any(r["request_id"] == request_id for r in requests)

    # 3. Security invariant: Self-approval prevention
    # Suppose admin submits a join request for themselves
    self_sub = await client.post("/api/onboarding/join-request", json={
        "institution_id": inst_id,
        "requested_role": "teacher",
        "department": "Math",
    }, headers=auth_header(admin_token))
    assert self_sub.status_code == 201
    self_request_id = self_sub.json()["request_id"]

    # Admin tries to approve their own request -> 400 Bad Request
    self_review = await client.post(
        f"/api/institutions/{inst_id}/join-requests/{self_request_id}/review",
        json={"decision": "APPROVED", "notes": "Self approval attempt"},
        headers=auth_header(admin_token),
    )
    assert self_review.status_code == 400
    assert "cannot approve their own join requests" in self_review.json()["detail"]

    # 4. Admin approves legitimate teacher request
    review_resp = await client.post(
        f"/api/institutions/{inst_id}/join-requests/{request_id}/review",
        json={"decision": "APPROVED", "notes": "Verified faculty credentials."},
        headers=auth_header(admin_token),
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["status"] == "APPROVED"

    # Verify membership created in DB
    membership = await db["institution_memberships"].find_one({
        "user_id": "TEACHER-APPLICANT-01",
        "institution_id": inst_id,
    })
    assert membership is not None
    assert membership["member_status"] == "ACTIVE"
    assert membership["role"] == "teacher"

    # Verify notification delivered to teacher
    notif = await db["notifications"].find_one({
        "user_id": "TEACHER-APPLICANT-01",
        "category": "MEMBERSHIP",
    })
    assert notif is not None
    assert "Membership Approved" in notif["title"]


@pytest.mark.asyncio
async def test_admin_reject_join_request_with_notification(client: AsyncClient):
    db = mongo.db()
    inst_id, _ = await seed_institution_and_student(db)

    admin_token = await create_user_helper(
        db,
        "INST-ADMIN-02",
        role="institution_admin",
        institution_id=inst_id,
    )
    applicant_token = await create_user_helper(
        db,
        "REJECT-APPLICANT-01",
        role="verifier",
        full_name="Invalid Applicant",
    )

    sub_resp = await client.post(
        "/api/onboarding/join-request",
        json={"institution_id": inst_id, "requested_role": "student"},
        headers=auth_header(applicant_token),
    )
    assert sub_resp.status_code == 201
    request_id = sub_resp.json()["request_id"]

    # Reject request
    reject_resp = await client.post(
        f"/api/institutions/{inst_id}/join-requests/{request_id}/review",
        json={"decision": "REJECTED", "notes": "No matching admission record found."},
        headers=auth_header(admin_token),
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "REJECTED"

    # Verify rejection notification
    notif = await db["notifications"].find_one({
        "user_id": "REJECT-APPLICANT-01",
        "category": "MEMBERSHIP",
    })
    assert notif is not None
    assert "was not approved" in notif["message"]


@pytest.mark.asyncio
async def test_onboarding_completion_routing_and_privilege_prevention(client: AsyncClient):
    db = mongo.db()
    inst_id, _ = await seed_institution_and_student(db)
    token = await create_user_helper(db, "FINISHER-01")

    # 1. Privilege escalation in complete payload is forbidden
    escalate_resp = await client.post(
        "/api/onboarding/complete",
        json={"selected_role": "aicte_admin", "institution_id": inst_id},
        headers=auth_header(token),
    )
    assert escalate_resp.status_code == 403

    # A rejected escalation must not have written role or tenant.
    untouched = await db["users"].find_one({"user_id": "FINISHER-01"})
    assert untouched["role"] == "verifier"
    assert untouched.get("institution_id") is None

    # 2. Completion records the journey and keeps the caller's authorization.
    complete_resp = await client.post(
        "/api/onboarding/complete",
        json={"selected_role": "student", "institution_id": inst_id},
        headers=auth_header(token),
    )
    assert complete_resp.status_code == 200
    data = complete_resp.json()
    assert data["status"] == "completed"
    assert data["selected_role"] == "verifier"
    assert data["target_dashboard"] == "/dashboard"

    user = await db["users"].find_one({"user_id": "FINISHER-01"})
    assert user["onboarding_completed"] is True
    assert user["role"] == "verifier"
    assert user.get("institution_id") is None


@pytest.mark.asyncio
async def test_complete_onboarding_cannot_grant_institution_admin(client: AsyncClient):
    db = mongo.db()
    inst_id, _ = await seed_institution_and_student(db)
    token = await create_user_helper(db, "VERIFIER-ESCALATE-01", role="verifier")

    response = await client.post(
        "/api/onboarding/complete",
        json={"selected_role": "institution_admin", "institution_id": inst_id},
        headers=auth_header(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["selected_role"] == "verifier"
    assert body["target_dashboard"] == "/dashboard"

    user = await db["users"].find_one({"user_id": "VERIFIER-ESCALATE-01"})
    assert user["role"] == "verifier"
    assert user.get("institution_id") is None
    assert user.get("active_institution_id") is None


@pytest.mark.asyncio
async def test_complete_onboarding_cannot_move_teacher_to_another_institution(
    client: AsyncClient,
):
    db = mongo.db()
    home_id, _ = await seed_institution_and_student(db)
    other_id = "INST-TEST-002"
    await db["institutions"].replace_one(
        {"institution_id": other_id},
        {
            "institution_id": other_id,
            "name": "Other College",
            "category": "COLLEGE",
            "institution_type": "ENGINEERING",
            "city": "Mumbai",
            "state": "Maharashtra",
            "verification_status": "APPROVED",
            "is_active": True,
        },
        upsert=True,
    )
    token = await create_user_helper(
        db,
        "TEACHER-TENANT-01",
        role="teacher",
        institution_id=home_id,
    )

    response = await client.post(
        "/api/onboarding/complete",
        json={"selected_role": "institution_admin", "institution_id": other_id},
        headers=auth_header(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["selected_role"] == "teacher"
    assert body["target_dashboard"] == "/teacher"

    user = await db["users"].find_one({"user_id": "TEACHER-TENANT-01"})
    assert user["role"] == "teacher"
    assert user["institution_id"] == home_id
    assert user.get("active_institution_id") in (None, home_id)
