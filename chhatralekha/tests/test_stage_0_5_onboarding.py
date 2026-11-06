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

    payload = {
        "institution_id": inst_id,
        "requested_role": "university_admin",
    }
    resp = await client.post("/api/onboarding/join-request", json=payload, headers=auth_header(token))
    # Should be rejected with 403 Forbidden
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
    assert "do not match" in resp_bad.json()["detail"]

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

    # 2. Legitimate completion routes to student workspace
    complete_resp = await client.post(
        "/api/onboarding/complete",
        json={"selected_role": "student", "institution_id": inst_id},
        headers=auth_header(token),
    )
    assert complete_resp.status_code == 200
    data = complete_resp.json()
    assert data["status"] == "completed"
    assert data["target_dashboard"] == "/me"

    user = await db["users"].find_one({"user_id": "FINISHER-01"})
    assert user["onboarding_completed"] is True
