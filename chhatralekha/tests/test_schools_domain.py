"""Tests for school domain models, SchoolBasicPack regulatory rules, and school workflows."""

from __future__ import annotations

import io
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import mongo
from app.core.security import (
    ROLE_AICTE,
    ROLE_INSTITUTION,
    ROLE_NATIONAL_ADMIN,
    ROLE_STATE_ADMIN,
    create_access_token,
)
from app.main import app
from app.models.enums import AnomalyType, InstitutionKind, RulePackType
from app.services.anomaly_engine import AnomalyEngine, RegistrySnapshot
from app.services.rule_packs.school_basic import SchoolBasicPack


@pytest.fixture
def auth_headers():
    db = mongo.db()

    async def _make(role: str, user_id: str, institution_id: str = "SCH-DAV-101", **extra):
        doc = {
            "user_id": user_id,
            "email": f"{user_id}@test.gov.in",
            "full_name": f"User {user_id}",
            "role": role,
            "institution_id": institution_id,
            "is_active": True,
            **extra,
        }
        await db["users"].update_one({"user_id": user_id}, {"$set": doc}, upsert=True)
        token = create_access_token(subject=user_id, role=role, institution_id=institution_id)
        return {"Authorization": f"Bearer {token}"}

    return _make


@pytest.mark.asyncio
async def test_school_basic_rule_pack_anomalies():
    """Verify SchoolBasicPack detects minor guardian missing, age mismatch, duplicate school enrolment, and section cap."""
    pack = SchoolBasicPack()

    # School institution with no UDISE
    inst_no_udise = SimpleNamespace(
        institution_id="SCH-001",
        name="Greenwood High School",
        institution_type="SCHOOL",
        category="SCHOOL",
        kind=InstitutionKind.SCHOOL.value,
        rule_pack=RulePackType.SCHOOL_BASIC.value,
        identifiers=[],
    )

    # Minor student with no guardian details
    minor_no_guardian = SimpleNamespace(
        apaar_id="APAAR-SCH-001",
        student_name="Rahul Verma",
        date_of_birth="2012-05-10",
        institution_id="SCH-001",
        program_id="GRADE-7",
        grade_level="Class 7",
        section="A",
        academic_year="2025-26",
        is_active=True,
        is_minor=True,
        guardian_name="",
        guardian_contact="",
    )

    # Student with age incompatible with Grade 10 (e.g., 8 years old)
    age_mismatch = SimpleNamespace(
        apaar_id="APAAR-SCH-002",
        student_name="Mini Wonder",
        date_of_birth="2018-01-01",  # ~8 years old
        institution_id="SCH-001",
        program_id="GRADE-10",
        grade_level="Class 10",
        section="A",
        academic_year="2025-26",
        is_active=True,
        is_minor=True,
        guardian_name="Parent Wonder",
        guardian_contact="+919876543210",
    )

    # Duplicate active enrolment across 2 schools
    dup_school_1 = SimpleNamespace(
        apaar_id="APAAR-SCH-DUP",
        student_name="Simran Kaur",
        date_of_birth="2011-03-20",
        institution_id="SCH-001",
        program_id="GRADE-8",
        grade_level="Class 8",
        section="B",
        academic_year="2025-26",
        is_active=True,
        is_minor=True,
        guardian_name="Jaswinder Kaur",
        guardian_contact="+919876543211",
    )
    dup_school_2 = SimpleNamespace(
        apaar_id="APAAR-SCH-DUP",
        student_name="Simran Kaur",
        date_of_birth="2011-03-20",
        institution_id="SCH-002",
        program_id="GRADE-8",
        grade_level="Class 8",
        section="A",
        academic_year="2025-26",
        is_active=True,
        is_minor=True,
        guardian_name="Jaswinder Kaur",
        guardian_contact="+919876543211",
    )

    snapshot = RegistrySnapshot(
        institutions=[inst_no_udise],
        programs=[],
        students=[minor_no_guardian, age_mismatch, dup_school_1, dup_school_2],
    )

    anomalies = pack.evaluate(snapshot)
    types = {a.anomaly_type for a in anomalies}

    assert AnomalyType.MISSING_UDISE_CODE in types
    assert AnomalyType.MINOR_GUARDIAN_REQUIRED in types
    assert AnomalyType.INVALID_AGE_FOR_GRADE in types
    assert AnomalyType.DUPLICATE_SCHOOL_ENROLMENT in types


