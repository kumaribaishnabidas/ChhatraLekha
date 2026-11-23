"""Tests for Demo Academic Context Discovery and Contextual Student Demo Login."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_get_demo_academic_context(client):
    """Ensure GET /api/auth/demo-academic-context returns valid schools and colleges."""
    res = await client.get("/api/auth/demo-academic-context")
    assert res.status_code == 200
    data = res.json()
    assert "schools" in data
    assert "colleges" in data

    schools = data["schools"]
    colleges = data["colleges"]
    assert len(schools) >= 2
    assert len(colleges) >= 2

    # Verify school structure
    first_school = schools[0]
    assert "institution_id" in first_school
    assert "name" in first_school
    assert "classes" in first_school
    assert len(first_school["classes"]) > 0
    first_class = first_school["classes"][0]
    assert "class_name" in first_class
    assert "sections" in first_class

    # Verify college structure
    first_college = colleges[0]
    assert "institution_id" in first_college
    assert "name" in first_college
    assert "courses" in first_college
    assert len(first_college["courses"]) > 0
    first_course = first_college["courses"][0]
    assert "program_id" in first_course
    assert "semesters" in first_course


@pytest.mark.asyncio
async def test_demo_login_school_student_context(client):
    """Verify demo login with school academic context returns tokens and matched student record."""
    payload = {
        "role": "student",
        "education_type": "school",
        "institution_id": "SCH-DEL-001",
        "class_name": "Class 10",
        "section": "A",
    }
    res = await client.post("/api/auth/demo-login", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] == "student"

    # Authenticate with the issued token and verify profile reflects chosen school context
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    me_res = await client.get("/api/students/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["institution_id"] == "SCH-DEL-001"
    assert "GRADE-10" in me_data.get("program_id", "")


@pytest.mark.asyncio
async def test_demo_login_college_student_context(client):
    """Verify demo login with college academic context returns tokens and matched student record."""
    payload = {
        "role": "student",
        "education_type": "college",
        "institution_id": "INST-0421",
        "program_id": "BTECH_CSE",
        "semester": "Semester 5",
    }
    res = await client.post("/api/auth/demo-login", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] == "student"

    headers = {"Authorization": f"Bearer {data['access_token']}"}
    me_res = await client.get("/api/students/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["institution_id"] == "INST-0421"
    assert me_data["program_id"] == "BTECH_CSE"


@pytest.mark.asyncio
async def test_demo_login_invalid_school_institution(client):
    """Verify error when selecting a non-existent school."""
    payload = {
        "role": "student",
        "education_type": "school",
        "institution_id": "NON-EXISTENT-SCHOOL",
        "class_name": "Class 10",
    }
    res = await client.post("/api/auth/demo-login", json=payload)
    assert res.status_code == 404
    assert "not available" in res.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_demo_login_invalid_school_class(client):
    """Verify error when selecting an unsupported class for a school."""
    payload = {
        "role": "student",
        "education_type": "school",
        "institution_id": "SCH-DEL-001",
        "class_name": "Class 1",  # Not supported by Senior Secondary SCH-DEL-001
    }
    res = await client.post("/api/auth/demo-login", json=payload)
    assert res.status_code == 404
    assert "not offered" in res.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_demo_login_invalid_college_program(client):
    """Verify error when selecting an unsupported course program for a college."""
    payload = {
        "role": "student",
        "education_type": "college",
        "institution_id": "INST-0421",
        "program_id": "AERONAUTICAL_ENG",  # Not offered
        "semester": "Semester 1",
    }
    res = await client.post("/api/auth/demo-login", json=payload)
    assert res.status_code == 404
    assert "not offered" in res.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_demo_login_invalid_college_semester(client):
    """Verify error when selecting an out-of-range semester for a program."""
    payload = {
        "role": "student",
        "education_type": "college",
        "institution_id": "INST-0421",
        "program_id": "MBA_MGMT",  # 4 semesters only
        "semester": "Semester 8",
    }
    res = await client.post("/api/auth/demo-login", json=payload)
    assert res.status_code == 404
    assert "not offered" in res.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_demo_login_backward_compatibility_student_and_others(client):
    """Verify existing demo logins without context continue to function seamlessly."""
    # Student default
    res = await client.post("/api/auth/demo-login", json={"role": "student"})
    assert res.status_code == 200
    assert res.json()["role"] == "student"

    # Other roles including faculty and directorate aliases
    for role in ["parent", "teacher", "faculty", "school_admin", "college_admin", "university_admin", "directorate"]:
        r = await client.post("/api/auth/demo-login", json={"role": role})
        assert r.status_code == 200, f"Role {role} failed: {r.text}"
