"""End-to-end tests of the correction workflow and the impact API."""

from __future__ import annotations

from app.core.database import mongo
from app.services import audit_chain


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def create_student(client, token, **overrides):
    payload = {
        "apaar_id": "984210357890",
        "student_name": "Rahul Kumar",
        "date_of_birth": "2004-03-12",
        "gender": "M",
        "institution_id": "INST-T1",
        "program_id": "BTECH_CSE",
        "academic_year": "2024-25",
        "admission_quota": "REGULAR_MERIT",
        "enrollment_date": "2024-07-01",
        "student_institute_roll_no": "CSE-0001",
        "nationality": "Indian",
    }
    payload.update(overrides)
    return await client.post("/api/students", json=payload, headers=auth(token))


async def snapshot_collections():
    """A snapshot of every collection, for the no-mutation assertions."""
    db = mongo.db()
    snapshot = {}
    for name in await db.list_collection_names():
        snapshot[name] = len(await db[name].find({}).to_list(length=None))
    return snapshot


# ------------------------------------------------------------- the preview


async def test_the_preview_writes_nothing(client, institution_token):
    created = await create_student(client, institution_token)
    assert created.status_code == 201, created.text
    record_id = created.json()["record_id"]

    before = await snapshot_collections()
    response = await client.post(
        f"/api/students/{record_id}/correction-preview",
        json={"changes": {"academic_year": "2025-26"}},
        headers=auth(institution_token),
    )
    after = await snapshot_collections()

    assert response.status_code == 200
    assert response.json()["preview"] is True
    assert before == after, "the preview must not write to any collection"


async def test_the_preview_reports_the_before_and_after(client, institution_token):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]
    response = await client.post(
        f"/api/students/{record_id}/correction-preview",
        json={"changes": {"academic_year": "2025-26"}},
        headers=auth(institution_token),
    )
    body = response.json()
    change = next(item for item in body["changed_fields"] if item["field"] == "academic_year")
    assert change["before"] == "2024-25"
    assert change["after"] == "2025-26"
    assert body["current_version"] == 1


async def test_a_harmless_correction_produces_no_task(client, institution_token):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]
    response = await client.post(
        f"/api/students/{record_id}/correction-preview",
        json={"changes": {"contact_email": "new@example.in"}},
        headers=auth(institution_token),
    )
    body = response.json()
    assert body["findings"] == []
    assert body["checklist"] == []


async def test_the_preview_of_a_missing_record_is_a_404(client, institution_token):
    response = await client.post(
        "/api/students/000000000000000000000000/correction-preview",
        json={"changes": {"academic_year": "2025-26"}},
        headers=auth(institution_token),
    )
    assert response.status_code == 404


async def test_the_preview_rejects_an_unknown_field(client, institution_token):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]
    response = await client.post(
        f"/api/students/{record_id}/correction-preview",
        json={"changes": {"is_active": False}},
        headers=auth(institution_token),
    )
    assert response.status_code == 422


# ---------------------------------------------------------------- the apply


async def test_a_correction_is_applied_and_the_version_is_kept(client, institution_token):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]

    response = await client.post(
        f"/api/students/{record_id}/corrections",
        json={
            "changes": {"academic_year": "2025-26"},
            "reason": "The admission was made in the 2025-26 session.",
            "expected_version": 1,
        },
        headers=auth(institution_token),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["applied"] is True
    assert body["version_no"] == 2

    # The record now carries the new value and the new version.
    record = await client.get("/api/students/984210357890", headers=auth(institution_token))
    assert record.json()["academic_year"] == "2025-26"

    # The previous version is preserved.
    versions = await client.get(
        f"/api/students/{record_id}/versions", headers=auth(institution_token)
    )
    assert versions.status_code == 200
    assert len(versions.json()) == 1
    assert versions.json()[0]["version_no"] == 2
    assert versions.json()[0]["previous_values"]["academic_year"] == "2024-25"
    assert versions.json()[0]["reason"] == "The admission was made in the 2025-26 session."


async def test_a_stale_expected_version_is_refused(client, institution_token):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]

    first = await client.post(
        f"/api/students/{record_id}/corrections",
        json={
            "changes": {"academic_year": "2025-26"},
            "reason": "first correction",
            "expected_version": 1,
        },
        headers=auth(institution_token),
    )
    assert first.status_code == 200

    second = await client.post(
        f"/api/students/{record_id}/corrections",
        json={
            "changes": {"academic_year": "2026-27"},
            "reason": "second correction, based on a stale preview",
            "expected_version": 1,
        },
        headers=auth(institution_token),
    )
    assert second.status_code == 409
    assert "changed since the preview" in second.json()["detail"]