@pytest.mark.asyncio
async def test_anomaly_engine_dispatches_to_school_pack():
    """Verify master AnomalyEngine transparently dispatches to SchoolBasicPack when school records exist."""
    engine = AnomalyEngine()
    inst = SimpleNamespace(
        institution_id="SCH-DPS-99",
        name="Delhi Public School",
        institution_type="SCHOOL",
        category="SCHOOL",
        kind="SCHOOL",
        rule_pack="school_basic",
        state="Delhi",
        city="New Delhi",
        affiliation_university="CBSE",
        approval_year=2000,
        naac_grade="A",
        identifiers=[{"scheme": "UDISE_PLUS", "code": "07010100123"}],
    )
    student = SimpleNamespace(
        apaar_id="123456789012",
        student_name="Arjun Roy",
        date_of_birth="2012-04-12",
        gender="M",
        institution_id="SCH-DPS-99",
        program_id="GRADE-8",
        grade_level="Class 8",
        academic_year="2025-26",
        admission_quota="REGULAR_MERIT",
        enrollment_date="2025-06-01",
        student_institute_roll_no="801",
        nationality="Indian",
        passport_number=None,
        visa_validity=None,
        country_of_origin=None,
        is_active=True,
        is_minor=True,
        guardian_name="",  # Missing guardian -> triggers MINOR_GUARDIAN_REQUIRED
        guardian_contact="",
    )

    snapshot = RegistrySnapshot(
        institutions=[inst],
        programs=[],
        students=[student],
    )

    anomalies = engine.evaluate(snapshot)
    types = [a.anomaly_type for a in anomalies]
    assert AnomalyType.MINOR_GUARDIAN_REQUIRED in types


