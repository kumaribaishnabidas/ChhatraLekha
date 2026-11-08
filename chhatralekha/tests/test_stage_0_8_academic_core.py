"""Stage 0.8: Academic Management Core Automated Tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


@pytest.fixture
async def admin_auth_headers(async_client: AsyncClient):
    resp = await async_client.post("/api/auth/demo-login", json={"role": "school_admin"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def college_admin_headers(async_client: AsyncClient):
    resp = await async_client.post("/api/auth/demo-login", json={"role": "college_admin"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def student_auth_headers(async_client: AsyncClient):
    resp = await async_client.post("/api/auth/demo-login", json={"role": "student"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_academic_overview_and_explicit_seeding(async_client: AsyncClient, admin_auth_headers):
    """Verify that academic overview is read-only by default, and returns metrics after explicit seeding."""
    from app.api.academic import seed_academic_data
    from app.core.database import mongo

    # 1. Unseeded overview returns 0 counts and has zero write side effects
    res = await async_client.get("/api/academic/overview", headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "institution_id" in data
    inst_id = data["institution_id"]
    assert data["total_classes"] == 0
    assert data["total_subjects"] == 0
    assert data["total_enrolled_students"] == 0

    # 2. Explicitly seed academic data via the administrative function
    db = mongo.db()
    await seed_academic_data(db, inst_id)

    # 3. Subsequent overview reflects seeded records
    res_after = await async_client.get("/api/academic/overview", headers=admin_auth_headers)
    assert res_after.status_code == 200
    data_after = res_after.json()
    assert data_after["total_classes"] >= 1
    assert data_after["total_subjects"] >= 1
    assert data_after["total_enrolled_students"] >= 1


@pytest.mark.asyncio
async def test_academic_year_lifecycle_and_validation(async_client: AsyncClient, admin_auth_headers):
    """Test academic year creation, date validation, activation, and archiving without data loss."""
    # 1. Invalid date boundaries (start >= end) must fail
    invalid_payload = {
        "year_label": "2028-29",
        "start_date": "2029-06-01",
        "end_date": "2028-05-31",
        "is_current": False,
        "status": "UPCOMING",
        "terms": ["Term 1", "Term 2"],
    }
    res_bad = await async_client.post("/api/academic/years", json=invalid_payload, headers=admin_auth_headers)
    assert res_bad.status_code == 400
    assert "start_date must precede end_date" in res_bad.json()["detail"]

    # 2. Valid creation
    valid_payload = {
        "year_label": "2027-28",
        "start_date": "2027-06-01",
        "end_date": "2028-05-31",
        "admission_start_date": "2027-04-01",
        "admission_end_date": "2027-05-15",
        "is_current": False,
        "status": "UPCOMING",
        "terms": ["Monsoon", "Spring"],
    }
    res_ok = await async_client.post("/api/academic/years", json=valid_payload, headers=admin_auth_headers)
    assert res_ok.status_code == 200
    year_id = res_ok.json()["id"]

    # 3. Activate year
    res_act = await async_client.post(f"/api/academic/years/{year_id}/activate", headers=admin_auth_headers)
    assert res_act.status_code == 200
    assert res_act.json()["is_current"] is True

    # 4. Archive year (records must be retained)
    res_arch = await async_client.post(f"/api/academic/years/{year_id}/archive", headers=admin_auth_headers)
    assert res_arch.status_code == 200
    assert res_arch.json()["status"] == "ARCHIVED"
    assert res_arch.json()["is_current"] is False


@pytest.mark.asyncio
async def test_semester_term_management_and_validation(async_client: AsyncClient, admin_auth_headers):
    """Verify term creation and boundary validation."""
    bad_term = {
        "academic_year": "2025-26",
        "name": "Invalid Term",
        "term_type": "SEMESTER",
        "start_date": "2025-12-01",
        "end_date": "2025-06-01",
        "status": "ACTIVE",
    }
    res_bad = await async_client.post("/api/academic/terms", json=bad_term, headers=admin_auth_headers)
    assert res_bad.status_code == 400

    good_term = {
        "academic_year": "2025-26",
        "name": "Autumn Trimester",
        "term_type": "TRIMESTER",
        "start_date": "2025-08-01",
        "end_date": "2025-11-15",
        "status": "ACTIVE",
    }
    res_good = await async_client.post("/api/academic/terms", json=good_term, headers=admin_auth_headers)
    assert res_good.status_code == 200
    assert res_good.json()["name"] == "Autumn Trimester"

    # List terms
    res_list = await async_client.get("/api/academic/terms?academic_year=2025-26", headers=admin_auth_headers)
    assert res_list.status_code == 200
    terms = res_list.json()
    assert any(t["name"] == "Autumn Trimester" for t in terms)


@pytest.mark.asyncio
async def test_department_and_programme_hierarchy(async_client: AsyncClient, college_admin_headers):
    """Test department creation, programme linkage, and department programme count increment."""
    # 1. Create Department
    dept_payload = {
        "department_code": "BIO",
        "name": "Department of Biotechnology & Bioinformatics",
        "description": "Genomics and cellular biology studies.",
        "head_of_department_id": "FAC-088",
        "head_of_department_name": "Dr. Kavita Menon",
        "contact_email": "biotech@institution.edu.in",
        "campus_id": "EAST-CAMPUS",
    }
    dept_res = await async_client.post("/api/academic/departments", json=dept_payload, headers=college_admin_headers)
    assert dept_res.status_code == 200
    dept_data = dept_res.json()
    dept_id = dept_data["department_id"]

    # 2. Create Programme linked to department
    prg_payload = {
        "programme_code": "BTECH-BIO",
        "name": "Bachelor of Technology in Biotechnology",
        "department_id": dept_id,
        "academic_level": "UNDERGRADUATE",
        "duration_years": 4,
        "total_semesters": 8,
        "degree_awarded": "B.Tech",
        "approved_intake": 60,
    }
    prg_res = await async_client.post("/api/academic/programmes", json=prg_payload, headers=college_admin_headers)
    assert prg_res.status_code == 200
    prg_data = prg_res.json()
    assert prg_data["department_id"] == dept_id

    # 3. Verify department programme count updated
    depts_list = await async_client.get("/api/academic/departments", headers=college_admin_headers)
    assert depts_list.status_code == 200
    target_dept = next(d for d in depts_list.json() if d["department_id"] == dept_id)
    assert target_dept["programme_count"] >= 1


@pytest.mark.asyncio
async def test_subject_management_with_credits_and_multilingual(async_client: AsyncClient, admin_auth_headers):
    """Create subjects with credits, practical classifications, and multilingual representations."""
    subj_payload = {
        "subject_code": "PHY-10",
        "subject_name": "Physics Laboratory and Mechanics",
        "subject_name_hi": "भौतिकी प्रयोगशाला एवं यांत्रिकी",
        "category": "LAB",
        "applicable_to": "Class 10",
        "credits": 4.0,
        "theory_hours": 2,
        "practical_hours": 3,
        "is_practical": True,
    }
    res = await async_client.post("/api/academic/subjects", json=subj_payload, headers=admin_auth_headers)
    assert res.status_code == 200
    subj_data = res.json()
    assert subj_data["subject_code"] == "PHY-10"
    assert subj_data["credits"] == 4.0
    assert subj_data["is_practical"] is True
    assert subj_data["subject_name_hi"] == "भौतिकी प्रयोगशाला एवं यांत्रिकी"


@pytest.mark.asyncio
async def test_student_enrolment_and_duplicate_prevention(async_client: AsyncClient, admin_auth_headers):
    """Verify student enrolment and prevention of duplicate active enrolment in the same academic year."""
    enrol_payload = {
        "student_id": "STU-999-TEST",
        "student_name": "Vikram Adityaraj",
        "academic_year": "2025-26",
        "roll_number": "10-C-45",
        "class_name": "Class 10-C",
        "section": "C",
        "remarks": "Fresh admission candidate.",
    }
    # First enrolment succeeds
    res1 = await async_client.post("/api/academic/enrolments", json=enrol_payload, headers=admin_auth_headers)
    assert res1.status_code == 200
    enrol_data = res1.json()
    assert enrol_data["student_id"] == "STU-999-TEST"
    assert enrol_data["is_current"] is True

    # Duplicate active enrolment for same student & year must fail with 409 Conflict
    res2 = await async_client.post("/api/academic/enrolments", json=enrol_payload, headers=admin_auth_headers)
    assert res2.status_code == 409
    assert "already has an active enrolment" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_student_promotion_preserves_historical_records(async_client: AsyncClient, admin_auth_headers):
    """Promoting a student must mark previous enrolment as PROMOTED (is_current=False) and create a new active enrolment."""
    # 1. Enrol student in Class 9
    enrol_payload = {
        "student_id": "STU-PROMOTE-01",
        "student_name": "Ananya Joshi",
        "academic_year": "2024-25",
        "class_name": "Class 9-A",
        "section": "A",
        "remarks": "Academic Year 2024-25 entry.",
    }
    res = await async_client.post("/api/academic/enrolments", json=enrol_payload, headers=admin_auth_headers)
    assert res.status_code == 200
    enrol_id = res.json()["enrolment_id"]

    # 2. Promote to Class 10 (2025-26)
    promo_payload = {
        "target_academic_year": "2025-26",
        "target_grade_or_semester": "Class 10-A",
        "target_section": "A",
        "promotion_status": "PROMOTED",
        "remarks": "Promoted with Distinction (Grade A+).",
    }
    res_promo = await async_client.post(
        f"/api/academic/enrolments/{enrol_id}/promote",
        json=promo_payload,
        headers=admin_auth_headers,
    )
    assert res_promo.status_code == 200
    new_enrol = res_promo.json()
    assert new_enrol["academic_year"] == "2025-26"
    assert new_enrol["is_current"] is True

    # 3. Verify old enrolment record was preserved as historical record
    enrols_list = await async_client.get(
        "/api/academic/enrolments?student_id=STU-PROMOTE-01",
        headers=admin_auth_headers,
    )
    assert enrols_list.status_code == 200
    history = enrols_list.json()
    assert len(history) == 2
    old_rec = next(r for r in history if r["enrolment_id"] == enrol_id)
    assert old_rec["is_current"] is False
    assert old_rec["status"] == "PROMOTED"


@pytest.mark.asyncio
async def test_section_transfer_and_auditing(async_client: AsyncClient, admin_auth_headers):
    """Section transfer updates student section, remarks, and logs audit event."""
    from app.core.database import mongo

    enrol_payload = {
        "student_id": "STU-TRANSFER-01",
        "student_name": "Devendra Patil",
        "academic_year": "2025-26",
        "class_name": "Class 10",
        "section": "A",
    }
    res = await async_client.post("/api/academic/enrolments", json=enrol_payload, headers=admin_auth_headers)
    assert res.status_code == 200
    enrol_doc = res.json()
    enrol_id = enrol_doc["enrolment_id"]
    target_class_id = f"CLS-{enrol_doc['institution_id']}-TRANSFER-B"
    await mongo.db()["classes"].insert_one({
        "_id": target_class_id,
        "class_id": target_class_id,
        "institution_id": enrol_doc["institution_id"],
        "grade_level": "Class 10",
        "section": "B",
    })

    # Transfer from Section A to Section B
    transfer_payload = {
        "target_class_id": target_class_id,
        "target_section": "B",
        "transfer_reason": "Language elective scheduling accommodation.",
    }
    transfer_res = await async_client.post(
        f"/api/academic/enrolments/{enrol_id}/transfer-section",
        json=transfer_payload,
        headers=admin_auth_headers,
    )
    assert transfer_res.status_code == 200
    updated = transfer_res.json()
    assert updated["section"] == "B"
    assert "Language elective scheduling accommodation" in updated["remarks"]

    db = mongo.db()
    await db["classes"].insert_one({
        "_id": "CLS-FOREIGN-TENANT",
        "institution_id": "INST-OTHER",
        "class_name": "Class 10",
    })
    for invalid_class_id in ("CLS-DOES-NOT-EXIST", "CLS-FOREIGN-TENANT"):
        rejected = await async_client.post(
            f"/api/academic/enrolments/{enrol_id}/transfer-section",
            json={
                "target_class_id": invalid_class_id,
                "target_section": "C",
                "transfer_reason": "Invalid target validation test.",
            },
            headers=admin_auth_headers,
        )
        assert rejected.status_code == 404

    current = await async_client.get(
        "/api/academic/enrolments?student_id=STU-TRANSFER-01",
        headers=admin_auth_headers,
    )
    assert current.status_code == 200
    assert current.json()[0]["section"] == "B"
    assert current.json()[0]["class_id"] == transfer_payload["target_class_id"]


@pytest.mark.asyncio
async def test_faculty_assignments_lifecycle(async_client: AsyncClient, admin_auth_headers):
    """Create, list, and delete teacher assignments."""
    asn_payload = {
        "teacher_id": "FAC-TEST-09",
        "teacher_name": "Dr. Subhash Chandra",
        "subject_id": "SUB-TEST-CHEM",
        "subject_name": "Chemistry & Polymers",
        "target_type": "CLASS",
        "target_id": "CLS-10A",
        "target_label": "Class 10-A",
        "academic_year": "2025-26",
        "role_in_course": "PRIMARY_INSTRUCTOR",
    }
    res = await async_client.post("/api/academic/teacher-assignments", json=asn_payload, headers=admin_auth_headers)
    assert res.status_code == 200
    asn_id = res.json()["assignment_id"]

    # Delete assignment
    del_res = await async_client.delete(f"/api/academic/teacher-assignments/{asn_id}", headers=admin_auth_headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "DELETED"


@pytest.mark.asyncio
async def test_academic_calendar_events_and_validation(async_client: AsyncClient, admin_auth_headers):
    """Create and delete academic calendar events."""
    event_payload = {
        "academic_year": "2025-26",
        "title": "National Science Day Exhibition",
        "description": "Student science model presentations.",
        "event_type": "INSTITUTION_EVENT",
        "start_date": "2026-02-28",
        "end_date": "2026-02-28",
        "target_audience": "ALL",
        "is_holiday": False,
        "timezone": "Asia/Kolkata",
    }
    res = await async_client.post("/api/academic/calendar/events", json=event_payload, headers=admin_auth_headers)
    assert res.status_code == 200
    evt_id = res.json()["event_id"]

    del_res = await async_client.delete(f"/api/academic/calendar/events/{evt_id}", headers=admin_auth_headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "DELETED"


@pytest.mark.asyncio
async def test_unauthorized_access_prevented(async_client: AsyncClient, student_auth_headers):
    """Unauthorized student role cannot mutate academic years or enrolments (403 Forbidden)."""
    payload = {
        "year_label": "2030-31",
        "start_date": "2030-06-01",
        "end_date": "2031-05-31",
        "is_current": False,
        "status": "UPCOMING",
        "terms": ["Term 1"],
    }
    res = await async_client.post("/api/academic/years", json=payload, headers=student_auth_headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_get_requests_have_no_write_side_effects(async_client: AsyncClient, admin_auth_headers):
    """Verify all 10 GET academic endpoints are strictly read-only and have zero write side effects."""
    from app.core.database import mongo
    from app.core.security import create_access_token
    db = mongo.db()

    fresh_inst_id = "INST-READONLY-TEST"
    fresh_user_id = "USR-READONLY-TEST"
    await db["users"].insert_one({
        "user_id": fresh_user_id,
        "email": "readonly.admin@institution.test",
        "full_name": "Readonly Test Admin",
        "role": "school_admin",
        "institution_id": fresh_inst_id,
        "is_active": True,
    })
    token = create_access_token(
        subject=fresh_user_id,
        role="school_admin",
        institution_id=fresh_inst_id,
        extra_claims={"is_demo": True},
    )
    readonly_headers = {"Authorization": f"Bearer {token}"}

    # Cross-tenant IDOR check: admin from another institution cannot query fresh_inst_id
    res_cross = await async_client.get(f"/api/academic/years?institution_id={fresh_inst_id}", headers=admin_auth_headers)
    assert res_cross.status_code == 403

    collections = [
        "academic_years",
        "semester_terms",
        "departments",
        "programmes",
        "classes",
        "subjects",
        "student_enrolments",
        "teacher_assignments",
        "academic_calendar_events",
    ]

    for c in collections:
        count = await db[c].count_documents({"institution_id": fresh_inst_id})
        assert count == 0

    endpoints = [
        "/api/academic/overview",
        "/api/academic/years",
        "/api/academic/terms",
        "/api/academic/departments",
        "/api/academic/programmes",
        "/api/academic/classes",
        "/api/academic/subjects",
        "/api/academic/enrolments",
        "/api/academic/teacher-assignments",
        "/api/academic/calendar/events",
    ]

    for ep in endpoints:
        res = await async_client.get(ep, headers=readonly_headers)
        assert res.status_code == 200, f"Endpoint {ep} failed with {res.status_code}"

    for c in collections:
        count = await db[c].count_documents({"institution_id": fresh_inst_id})
        assert count == 0, f"Collection {c} had write side effects from GET queries!"


@pytest.mark.asyncio
async def test_hierarchy_validation_and_cross_tenant_isolation(async_client: AsyncClient, college_admin_headers):
    """Verify that referencing non-existent parent entities fails with HTTP 400."""
    # 1. Referencing non-existent department when creating programme fails
    bad_prg = {
        "programme_code": "MTECH-AI",
        "name": "M.Tech in Artificial Intelligence",
        "department_id": "DEP-NONEXISTENT-999",
        "academic_level": "POSTGRADUATE",
        "duration_years": 2,
        "total_semesters": 4,
        "degree_awarded": "M.Tech",
        "approved_intake": 30,
    }
    res_prg = await async_client.post("/api/academic/programmes", json=bad_prg, headers=college_admin_headers)
    assert res_prg.status_code == 400
    assert "not found in institution" in res_prg.json()["detail"]

    # 2. Referencing non-existent programme when creating class section fails
    bad_cls = {
        "grade_level": "Semester 1",
        "section": "A",
        "academic_year": "2025-26",
        "programme_id": "PRG-NONEXISTENT-888",
    }
    res_cls = await async_client.post("/api/academic/classes", json=bad_cls, headers=college_admin_headers)
    assert res_cls.status_code == 400
    assert "not found in institution" in res_cls.json()["detail"]

    # 3. Referencing non-existent department when creating subject fails
    bad_sub = {
        "subject_code": "CS-999",
        "subject_name": "Advanced Neural Networks",
        "applicable_to": "M.Tech",
        "department_id": "DEP-NONEXISTENT-999",
    }
    res_sub = await async_client.post("/api/academic/subjects", json=bad_sub, headers=college_admin_headers)
    assert res_sub.status_code == 400
    assert "not found in institution" in res_sub.json()["detail"]
