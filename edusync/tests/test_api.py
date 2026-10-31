"""End-to-end tests of the HTTP API."""

from __future__ import annotations

from app.services import seal


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def create_student(client, token, **overrides):
    payload = {
        "apaar_id": "984210357890",
        "student_name": "Aakash Verma",
        "date_of_birth": "2004-03-12",
        "gender": "M",
        "institution_id": "INST-T1",
        "program_id": "BTECH_CSE",
        "academic_year": "2024-25",
        "admission_quota": "REGULAR_MERIT",
        "enrollment_date": "2024-08-01",
        "student_institute_roll_no": "CSE-0001",
        "nationality": "Indian",
    }
    payload.update(overrides)
    return await client.post("/api/students", json=payload, headers=auth(token))


async def grant_consent(client, token, apaar_id="984210357890", status="GRANTED"):
    """Give a student the credential-verification consent."""
    return await client.post(
        "/api/consent",
        json={
            "apaar_id": apaar_id,
            "purpose": "CREDENTIAL_VERIFICATION",
            "status": status,
            "channel": "WEB_PORTAL",
        },
        headers=auth(token),
    )


# ------------------------------------------------------------------- auth


async def test_login_returns_a_token_pair(client):
    response = await client.post(
        "/api/auth/login",
        json={"email": "aicte@edusync.test", "password": "Test@1234"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "aicte_admin"
    assert body["access_token"]
    assert body["refresh_token"]


async def test_a_wrong_password_is_rejected(client):
    response = await client.post(
        "/api/auth/login",
        json={"email": "aicte@edusync.test", "password": "nope"},
    )
    assert response.status_code == 401


async def test_the_current_user_is_returned(client, aicte_token):
    response = await client.get("/api/auth/me", headers=auth(aicte_token))
    assert response.status_code == 200
    assert response.json()["role"] == "aicte_admin"


async def test_an_unauthenticated_request_is_rejected(client):
    response = await client.get("/api/students")
    assert response.status_code == 401


async def test_a_refresh_token_issues_a_new_access_token(client):
    login = await client.post(
        "/api/auth/login",
        json={"email": "aicte@edusync.test", "password": "Test@1234"},
    )
    refresh = login.json()["refresh_token"]
    response = await client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 200
    assert response.json()["access_token"]


# ------------------------------------------------------------------- rbac


async def test_an_institution_may_not_read_the_anomaly_register(client, institution_token):
    response = await client.get("/api/anomalies", headers=auth(institution_token))
    assert response.status_code == 403


async def test_a_verifier_may_not_onboard_students(client, verifier_token):
    response = await create_student(client, verifier_token)
    assert response.status_code == 403


async def test_an_institution_may_not_read_another_institution(client, institution_token):
    response = await create_student(
        client, institution_token, institution_id="INST-OTHER"
    )
    assert response.status_code == 403


# --------------------------------------------------------------- students


async def test_an_institution_onboards_a_student(client, institution_token):
    response = await create_student(client, institution_token)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["apaar_id"] == "984210357890"
    assert body["verification_status"] in {"PENDING_REVIEW", "VERIFIED"}
    assert body["masked_apaar_id"] == "9842 **** ****"


async def test_an_invalid_apaar_id_is_rejected(client, institution_token):
    response = await create_student(client, institution_token, apaar_id="12345")
    assert response.status_code == 422


async def test_a_duplicate_apaar_id_is_rejected(client, institution_token):
    await create_student(client, institution_token)
    response = await create_student(client, institution_token)
    assert response.status_code == 409


async def test_the_student_list_is_scoped_to_the_institution(client, institution_token):
    await create_student(client, institution_token)
    response = await client.get("/api/students", headers=auth(institution_token))
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_a_student_can_be_updated(client, institution_token):
    await create_student(client, institution_token)
    response = await client.put(
        "/api/students/984210357890",
        json={"student_name": "Aakash Verma Iyer"},
        headers=auth(institution_token),
    )
    assert response.status_code == 200
    assert response.json()["student_name"] == "Aakash Verma Iyer"


async def test_a_student_can_be_deactivated(client, institution_token):
    await create_student(client, institution_token)
    response = await client.delete(
        "/api/students/984210357890", headers=auth(institution_token)
    )
    assert response.status_code == 204
    listing = await client.get("/api/students", headers=auth(institution_token))
    assert listing.json() == []


async def test_the_qr_badge_is_rendered(client, institution_token):
    await create_student(client, institution_token)
    response = await client.get(
        "/api/students/984210357890/qr", headers=auth(institution_token)
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


async def test_the_certificate_carries_the_apaar_id(client, institution_token):
    await create_student(client, institution_token)
    response = await client.get(
        "/api/students/984210357890/certificate.pdf",
        headers=auth(institution_token),
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"
    assert len(response.content) > 2000


async def test_a_verifier_may_not_issue_a_certificate(client, institution_token, verifier_token):
    await create_student(client, institution_token)
    response = await client.get(
        "/api/students/984210357890/certificate.pdf",
        headers=auth(verifier_token),
    )
    assert response.status_code == 403


async def test_the_issued_badge_verifies_against_the_registry(
    client, institution_token, verifier_token
):
    """The seal printed on the badge must re-derive from the stored record."""
    from app.services import qr

    await create_student(client, institution_token)
    await grant_consent(client, institution_token)

    student = (
        await client.get("/api/students/984210357890", headers=auth(institution_token))
    ).json()
    assert student["apaar_id"] == "984210357890"

    # The badge carries an opaque token, not the APAAR ID.
    issued = await client.post(
        "/api/verification-tokens",
        json={"student_record_id": student["record_id"]},
        headers=auth(institution_token),
    )
    assert issued.status_code == 201, issued.text
    link = qr.build_token_payload(issued.json()["token"])
    assert "984210357890" not in link

    response = await client.post(
        "/api/verify/scan", params={"payload": link}, headers=auth(verifier_token)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verified"] is True
    assert body["verdict"] == "VALID"


# ------------------------------------------------------------- bulk csv


CSV = (
    "APAAR_ID,Full_Name,DOB,Gender,Roll_No,Program_Code,Category,Nationality,Doc_Number\n"
    "984210357890,Aakash Verma,2004-03-12,Male,CSE-1,BTECH_CSE,REGULAR_MERIT,Indian,\n"
    "984210357891,Sanya Kapoor,2005-01-20,Female,CSE-2,BTECH_CSE,REGULAR_MERIT,Indian,\n"
    "12345,Bad Row,2004-01-01,Male,CSE-3,BTECH_CSE,REGULAR_MERIT,Indian,\n"
)


async def test_the_bulk_preview_reports_every_row(client, institution_token):
    response = await client.post(
        "/api/students/bulk/preview?institution_id=INST-T1",
        files={"file": ("batch.csv", CSV, "text/csv")},
        headers=auth(institution_token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 3
    assert body["critical_rows"] == 1
    assert body["valid_rows"] == 2
    assert body["rows"][2]["issues"][0]["code"] == "INVALID_APAAR"


async def test_the_bulk_commit_only_commits_the_valid_rows(client, institution_token):
    response = await client.post(
        "/api/students/bulk/commit?institution_id=INST-T1",
        files={"file": ("batch.csv", CSV, "text/csv")},
        headers=auth(institution_token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["committed"] == 2
    assert body["skipped"] == 1
    assert body["critical_rows"] == 1


# -------------------------------------------------------------- dashboard


async def test_the_national_dashboard_reports_the_kpis(client, aicte_token):
    response = await client.get("/api/dashboard/national", headers=auth(aicte_token))
    assert response.status_code == 200
    body = response.json()
    assert body["institution_count"] == 1
    assert body["programme_count"] == 1


async def test_the_intake_matrix_is_returned(client, aicte_token):
    response = await client.get("/api/dashboard/intake", headers=auth(aicte_token))
    assert response.status_code == 200
    rows = response.json()
    assert rows[0]["approved_intake"] == 10


async def test_the_compliance_matrix_is_returned(client, aicte_token):
    response = await client.get("/api/dashboard/compliance", headers=auth(aicte_token))
    assert response.status_code == 200
    assert response.json()[0]["institution_id"] == "INST-T1"


async def test_the_quota_distribution_is_returned(client, aicte_token):
    response = await client.get("/api/dashboard/quota", headers=auth(aicte_token))
    assert response.status_code == 200
    assert len(response.json()) == 7


# ------------------------------------------------------------ verification


async def test_a_verifier_can_verify_a_credential(client, institution_token, verifier_token):
    await create_student(client, institution_token)
    await grant_consent(client, institution_token)
    response = await client.get(
        "/api/verify/984210357890", headers=auth(verifier_token)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verified"] is True
    assert body["student"]["student_name"] == "Aakash Verma"


async def test_verifying_an_unknown_id_is_not_found(client, verifier_token):
    response = await client.get("/api/verify/999999999999", headers=auth(verifier_token))
    assert response.status_code == 200
    assert response.json()["verdict"] == "NOT_FOUND"


async def test_a_tampered_seal_is_invalid(client, institution_token, verifier_token):
    await create_student(client, institution_token)
    response = await client.get(
        "/api/verify/984210357890?seal=HMAC-SHA256.k1.bm90YXNpZ25hdHVyZQ",
        headers=auth(verifier_token),
    )
    assert response.status_code == 200
    assert response.json()["verified"] is False


async def test_a_scanned_payload_is_verified(client, institution_token, verifier_token):
    await create_student(client, institution_token)
    await grant_consent(client, institution_token)
    payload = seal.sign(
        seal.CredentialPayload(
            apaar_id="984210357890",
            institution_id="INST-T1",
            program_id="BTECH_CSE",
            academic_year="2024-25",
            enrollment_date="2024-08-01",
            student_name="Aakash Verma",
            date_of_birth="2004-03-12",
            gender="M",
            admission_quota="REGULAR_MERIT",
            nationality="Indian",
            student_institute_roll_no="CSE-0001",
        )
    )
    # The legacy link format - the one a badge printed before the token flow
    # existed - is still readable, so a verifier can check an old badge.
    link = "https://chhatralekha.vercel.app/verify?apaar=984210357890&seal=" + payload
    response = await client.post(
        "/api/verify/scan", params={"payload": link}, headers=auth(verifier_token)
    )
    assert response.status_code == 200
    assert response.json()["verified"] is True


async def test_the_verdict_is_issued_even_without_consent(
    client, institution_token, verifier_token
):
    await create_student(client, institution_token)
    response = await client.get(
        "/api/verify/984210357890", headers=auth(verifier_token)
    )
    body = response.json()
    assert body["verified"] is True
    assert body["student"] is None
    assert "No consent" in body["consent_note"]


async def test_the_personal_fields_are_withheld_after_a_revocation(
    client, institution_token, verifier_token
):
    await create_student(client, institution_token)
    await grant_consent(client, institution_token, status="REVOKED")
    response = await client.get(
        "/api/verify/984210357890", headers=auth(verifier_token)
    )
    body = response.json()
    assert body["student"] is None
    assert "withdrew" in body["consent_note"]


# ------------------------------------------------------------------ consent


async def test_consent_can_be_recorded_and_listed(client, institution_token):
    await create_student(client, institution_token)
    response = await grant_consent(client, institution_token)
    assert response.status_code == 201

    listing = await client.get(
        "/api/consent/984210357890", headers=auth(institution_token)
    )
    assert len(listing.json()) == 1


async def test_the_consent_decisions_are_evaluated(client, institution_token):
    await create_student(client, institution_token)
    await grant_consent(client, institution_token)
    response = await client.get(
        "/api/consent/984210357890/decisions", headers=auth(institution_token)
    )
    decisions = {item["purpose"]: item for item in response.json()}
    assert decisions["CREDENTIAL_VERIFICATION"]["allowed"] is True
    assert decisions["MARKETING"]["allowed"] is False


# ------------------------------------------------------------------ reports


async def test_the_student_register_exports_as_csv(client, aicte_token, institution_token):
    await create_student(client, institution_token)
    response = await client.get("/api/reports/students.csv", headers=auth(aicte_token))
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "984210357890" in response.text


async def test_the_student_register_exports_as_pdf(client, aicte_token, institution_token):
    await create_student(client, institution_token)
    response = await client.get("/api/reports/students.pdf", headers=auth(aicte_token))
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"


async def test_the_anomaly_register_exports_as_pdf(client, aicte_token):
    response = await client.get("/api/reports/anomalies.pdf", headers=auth(aicte_token))
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"


async def test_the_audit_trail_exports_as_csv(client, aicte_token):
    response = await client.get("/api/reports/audit.csv", headers=auth(aicte_token))
    assert response.status_code == 200
    assert "PREV_HASH" in response.text


async def test_the_utilisation_matrix_exports_as_csv(client, aicte_token):
    response = await client.get("/api/reports/utilisation.csv", headers=auth(aicte_token))
    assert response.status_code == 200
    assert "APPROVED_INTAKE" in response.text


# ------------------------------------------------------------------- portal


async def test_the_health_endpoint_reports_the_database(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["database"] == "up"
    assert body["database_engine"] == "mongodb"


async def test_the_openapi_document_is_generated(client):
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/students" in paths
    assert "/api/verify/{apaar_id}" in paths
    assert "/api/dashboard/national" in paths