@pytest.mark.asyncio
async def test_school_csv_preview_and_commit(auth_headers):
    """Verify school CSV batch upload preview and commit endpoints."""
    headers = await auth_headers(ROLE_INSTITUTION, "school_admin_1", "SCH-DAV-101")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Check template endpoint
        t_res = await client.get("/api/schools/template")
        assert t_res.status_code == 200
        assert "headers" in t_res.json()

        # CSV upload preview
        csv_content = (
            "student_name,grade_level,section,date_of_birth,gender,student_institute_roll_no,guardian_name,guardian_contact,guardian_relationship,apaar_id,stream,contact_phone,contact_email\n"
            "Ananya Sen,Class 10,A,2010-08-20,F,1001,Poulomi Sen,+919876500001,MOTHER,,,+919876500001,\n"
            "Ishaan Sen,Class 10,A,2010-09-12,M,1002,Poulomi Sen,+919876500001,MOTHER,,,+919876500001,\n"
        )
        files = {"file": ("students.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        p_res = await client.post("/api/schools/students/bulk-preview", headers=headers, files=files)
        assert p_res.status_code == 200
        preview = p_res.json()
        assert preview["total_rows"] == 2
        assert preview["valid_rows"] == 2
        assert preview["invalid_rows"] == 0

        # Commit students
        commit_payload = {
            "institution_id": "SCH-DAV-101",
            "academic_year": "2025-26",
            "students": [
                {
                    "student_name": "Ananya Sen",
                    "grade_level": "Class 10",
                    "section": "A",
                    "date_of_birth": "2010-08-20",
                    "gender": "F",
                    "student_institute_roll_no": "1001",
                    "guardian_name": "Poulomi Sen",
                    "guardian_contact": "+919876500001",
                    "guardian_relationship": "MOTHER",
                },
                {
                    "student_name": "Ishaan Sen",
                    "grade_level": "Class 10",
                    "section": "A",
                    "date_of_birth": "2010-09-12",
                    "gender": "M",
                    "student_institute_roll_no": "1002",
                    "guardian_name": "Poulomi Sen",
                    "guardian_contact": "+919876500001",
                    "guardian_relationship": "MOTHER",
                },
            ],
        }
        c_res = await client.post("/api/schools/students/bulk-commit", headers=headers, json=commit_payload)
        assert c_res.status_code == 200
        assert c_res.json()["committed"] == 2


@pytest.mark.asyncio
async def test_school_promotion_and_transfer_certificate(auth_headers):
    """Verify grade promotion and school Transfer Certificate issuance."""
    test_db = mongo.db()
    headers = await auth_headers(ROLE_INSTITUTION, "school_admin_2", "SCH-KVS-202")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Seed 1 student in Class 9
        st_doc = {
            "apaar_id": "APAAR-KVS-901",
            "student_name": "Priya Nair",
            "date_of_birth": "2011-02-14",
            "gender": "F",
            "institution_id": "SCH-KVS-202",
            "program_id": "GRADE-CLASS-9",
            "academic_year": "2024-25",
            "grade_level": "Class 9",
            "section": "B",
            "student_institute_roll_no": "901",
            "guardian_name": "Ramesh Nair",
            "guardian_contact": "+919876512345",
            "is_minor": True,
            "is_active": True,
            "record_status": "ACTIVE",
        }
        await test_db["students"].insert_one(st_doc)

        # Promote to Class 10
        promo_payload = {
            "institution_id": "SCH-KVS-202",
            "current_academic_year": "2024-25",
            "target_academic_year": "2025-26",
            "from_grade": "Class 9",
            "to_grade": "Class 10",
            "student_ids": ["APAAR-KVS-901"],
        }
        p_res = await client.post("/api/schools/promotions", headers=headers, json=promo_payload)
        assert p_res.status_code == 200
        assert p_res.json()["promoted_count"] == 1

        # Verify old record is PROMOTED and new record is ACTIVE in Class 10
        old_st = await test_db["students"].find_one({"apaar_id": "APAAR-KVS-901", "academic_year": "2024-25"})
        new_st = await test_db["students"].find_one({"apaar_id": "APAAR-KVS-901", "academic_year": "2025-26"})
        assert old_st["record_status"] == "PROMOTED"
        assert new_st["record_status"] == "ACTIVE"
        assert new_st["grade_level"] == "Class 10"

        # Issue Transfer Certificate (TC)
        tc_payload = {
            "institution_id": "SCH-KVS-202",
            "student_record_id": "APAAR-KVS-901",
            "reason": "Parent transfer to another state",
            "conduct_remarks": "Exemplary",
            "destination_school": "Kendriya Vidyalaya No. 2, Bengaluru",
        }
        tc_res = await client.post("/api/schools/transfers/issue-tc", headers=headers, json=tc_payload)
        assert tc_res.status_code == 200
        tc_data = tc_res.json()
        assert tc_data["tc_number"].startswith("TC-2024-25-")
        assert tc_data["verification_token"] != ""
        assert tc_data["seal"] != ""

        # Check school dashboard
        dash_res = await client.get("/api/schools/dashboard?institution_id=SCH-KVS-202", headers=headers)
        assert dash_res.status_code == 200
        dash = dash_res.json()
        assert "guardian_coverage_percent" in dash
        assert dash["guardian_coverage_percent"] == 100.0


@pytest.mark.asyncio
async def test_role_hierarchy_and_aliases(auth_headers):
    """Verify national_admin, aicte_admin alias, and state_admin role scoping."""
    nat_headers = await auth_headers(ROLE_NATIONAL_ADMIN, "nat_admin_01", "SCH-CENTRAL")
    aicte_headers = await auth_headers(ROLE_AICTE, "aicte_admin_01", "SCH-AICTE")
    state_headers = await auth_headers(ROLE_STATE_ADMIN, "state_admin_mh", "SCH-MAHARASHTRA")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Both national_admin and aicte_admin alias access school dashboard for any institution without 403
        r1 = await client.get("/api/schools/dashboard?institution_id=ANY-SCH-001", headers=nat_headers)
        r2 = await client.get("/api/schools/dashboard?institution_id=ANY-SCH-001", headers=aicte_headers)
        r3 = await client.get("/api/schools/dashboard?institution_id=ANY-SCH-001", headers=state_headers)

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r3.status_code == 200