async def test_a_correction_needs_a_reason(client, institution_token):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]
    response = await client.post(
        f"/api/students/{record_id}/corrections",
        json={"changes": {"academic_year": "2025-26"}, "reason": "  ", "expected_version": 1},
        headers=auth(institution_token),
    )
    assert response.status_code == 422


async def test_a_correction_creates_the_review_checklist(client, institution_token):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]
    response = await client.post(
        f"/api/students/{record_id}/corrections",
        json={
            "changes": {"academic_year": "2025-26"},
            "reason": "the admission was made in the 2025-26 session",
            "expected_version": 1,
        },
        headers=auth(institution_token),
    )
    assert response.json()["tasks_created"] >= 1

    tasks = await client.get("/api/review-tasks", headers=auth(institution_token))
    assert tasks.status_code == 200
    assert len(tasks.json()) >= 1
    assert tasks.json()[0]["rule_id"].startswith("CIA-")
    assert tasks.json()[0]["status"] == "open"


async def test_a_correction_never_modifies_a_linked_record(client, institution_token):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]
    linked = await create_student(
        client,
        institution_token,
        apaar_id="984210357891",
        student_name="Rahul K.",
        student_institute_roll_no="CSE-0002",
    )
    assert linked.status_code == 201

    await client.post(
        f"/api/students/{record_id}/corrections",
        json={
            "changes": {"academic_year": "2025-26"},
            "reason": "the admission was made in the 2025-26 session",
            "expected_version": 1,
        },
        headers=auth(institution_token),
    )

    untouched = await client.get(
        "/api/students/984210357891", headers=auth(institution_token)
    )
    assert untouched.json()["academic_year"] == "2024-25"
    assert untouched.json()["student_name"] == "Rahul K."


async def test_the_audit_chain_still_verifies_after_a_correction(client, institution_token):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]
    await client.post(
        f"/api/students/{record_id}/corrections",
        json={
            "changes": {"academic_year": "2025-26"},
            "reason": "the admission was made in the 2025-26 session",
            "expected_version": 1,
        },
        headers=auth(institution_token),
    )

    db = mongo.db()
    entries = await db["audit_events"].find({}).sort("_id", 1).to_list(length=None)
    assert entries
    assert audit_chain.verify(entries)
    assert audit_chain.first_break(entries) is None

    actions = [entry.get("action") for entry in entries]
    assert "APPLY_CORRECTION" in actions


# ------------------------------------------------------------- the checklist


