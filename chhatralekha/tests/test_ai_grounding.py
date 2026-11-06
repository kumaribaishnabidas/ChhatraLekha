"""Tests for the grounded, authorisation-aware assistant.

These tests focus on the properties that matter:

* a student only ever sees their own record;
* a parent only sees a verified ward;
* a client-supplied role or student id cannot widen the scope;
* drafts are never leaked as published results;
* missing data produces an honest answer, not an invented one.
"""

from __future__ import annotations

import pytest

from app.core.database import mongo
from app.core.security import create_access_token


def _bearer(user_id: str, role: str, institution_id: str | None = None) -> dict[str, str]:
    token = create_access_token(
        subject=user_id,
        role=role,
        institution_id=institution_id,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def ai(client):
    """A small campus with two institutions, one verified ward and some drafts."""
    db = mongo.db()

    await db["institutions"].insert_many(
        [
            {"institution_id": "INST-AI", "name": "Sunrise Public School", "is_active": True},
            {"institution_id": "INST-B", "name": "Other College", "is_active": True},
        ]
    )
    await db["programmes"].insert_one(
        {
            "institution_id": "INST-AI",
            "program_id": "PROG-AI",
            "program_name": "Class 10",
            "program_level": "SCHOOL",
            "academic_year": "2025-26",
            "approved_intake": 40,
            "total_sanctioned": 40,
        }
    )
    await db["students"].insert_many(
        [
            {
                "apaar_id": "STU-OWN",
                "student_name": "Aarav Own",
                "institution_id": "INST-AI",
                "program_id": "PROG-AI",
                "academic_year": "2025-26",
                "grade_level": "Class 10",
                "section": "A",
                "record_status": "ACTIVE",
                "is_active": True,
            },
            {
                "apaar_id": "STU-OTHER",
                "student_name": "Meera Other",
                "institution_id": "INST-AI",
                "program_id": "PROG-AI",
                "academic_year": "2025-26",
                "grade_level": "Class 10",
                "section": "B",
                "record_status": "ACTIVE",
                "is_active": True,
            },
            {
                "apaar_id": "STU-WARD2",
                "student_name": "Kabir Second",
                "institution_id": "INST-B",
                "program_id": "PROG-B",
                "academic_year": "2025-26",
                "record_status": "ACTIVE",
                "is_active": True,
            },
        ]
    )
    await db["classes"].insert_one(
        {
            "_id": "CLS-INST-AI-CLASS_10-A-2025-26",
            "class_id": "CLS-INST-AI-CLASS_10-A-2025-26",
            "institution_id": "INST-AI",
            "grade_level": "Class 10",
            "section": "A",
            "academic_year": "2025-26",
        }
    )
    await db["users"].insert_many(
        [
            {
                "user_id": "USR-STU-AI",
                "email": "aarav@ai.test",
                "full_name": "Aarav Own",
                "role": "student",
                "apaar_id": "STU-OWN",
                "institution_id": "INST-AI",
                "is_active": True,
            },
            {
                "user_id": "USR-PARENT-AI",
                "email": "parent@ai.test",
                "full_name": "Parent Own",
                "role": "parent",
                "is_active": True,
            },
            {
                "user_id": "USR-PARENT-NOLINK",
                "email": "unlinked@ai.test",
                "full_name": "Unlinked Parent",
                "role": "parent",
                "is_active": True,
            },
            {
                "user_id": "USR-TEACH-AI",
                "email": "teacher@ai.test",
                "full_name": "Teacher One",
                "role": "teacher",
                "institution_id": "INST-AI",
                "is_active": True,
            },
            {
                "user_id": "USR-ADMIN-AI",
                "email": "admin@ai.test",
                "full_name": "Admin One",
                "role": "institution_admin",
                "institution_id": "INST-AI",
                "is_active": True,
            },
            {
                "user_id": "USR-NAT-AI",
                "email": "national@ai.test",
                "full_name": "National Admin",
                "role": "aicte_admin",
                "is_active": True,
            },
            {
                "user_id": "USR-VER-AI",
                "email": "verifier@ai.test",
                "full_name": "Verifier",
                "role": "verifier",
                "is_active": True,
            },
        ]
    )
    await db["guardian_relationships"].insert_many(
        [
            {
                "link_id": "GLINK-1",
                "parent_user_id": "USR-PARENT-AI",
                "student_id": "STU-OWN",
                "institution_id": "INST-AI",
                "status": "VERIFIED",
            },
            {
                "link_id": "GLINK-2",
                "parent_user_id": "USR-PARENT-AI",
                "student_id": "STU-OTHER",
                "institution_id": "INST-AI",
                "status": "PENDING",
            },
        ]
    )

    await db["attendance_records"].insert_many(
        [
            {"student_id": "STU-OWN", "institution_id": "INST-AI", "status": "PRESENT", "session_date": "2026-10-01", "target_label": "Class 10-A"},
            {"student_id": "STU-OWN", "institution_id": "INST-AI", "status": "PRESENT", "session_date": "2026-10-02", "target_label": "Class 10-A"},
            {"student_id": "STU-OWN", "institution_id": "INST-AI", "status": "LATE", "session_date": "2026-10-03", "target_label": "Class 10-A"},
            {"student_id": "STU-OWN", "institution_id": "INST-AI", "status": "ABSENT", "session_date": "2026-10-04", "target_label": "Class 10-A"},
            {"student_id": "STU-OTHER", "institution_id": "INST-AI", "status": "ABSENT", "session_date": "2026-10-01", "target_label": "Class 10-B"},
            {"student_id": "STU-OTHER", "institution_id": "INST-AI", "status": "ABSENT", "session_date": "2026-10-02", "target_label": "Class 10-B"},
            {"student_id": "STU-WARD2", "institution_id": "INST-B", "status": "PRESENT", "session_date": "2026-10-01", "target_label": "B.A."},
            {"student_id": "STU-WARD2", "institution_id": "INST-B", "status": "PRESENT", "session_date": "2026-10-02", "target_label": "B.A."},
        ]
    )
    await db["attendance_sessions"].insert_many(
        [
            {"session_id": "ATT-1", "institution_id": "INST-AI", "target_id": "CLS-INST-AI-CLASS_10-A-2025-26"},
            {"session_id": "ATT-2", "institution_id": "INST-AI", "target_id": "CLS-INST-AI-CLASS_10-A-2025-26"},
            {"session_id": "ATT-3", "institution_id": "INST-B", "target_id": "PROG-B"},
        ]
    )

    await db["assessments"].insert_many(
        [
            {
                "_id": "ASM-1",
                "assessment_id": "ASM-1",
                "institution_id": "INST-AI",
                "name": "Mid-Term",
                "term": "Term 1",
                "subject_name": "Mathematics",
                "status": "PUBLISHED",
                "max_marks": 100.0,
            },
            {
                "_id": "ASM-2",
                "assessment_id": "ASM-2",
                "institution_id": "INST-AI",
                "name": "Draft Quiz",
                "term": "Term 1",
                "subject_name": "Science",
                "status": "DRAFT",
                "max_marks": 50.0,
            },
            {
                "_id": "ASM-3",
                "assessment_id": "ASM-3",
                "institution_id": "INST-AI",
                "name": "Final",
                "term": "Term 2",
                "subject_name": "English",
                "status": "PUBLISHED",
                "max_marks": 100.0,
            },
        ]
    )
    await db["assessment_marks"].insert_many(
        [
            {
                "assessment_id": "ASM-1",
                "institution_id": "INST-AI",
                "student_id": "STU-OWN",
                "marks_obtained": 80.0,
                "max_marks": 100.0,
                "percentage": 80.0,
                "grade": "A",
                "status": "PASS",
                "is_published": True,
            },
            {
                "assessment_id": "ASM-2",
                "institution_id": "INST-AI",
                "student_id": "STU-OWN",
                "marks_obtained": 45.0,
                "max_marks": 50.0,
                "percentage": 90.0,
                "grade": "A+",
                "status": "PASS",
                "is_published": True,
            },
            {
                "assessment_id": "ASM-3",
                "institution_id": "INST-AI",
                "student_id": "STU-OWN",
                "marks_obtained": 70.0,
                "max_marks": 100.0,
                "percentage": 70.0,
                "grade": "B",
                "status": "PASS",
                "is_published": False,
            },
            {
                "assessment_id": "ASM-1",
                "institution_id": "INST-AI",
                "student_id": "STU-OTHER",
                "marks_obtained": 40.0,
                "max_marks": 100.0,
                "percentage": 40.0,
                "grade": "D",
                "status": "FAIL",
                "is_published": True,
            },
        ]
    )

    await db["announcements"].insert_many(
        [
            {
                "announcement_id": "ANN-1",
                "institution_id": "INST-AI",
                "title": "Sports day",
                "content": "Sports day on Friday.",
                "priority": "NORMAL",
                "target_scope": "ALL",
                "published_at": "2026-10-05T09:00:00+00:00",
            },
            {
                "announcement_id": "ANN-2",
                "institution_id": "INST-AI",
                "title": "Class 10-A test",
                "content": "Bring your geometry box.",
                "priority": "HIGH",
                "target_scope": "CLASS",
                "target_id": "CLS-INST-AI-CLASS_10-A-2025-26",
                "published_at": "2026-10-06T09:00:00+00:00",
            },
            {
                "announcement_id": "ANN-3",
                "institution_id": "INST-B",
                "title": "Other campus",
                "content": "Not for this campus.",
                "priority": "NORMAL",
                "target_scope": "ALL",
                "published_at": "2026-10-07T09:00:00+00:00",
            },
        ]
    )

    await db["anomalies"].insert_many(
        [
            {"anomaly_id": "ANOM-1", "institution_id": "INST-AI", "severity": "CRITICAL", "anomaly_type": "DUPLICATE_APAAR"},
            {"anomaly_id": "ANOM-2", "institution_id": "INST-AI", "severity": "HIGH", "anomaly_type": "INTAKE_BREACH"},
            {"anomaly_id": "ANOM-3", "institution_id": "INST-B", "severity": "CRITICAL", "anomaly_type": "DUPLICATE_APAAR"},
        ]
    )

    await db["teacher_assignments"].insert_many(
        [
            {
                "assignment_id": "TA-1",
                "institution_id": "INST-AI",
                "teacher_id": "USR-TEACH-AI",
                "teacher_name": "Teacher One",
                "subject_name": "Mathematics",
                "target_id": "CLS-INST-AI-CLASS_10-A-2025-26",
                "target_label": "Class 10-A",
                "target_type": "CLASS",
            },
            {
                "assignment_id": "TA-2",
                "institution_id": "INST-AI",
                "teacher_id": "USR-TEACH-AI",
                "teacher_name": "Teacher One",
                "subject_name": "Science",
                "target_id": "PROG-AI",
                "target_label": "Class 10",
                "target_type": "PROGRAMME",
            },
        ]
    )

    return {
        "db": db,
        "student": _bearer("USR-STU-AI", "student", "INST-AI"),
        "parent": _bearer("USR-PARENT-AI", "parent"),
        "unlinked_parent": _bearer("USR-PARENT-NOLINK", "parent"),
        "teacher": _bearer("USR-TEACH-AI", "teacher", "INST-AI"),
        "admin": _bearer("USR-ADMIN-AI", "institution_admin", "INST-AI"),
        "national": _bearer("USR-NAT-AI", "aicte_admin"),
        "verifier": _bearer("USR-VER-AI", "verifier"),
    }


async def _ask(client, headers, message="What is my attendance?", language="en", **extra):
    response = await client.post(
        "/api/ai/chat",
        json={"message": message, "language": language, **extra},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
async def test_anonymous_gets_guidance_and_a_sign_in_prompt(client, ai):
    data = await _ask(client, {}, "What is my attendance?")

    assert data["grounded"] is False
    assert "sign in" in data["reply"].lower()
    assert any(action["url"] == "/login" for action in data["actions"])
    assert data["data"] is None


@pytest.mark.asyncio
async def test_student_attendance_is_grounded_in_own_record(client, ai):
    data = await _ask(client, ai["student"])

    assert data["grounded"] is True
    assert data["intent"] == "attendance"
    assert data["data"]["kind"] == "attendance"
    entry = data["data"]["students"][0]
    assert entry["student_name"] == "Aarav Own"
    assert entry["total_sessions"] == 4
    assert entry["attendance_rate"] == 75.0
    assert data["citations"][0]["collection"] == "attendance_records"


@pytest.mark.asyncio
async def test_body_role_and_student_id_cannot_escalate(client, ai):
    data = await _ask(
        client,
        ai["student"],
        role="aicte_admin",
        context={"role": "aicte_admin", "student_id": "STU-OTHER", "apaar_id": "STU-OTHER"},
    )

    assert data["grounded"] is True
    entry = data["data"]["students"][0]
    assert entry["student_name"] == "Aarav Own"
    assert entry["attendance_rate"] == 75.0
    assert all(row["student_name"] != "Meera Other" for row in data["data"]["students"])


@pytest.mark.asyncio
async def test_parent_sees_only_the_verified_ward(client, ai):
    data = await _ask(client, ai["parent"])

    assert data["grounded"] is True
    names = [row["student_name"] for row in data["data"]["students"]]
    assert names == ["Aarav Own"]
    assert "Meera Other" not in names


@pytest.mark.asyncio
async def test_parent_without_a_verified_link_gets_an_honest_answer(client, ai):
    data = await _ask(client, ai["unlinked_parent"])

    assert data["grounded"] is False
    assert "not linked" in data["reply"].lower()
    assert data["data"] is None


@pytest.mark.asyncio
async def test_only_published_results_are_released(client, ai):
    data = await _ask(client, ai["student"], "Show my latest results")

    assert data["grounded"] is True
    assert data["intent"] == "results"
    payload = data["data"]["students"][0]
    assert payload["result_count"] == 1
    assert payload["results"][0]["assessment"] == "Mid-Term"
    assert payload["results"][0]["marks_obtained"] == 80.0
    assert payload["average_percentage"] == 80.0
    # The 90% mark belongs to a DRAFT assessment and must not leak.
    assert all(row["assessment"] != "Draft Quiz" for row in payload["results"])


@pytest.mark.asyncio
async def test_missing_data_is_answered_honestly(client, ai):
    db = ai["db"]
    await db["users"].insert_one(
        {
            "user_id": "USR-EMPTY",
            "email": "empty@ai.test",
            "full_name": "Empty Student",
            "role": "student",
            "apaar_id": "STU-EMPTY",
            "institution_id": "INST-AI",
            "is_active": True,
        }
    )
    await db["students"].insert_one(
        {
            "apaar_id": "STU-EMPTY",
            "student_name": "Empty Student",
            "institution_id": "INST-AI",
            "program_id": "PROG-AI",
        }
    )
    headers = _bearer("USR-EMPTY", "student", "INST-AI")

    data = await _ask(client, headers)

    assert data["grounded"] is False
    assert "could not find" in data["reply"].lower()
    assert data["data"]["students"][0]["attendance_rate"] is None


@pytest.mark.asyncio
async def test_institution_statistics_are_scoped(client, ai):
    data = await _ask(client, ai["admin"], "How many students are enrolled?")

    assert data["grounded"] is True
    assert data["intent"] == "campus_stats"
    assert data["data"]["students"] == 2
    assert data["data"]["anomalies"] == 2


@pytest.mark.asyncio
async def test_national_statistics_cover_every_institution(client, ai):
    data = await _ask(client, ai["national"], "What are the national enrollment metrics?")

    assert data["grounded"] is True
    assert data["intent"] == "national_stats"
    assert data["data"]["institutions"] >= 3
    assert data["data"]["students"] >= 3


@pytest.mark.asyncio
async def test_verifier_cannot_read_student_records(client, ai):
    data = await _ask(client, ai["verifier"])

    assert data["grounded"] is False
    assert "cannot read student records" in data["reply"].lower()


@pytest.mark.asyncio
async def test_anomalies_are_scoped_to_the_institution(client, ai):
    data = await _ask(client, ai["admin"], "How many anomalies are flagged?")

    assert data["grounded"] is True
    assert data["data"]["total"] == 2
    assert data["data"]["by_severity"]["CRITICAL"] == 1


@pytest.mark.asyncio
async def test_notices_respect_class_targeting(client, ai):
    data = await _ask(client, ai["student"], "What notices are there for me?")

    assert data["grounded"] is True
    titles = [notice["title"] for notice in data["data"]["notices"]]
    assert titles == ["Class 10-A test", "Sports day"]
    assert "Other campus" not in titles


@pytest.mark.asyncio
async def test_timetable_does_not_invent_times(client, ai):
    data = await _ask(client, ai["student"], "Show my timetable")

    assert "will not invent" in data["reply"]
    assert data["data"]["kind"] == "assignments"
    assert [row["subject"] for row in data["data"]["assignments"]] == [
        "Mathematics",
        "Science",
    ]


@pytest.mark.asyncio
async def test_id_card_masks_the_full_apaar_id(client, ai):
    data = await _ask(client, ai["student"], "Show my ID card")

    assert data["grounded"] is True
    assert data["intent"] == "id_card"
    assert data["data"]["students"][0]["apaar_masked"].startswith("****-****-")
    assert "STU-OWN" not in data["reply"]


@pytest.mark.asyncio
async def test_answers_follow_the_requested_language(client, ai):
    hindi = await _ask(client, ai["student"], language="hi")
    odia = await _ask(client, ai["student"], language="or")

    assert "उपस्थिति" in hindi["reply"]
    assert "ଉପସ୍ଥିତ" in odia["reply"]


@pytest.mark.asyncio
async def test_prompt_chips_come_from_the_authenticated_role(client, ai):
    response = await client.get("/api/ai/prompts", headers=ai["parent"])
    assert response.status_code == 200
    payload = response.json()

    assert payload["role"] == "parent"
    assert any("child" in prompt.lower() for prompt in payload["prompts"])

    anonymous = await client.get("/api/ai/prompts")
    assert anonymous.status_code == 200
    assert anonymous.json()["role"] == "student"