async def test_the_task_lifecycle_moves_from_open_to_resolved(
    client, institution_token
):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]
    await client.post(
        f"/api/students/{record_id}/corrections",
        json={
            "changes": {"academic_year": "2025-26"},
            "reason": "the admission was made in the 2025-26 session",
            "expected_version": 1,
        },
        headers=auth(institution_token),
    )
    tasks = (await client.get("/api/review-tasks", headers=auth(institution_token))).json()
    task_id = tasks[0]["task_id"]

    started = await client.patch(
        f"/api/review-tasks/{task_id}",
        json={"status": "in_progress", "review_note": "Taken up."},
        headers=auth(institution_token),
    )
    assert started.status_code == 200
    assert started.json()["status"] == "in_progress"

    resolved = await client.patch(
        f"/api/review-tasks/{task_id}",
        json={
            "status": "resolved",
            "review_note": "Checked against the source documents.",
            "outcome": "No further action needed.",
        },
        headers=auth(institution_token),
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["reviewer"]


async def test_a_dismissal_has_to_record_a_reason(client, institution_token):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]
    await client.post(
        f"/api/students/{record_id}/corrections",
        json={
            "changes": {"academic_year": "2025-26"},
            "reason": "the admission was made in the 2025-26 session",
            "expected_version": 1,
        },
        headers=auth(institution_token),
    )
    tasks = (await client.get("/api/review-tasks", headers=auth(institution_token))).json()
    task_id = tasks[0]["task_id"]

    refused = await client.patch(
        f"/api/review-tasks/{task_id}",
        json={"status": "dismissed", "review_note": ""},
        headers=auth(institution_token),
    )
    assert refused.status_code == 422

    accepted = await client.patch(
        f"/api/review-tasks/{task_id}",
        json={"status": "dismissed", "review_note": "The difference is explained."},
        headers=auth(institution_token),
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "dismissed"


async def test_the_impacts_endpoint_lists_the_assessments(client, institution_token):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]
    applied = await client.post(
        f"/api/students/{record_id}/corrections",
        json={
            "changes": {"academic_year": "2025-26"},
            "reason": "the admission was made in the 2025-26 session",
            "expected_version": 1,
        },
        headers=auth(institution_token),
    )
    assessment_id = applied.json()["assessment_id"]

    impacts = await client.get("/api/impacts", headers=auth(institution_token))
    assert impacts.status_code == 200
    assert any(item["assessment_id"] == assessment_id for item in impacts.json())

    detail = await client.get(
        f"/api/impacts/{assessment_id}", headers=auth(institution_token)
    )
    assert detail.status_code == 200
    assert "assessment" in detail.json()
    assert "tasks" in detail.json()


# ------------------------------------------------------------------- rbac


async def test_a_verifier_cannot_preview_a_correction(client, institution_token, verifier_token):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]
    response = await client.post(
        f"/api/students/{record_id}/correction-preview",
        json={"changes": {"academic_year": "2025-26"}},
        headers=auth(verifier_token),
    )
    assert response.status_code == 403


async def test_a_verifier_cannot_apply_a_correction(client, institution_token, verifier_token):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]
    response = await client.post(
        f"/api/students/{record_id}/corrections",
        json={
            "changes": {"academic_year": "2025-26"},
            "reason": "not allowed",
            "expected_version": 1,
        },
        headers=auth(verifier_token),
    )
    assert response.status_code == 403


async def test_a_verifier_cannot_review_a_task(client, institution_token, verifier_token):
    response = await client.get("/api/review-tasks", headers=auth(verifier_token))
    assert response.status_code == 403


async def test_an_institution_cannot_correct_another_institution(
    client, institution_token
):
    db = mongo.db()
    await db["institutions"].insert_one(
        {
            "institution_id": "INST-OTHER",
            "name": "Another Institute",
            "institution_type": "ENGINEERING",
            "state": "Kerala",
            "city": "Kochi",
            "affiliation_university": "Test",
            "approval_year": 2015,
            "naac_grade": "A",
            "is_active": True,
        }
    )
    await db["students"].insert_one(
        {
            "apaar_id": "984210357899",
            "student_name": "Someone Else",
            "date_of_birth": "2004-03-12",
            "gender": "M",
            "institution_id": "INST-OTHER",
            "program_id": "BTECH_CSE",
            "academic_year": "2024-25",
            "admission_quota": "REGULAR_MERIT",
            "enrollment_date": "2024-07-01",
            "student_institute_roll_no": "CSE-0009",
            "nationality": "Indian",
            "record_status": "ACTIVE",
            "is_active": True,
            "version": 1,
        }
    )
    other = await db["students"].find_one({"apaar_id": "984210357899"})
    response = await client.post(
        f"/api/students/{other['_id']}/correction-preview",
        json={"changes": {"academic_year": "2025-26"}},
        headers=auth(institution_token),
    )
    assert response.status_code == 403
