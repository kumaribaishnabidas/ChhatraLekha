"""Seed the EduSynC registry with a synthetic pan-India dataset.

The dataset is **entirely synthetic**: no real student, institution or APAAR
identifier is used. It is designed to exercise every detection layer so the
demo can show the platform catching real problems:

* a cross-institution duplicate APAAR ID,
* a same-institution duplicate,
* a duplicate institute roll number,
* a malformed APAAR ID,
* a foreign-national seat held by an Indian citizen,
* an over-admitted programme,
* an unsanctioned programme code,
* an impossible date and a missing mandatory field.

Usage::

    python -m app.scripts.seed            # the full demo dataset
    python -m app.scripts.seed --students 400
"""

from __future__ import annotations

import argparse
import asyncio
import random
import secrets
from datetime import date, timedelta
from typing import Any

from app.core.config import get_settings
from app.core.security import generate_api_key, hash_password
from app.models.documents import match_token
from app.models.enums import (
    AdmissionQuota,
    Gender,
    InstitutionType,
    SocialCategory,
)
from app.services.registry import recompute_anomalies

settings = get_settings()

# ------------------------------------------------------------------ fixtures

INSTITUTIONS = [
    ("INST-0421", "Vidya Vikas Institute of Technology", InstitutionType.ENGINEERING, "Karnataka", "Bengaluru", "Visvesvaraya Technological University", 2012, "A++"),
    ("INST-0422", "Bharatiya Vidya Mandir College of Engineering", InstitutionType.ENGINEERING, "Maharashtra", "Pune", "Savitribai Phule Pune University", 2009, "A+"),
    ("INST-0423", "Deccan Institute of Engineering & Technology", InstitutionType.ENGINEERING, "Telangana", "Hyderabad", "Osmania University", 2015, "A"),
    ("INST-0424", "Karnataka Institute of Management Studies", InstitutionType.MANAGEMENT, "Karnataka", "Mysuru", "University of Mysore", 2010, "A+"),
    ("INST-0425", "Gujarat Polytechnic of Engineering", InstitutionType.POLYTECHNIC, "Gujarat", "Ahmedabad", "Gujarat Technological University", 2014, "A"),
    ("INST-0426", "Tamil Nadu Institute of Technology", InstitutionType.ENGINEERING, "Tamil Nadu", "Coimbatore", "Anna University", 2008, "A++"),
    ("INST-0427", "Rajasthan Technical Institute", InstitutionType.ENGINEERING, "Rajasthan", "Jaipur", "Rajasthan Technical University", 2013, "A"),
    ("INST-0428", "Punjab Institute of Technology", InstitutionType.ENGINEERING, "Punjab", "Ludhiana", "Panjab University", 2016, "A+"),
    ("INST-0429", "Odisha Engineering College", InstitutionType.ENGINEERING, "Odisha", "Bhubaneswar", "KIIT University", 2011, "A++"),
    ("INST-0430", "Kerala Institute of Management", InstitutionType.MANAGEMENT, "Kerala", "Thiruvananthapuram", "University of Kerala", 2017, "A"),
    ("INST-0431", "Madhya Pradesh Polytechnic", InstitutionType.POLYTECHNIC, "Madhya Pradesh", "Indore", "Rajiv Gandhi Proudyogiki Vishwavidyalaya", 2018, "A"),
    ("INST-0432", "Assam Institute of Technology", InstitutionType.ENGINEERING, "Assam", "Guwahati", "Gauhati University", 2019, "A"),
]

PROGRAMMES = [
    ("BTECH_CSE", "B.Tech Computer Science & Engineering", "UG", 120, 6, 18, 6, 12),
    ("BTECH_ECE", "B.Tech Electronics & Communication", "UG", 60, 3, 9, 3, 6),
    ("BTECH_MECH", "B.Tech Mechanical Engineering", "UG", 60, 3, 9, 3, 6),
    ("BTECH_CIVIL", "B.Tech Civil Engineering", "UG", 60, 3, 9, 3, 6),
    ("BTECH_AIML", "B.Tech Artificial Intelligence & Machine Learning", "UG", 60, 3, 9, 3, 6),
    ("MCA", "Master of Computer Applications", "PG", 60, 3, 9, 3, 6),
    ("MBA", "Master of Business Administration", "PG", 120, 6, 18, 6, 0),
    ("DIPLOMA_CSE", "Diploma in Computer Science & Engineering", "DIPLOMA", 60, 0, 0, 0, 0),
    ("DIPLOMA_MECH", "Diploma in Mechanical Engineering", "DIPLOMA", 60, 0, 0, 0, 0),
    ("BBA", "Bachelor of Business Administration", "UG", 60, 0, 0, 0, 0),
]

FIRST_NAMES = [
    "Aakash", "Sanya", "Rehan", "Mei", "Aarav", "Diya", "Vihaan", "Ananya", "Kabir",
    "Ishita", "Rohan", "Priya", "Arjun", "Sneha", "Karthik", "Divya", "Aditya", "Nandini",
    "Farhan", "Kavya", "Nikhil", "Riya", "Varun", "Pooja", "Manish", "Aarti", "Siddharth",
    "Meghana", "Harsh", "Nisha", "Gaurav", "Shruti", "Imran", "Lakshmi", "Tarun",
    "Yash", "Swati", "Rajesh", "Bhavana", "Sameer", "Geeta", "Amit", "Kiran", "Sunil",
    "Preeti", "Naveen", "Tanvi", "Deepak", "Shalini", "Ramesh",
]

LAST_NAMES = [
    "Verma", "Kapoor", "Qureshi", "Chow", "Iyer", "Nair", "Singh", "Patel", "Reddy",
    "Menon", "Bose", "Gupta", "Joshi", "Desai", "Chauhan", "Rao", "Das", "Mehta",
    "Shetty", "Banerjee", "Pillai", "Yadav", "Kulkarni", "Sharma", "Malhotra",
]

STATES = [
    "Karnataka", "Maharashtra", "Tamil Nadu", "Delhi", "Uttar Pradesh", "West Bengal",
    "Gujarat", "Rajasthan", "Kerala", "Punjab", "Odisha", "Assam", "Bihar", "Madhya Pradesh",
]

DEMO_USERS = [
    ("aicte.admin@edusync.gov.in", "Dr. Ananya Iyer", "aicte_admin", None),
    ("principal@vidyavikas.edu.in", "Prof. Ramesh Kulkarni", "institution_admin", "INST-0421"),
    ("principal@bhartiya.edu.in", "Prof. Sunil Mehta", "institution_admin", "INST-0422"),
    ("verifier@acme-corp.com", "Maya Krishnan", "verifier", None),
    ("student@vidyavikas.edu.in", "Aakash Verma", "student", None),
]

#: The published AICTE Approval Process Handbook ceilings, stored as a
#: versioned policy document rather than hard-coded in the engine.
DEFAULT_POLICY_RULE = {
    "policy_id": "aph-2024-01",
    "version": "2024-01",
    "active": True,
    "effective_from": "2024-06-01",
    "description": (
        "The AICTE Approval Process Handbook ceilings: NRI 5% of the sanctioned "
        "intake, OCI and foreign nationals 15% together, tuition fee waiver 5%, and "
        "a per-programme PMSSS cap."
    ),
    "seats": {
        "NRI": {"rule": "percentage_of_approved_intake", "value": 5},
        "FN_OCI": {"rule": "percentage_of_approved_intake", "value": 15},
        "TFW": {"rule": "percentage_of_approved_intake", "value": 5},
        "PMSSS": {"rule": "absolute_per_programme", "value": 6},
    },
    "supported_categories": ["NRI", "FN_OCI", "TFW", "PMSSS"],
}


def _demo_password() -> str:
    """The password of the seeded demo accounts.

    It is read from ``DEMO_PASSWORD``. When that is not set, a password is
    generated and printed **once** - it is never stored in the repository and
    never written to a log.
    """
    configured = settings.demo_password.strip()
    if configured:
        return configured
    return secrets.token_urlsafe(12)


def _apaar_id(rng: random.Random) -> str:
    """A plausible, non-trivial 12-digit APAAR identifier."""
    while True:
        digits = "".join(str(rng.randint(0, 9)) for _ in range(12))
        if digits[0] == "0":
            continue
        if len(set(digits)) == 1:
            continue
        if all(int(digits[i + 1]) - int(digits[i]) == 1 for i in range(11)):
            continue
        if all(int(digits[i + 1]) - int(digits[i]) == -1 for i in range(11)):
            continue
        return digits


def _dob(rng: random.Random) -> str:
    year = rng.randint(2003, 2007)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}"


def _collection(db, name: str):
    return db[name]


async def seed(student_count: int = 2219, reset: bool = True) -> dict:
    """Populate the registry with the synthetic demo dataset."""
    from app.core.database import mongo

    rng = random.Random(20240815)

    await mongo.connect()
    db = mongo.db()

    if reset:
        for name in (
            "anomalies",
            "audit_events",
            "consents",
            "students",
            "programmes",
            "institutions",
            "users",
            "api_keys",
            "revoked_credentials",
            "submissions",
            "policy_rules",
            "record_versions",
            "impact_assessments",
            "review_tasks",
            "verification_tokens",
            "operation_status",
        ):
            await db[name].delete_many({})

    # --------------------------------------------------------- institutions
    institutions: list[dict[str, Any]] = []
    for row in INSTITUTIONS:
        institutions.append(
            {
                "institution_id": row[0],
                "name": row[1],
                "institution_type": row[2].value,
                "state": row[3],
                "city": row[4],
                "affiliation_university": row[5],
                "approval_year": row[6],
                "naac_grade": row[7],
                "email": f"principal@{row[0].lower()}.edu.in",
                "phone": f"+91 9{rng.randint(100000000, 999999999)}",
                "is_active": True,
            }
        )
    if institutions:
        await db["institutions"].insert_many(institutions)

    # ------------------------------------------------------------ programmes
    # Every institution offers a handful of programmes, so the compliance
    # matrix has something to compare.
    slots: list[tuple[dict[str, Any], tuple]] = []
    for index, institution in enumerate(institutions):
        for offset in range(5):
            slots.append((institution, PROGRAMMES[(index + offset) % len(PROGRAMMES)]))

    def _def_sanctioned(row) -> int:
        return row[3] + row[4] + row[5] + row[6] + row[7]

    base_total = sum(_def_sanctioned(row) for _, row in slots)
    scale = max(student_count, 1) / 0.92 / max(base_total, 1)

    programmes: list[dict[str, Any]] = []
    for institution, row in slots:
        approved = max(int(row[3] * scale), 5)
        nri = max(int(row[4] * scale), 0)
        oci_fn = max(int(row[5] * scale), 0)
        tfw = max(int(row[6] * scale), 0)
        pmsss = max(int(row[7] * scale), 0)
        programmes.append(
            {
                "institution_id": institution["institution_id"],
                "program_id": row[0],
                "program_name": row[1],
                "program_level": row[2],
                "academic_year": "2024-25",
                "policy_version": "aph-2024-01",
                "approved_intake": approved,
                "max_supernumerary_nri": nri,
                "max_supernumerary_fn_oci": oci_fn,
                "max_supernumerary_tfw": tfw,
                "max_pmsss": pmsss,
                "total_sanctioned": approved + nri + oci_fn + tfw + pmsss,
            }
        )
    if programmes:
        await db["programmes"].insert_many(programmes)

    # ------------------------------------------------------------- students
    students: list[dict[str, Any]] = []
    used_apaar: set[str] = set()

    def _new_apaar() -> str:
        while True:
            candidate = _apaar_id(rng)
            if candidate not in used_apaar:
                used_apaar.add(candidate)
                return candidate

    def _add(programme: dict[str, Any], quota: AdmissionQuota) -> None:
        nationality = "Indian"
        passport = None
        visa = None
        country = None
        if quota == AdmissionQuota.OCI:
            nationality = "OCI"
        elif quota == AdmissionQuota.FN:
            nationality = rng.choice(["China", "Nepal", "Bangladesh", "UAE"])
            passport = f"P{rng.randint(1000000, 9999999)}"
            visa = "2027-12-31"
            country = nationality
        enrolled = date(2024, 6, 1) + timedelta(days=rng.randint(0, 90))
        apaar_id = _new_apaar()
        students.append(
            {
                "apaar_id": apaar_id,
                "apaar_id_hmac": match_token(apaar_id),
                "student_name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                "date_of_birth": _dob(rng),
                "gender": rng.choices(
                    [Gender.MALE.value, Gender.FEMALE.value, Gender.OTHER.value],
                    weights=[48, 48, 4],
                )[0],
                "institution_id": programme["institution_id"],
                "program_id": programme["program_id"],
                "academic_year": "2024-25",
                "admission_quota": quota.value,
                "enrollment_date": enrolled.isoformat(),
                "student_institute_roll_no": (
                    f"{programme['program_id'][:3]}-{rng.randint(1, 99999):05d}"
                ),
                "nationality": nationality,
                "passport_number": passport,
                "visa_validity": visa,
                "country_of_origin": country,
                "social_category": rng.choices(
                    [
                        SocialCategory.GENERAL.value,
                        SocialCategory.OBC.value,
                        SocialCategory.SC.value,
                        SocialCategory.ST.value,
                        SocialCategory.EWS.value,
                    ],
                    weights=[50, 28, 12, 7, 3],
                )[0],
                "admission_date": enrolled.isoformat(),
                "contact_email": f"student{len(students) + 1}@example.in",
                "contact_phone": f"+91 9{rng.randint(100000000, 999999999)}",
                "state_of_domicile": rng.choice(STATES),
                "verification_status": "PENDING_REVIEW",
                "is_active": True,
                "record_status": "ACTIVE",
                "submission_source": "SEED",
            }
        )

    # Two programmes are deliberately over-admitted so that the dashboard shows
    # a live breach; every other programme sits inside its caps.
    breach_slots = {0, len(programmes) // 3}
    for slot_index, programme in enumerate(programmes):
        fill = 1.06 if slot_index in breach_slots else rng.uniform(0.86, 0.95)

        regular_target = int(round(programme["approved_intake"] * fill))
        # The regular seats are split into merit, management and PMSSS. PMSSS is
        # capped per course by the AICTE Approval Process Handbook.
        pmsss = min(max(programme["max_pmsss"], 0), int(regular_target * 0.15))
        remaining = regular_target - pmsss
        management = int(remaining * 0.25)
        merit = remaining - management

        for _ in range(merit):
            _add(programme, AdmissionQuota.MERIT)
        for _ in range(management):
            _add(programme, AdmissionQuota.MANAGEMENT)
        for _ in range(pmsss):
            _add(programme, AdmissionQuota.PMSSS)

        super_budget = (
            programme["max_supernumerary_nri"]
            + programme["max_supernumerary_fn_oci"]
            + programme["max_supernumerary_tfw"]
        )
        super_target = int(round(super_budget * 0.85))
        nri = min(programme["max_supernumerary_nri"], int(super_target * 0.40))
        oci = min(programme["max_supernumerary_fn_oci"], int(super_target * 0.20))
        foreign = min(
            programme["max_supernumerary_fn_oci"] - oci, int(super_target * 0.10)
        )
        tfw = min(
            programme["max_supernumerary_tfw"], max(super_target - nri - oci - foreign, 0)
        )
        for _ in range(nri):
            _add(programme, AdmissionQuota.NRI)
        for _ in range(oci):
            _add(programme, AdmissionQuota.OCI)
        for _ in range(foreign):
            _add(programme, AdmissionQuota.FN)
        for _ in range(tfw):
            _add(programme, AdmissionQuota.TFW)

    # --------------------------------------- deliberately planted demo anomalies
    first_programme = programmes[0]
    second_institution = institutions[1]
    second_programme = next(
        programme
        for programme in programmes
        if programme["institution_id"] == second_institution["institution_id"]
    )
    same_institution = [
        student
        for student in students
        if student["institution_id"] == first_programme["institution_id"]
    ][:2]

    # 1. cross-institution duplicate
    students.append(
        {
            **students[0],
            "institution_id": second_programme["institution_id"],
            "program_id": second_programme["program_id"],
            "student_institute_roll_no": f"XDU-{rng.randint(1, 99999):05d}",
        }
    )

    # 2. same-institution duplicate
    students.append({**students[1]})

    # 3. duplicate institute roll number (two different students)
    if len(same_institution) == 2:
        same_institution[0]["student_institute_roll_no"] = "DUP-00001"
        same_institution[1]["student_institute_roll_no"] = "DUP-00001"

    # 4. malformed APAAR ID
    students.append(
        {
            "apaar_id": "1234567890",
            "student_name": "Placeholder Student",
            "date_of_birth": "2004-01-01",
            "gender": Gender.MALE.value,
            "institution_id": first_programme["institution_id"],
            "program_id": first_programme["program_id"],
            "academic_year": "2024-25",
            "admission_quota": AdmissionQuota.MERIT.value,
            "enrollment_date": "2024-07-01",
            "student_institute_roll_no": "BAD-00001",
            "nationality": "Indian",
            "social_category": SocialCategory.GENERAL.value,
            "admission_date": "2024-07-01",
            "state_of_domicile": "Karnataka",
            "verification_status": "PENDING_REVIEW",
            "is_active": True,
            "record_status": "ACTIVE",
            "submission_source": "SEED",
        }
    )

    # 5. foreign-national seat held by an Indian citizen
    students.append(
        {
            "apaar_id": _new_apaar(),
            "student_name": "Contradiction Student",
            "date_of_birth": "2004-05-05",
            "gender": Gender.FEMALE.value,
            "institution_id": first_programme["institution_id"],
            "program_id": first_programme["program_id"],
            "academic_year": "2024-25",
            "admission_quota": AdmissionQuota.FN.value,
            "enrollment_date": "2024-07-01",
            "student_institute_roll_no": "CON-00001",
            "nationality": "Indian",
            "social_category": SocialCategory.GENERAL.value,
            "admission_date": "2024-07-01",
            "state_of_domicile": "Karnataka",
            "verification_status": "PENDING_REVIEW",
            "is_active": True,
            "record_status": "ACTIVE",
            "submission_source": "SEED",
        }
    )

    # 6. unsanctioned programme
    students.append(
        {
            "apaar_id": _new_apaar(),
            "student_name": "Unsanctioned Programme Student",
            "date_of_birth": "2004-06-06",
            "gender": Gender.MALE.value,
            "institution_id": first_programme["institution_id"],
            "program_id": "BTECH_NAVAL_ARCH",
            "academic_year": "2024-25",
            "admission_quota": AdmissionQuota.MERIT.value,
            "enrollment_date": "2024-07-01",
            "student_institute_roll_no": "UNS-00001",
            "nationality": "Indian",
            "social_category": SocialCategory.GENERAL.value,
            "admission_date": "2024-07-01",
            "state_of_domicile": "Karnataka",
            "verification_status": "PENDING_REVIEW",
            "is_active": True,
            "record_status": "ACTIVE",
            "submission_source": "SEED",
        }
    )

    # 7. impossible dates
    students.append(
        {
            "apaar_id": _new_apaar(),
            "student_name": "Future Date Student",
            "date_of_birth": "2099-01-01",
            "gender": Gender.FEMALE.value,
            "institution_id": first_programme["institution_id"],
            "program_id": first_programme["program_id"],
            "academic_year": "2024-25",
            "admission_quota": AdmissionQuota.MERIT.value,
            "enrollment_date": "2099-06-01",
            "student_institute_roll_no": "FUT-00001",
            "nationality": "Indian",
            "social_category": SocialCategory.GENERAL.value,
            "admission_date": "2099-06-01",
            "state_of_domicile": "Karnataka",
            "verification_status": "PENDING_REVIEW",
            "is_active": True,
            "record_status": "ACTIVE",
            "submission_source": "SEED",
        }
    )

    # 8. missing mandatory fields
    students.append(
        {
            "apaar_id": _new_apaar(),
            "student_name": "",
            "date_of_birth": "",
            "gender": Gender.OTHER.value,
            "institution_id": first_programme["institution_id"],
            "program_id": first_programme["program_id"],
            "academic_year": "",
            "admission_quota": AdmissionQuota.MERIT.value,
            "enrollment_date": "",
            "student_institute_roll_no": "",
            "nationality": "",
            "social_category": SocialCategory.GENERAL.value,
            "verification_status": "PENDING_REVIEW",
            "is_active": True,
            "record_status": "ACTIVE",
            "submission_source": "SEED",
        }
    )

    for student in students:
        student.setdefault("apaar_id_hmac", match_token(student.get("apaar_id")))
        student.setdefault("version", 1)
    await db["students"].insert_many(students)

    # ------------------------------------ the change-impact demo scenarios
    scenarios = await _seed_impact_scenarios(db, institutions, programmes, rng)

    # ---------------------------------------------------------------- users
    password = _demo_password()
    users = [
        {
            "user_id": f"USR-{index:02d}-{role.upper().replace('_', '-')}",
            "email": email,
            "full_name": full_name,
            "role": role,
            "institution_id": institution_id,
            "password_hash": hash_password(password),
            "is_active": True,
        }
        for index, (email, full_name, role, institution_id) in enumerate(
            DEMO_USERS, start=1
        )
    ]
    await db["users"].insert_many(users)

    # ------------------------------------------------------------- policy
    await db["policy_rules"].replace_one(
        {"policy_id": DEFAULT_POLICY_RULE["policy_id"]},
        DEFAULT_POLICY_RULE,
        upsert=True,
    )

    # -------------------------------------------- recompute the anomalies
    anomalies = await recompute_anomalies(db)

    api_key_plain, api_key_hash = generate_api_key("edusync")
    await db["api_keys"].insert_one(
        {
            "key_id": "KEY-DEMO-001",
            "label": "Demo institutional integration",
            "institution_id": "INST-0421",
            "role": "institution_admin",
            "key_hash": api_key_hash,
            "scopes": "students:read,students:write,reports:read",
            "is_active": True,
        }
    )

    return {
        "institutions": len(institutions),
        "programmes": len(programmes),
        "students": len(students),
        "anomalies": len(anomalies),
        "users": len(users),
        "accounts": [(email, role) for email, _, role, _ in DEMO_USERS],
        "scenarios": scenarios,
        "demo_password": password,
        "api_key": api_key_plain,
    }


async def _seed_impact_scenarios(
    db,
    institutions: list[dict[str, Any]],
    programmes: list[dict[str, Any]],
    rng: random.Random,
) -> dict[str, str]:
    """Create the four walk-through scenarios of the change impact detector.

    Each scenario is a synthetic student whose record is in the state that
    makes one of the rules fire, so the demo can be run end to end without
    editing data by hand.
    """
    from app.repositories.tokens import VerificationTokenRepository

    scenarios: dict[str, str] = {}

    def _base(apaar_id: str, institution_id: str, program_id: str, **overrides) -> dict[str, Any]:
        document = {
            "apaar_id": apaar_id,
            "apaar_id_hmac": match_token(apaar_id),
            "student_name": "Scenario Student",
            "date_of_birth": "2004-06-15",
            "gender": "M",
            "institution_id": institution_id,
            "program_id": program_id,
            "academic_year": "2024-25",
            "admission_quota": "REGULAR_MERIT",
            "enrollment_date": "2024-07-01",
            "student_institute_roll_no": "SCN-00001",
            "nationality": "Indian",
            "social_category": "GENERAL",
            "admission_date": "2024-07-01",
            "contact_email": "scenario@example.in",
            "contact_phone": "+91 90000 00000",
            "state_of_domicile": "Karnataka",
            "verification_status": "VERIFIED",
            "is_active": True,
            "record_status": "ACTIVE",
            "submission_source": "SEED_SCENARIO",
            "version": 1,
        }
        document.update(overrides)
        return document

    first = institutions[0]["institution_id"]
    second = institutions[1]["institution_id"]
    at_first = [p for p in programmes if p["institution_id"] == first]
    at_second = [p for p in programmes if p["institution_id"] == second]

    # 1. An admission-year correction. The student is enrolled in 2025-26 and
    #    has a live verification token, so changing the year triggers CIA-C
    #    (both years have to be recalculated) and CIA-F (the token now
    #    describes outdated data). A linked record at another institution
    #    still carries the old year, so a task is raised for it.
    scenario_one_id = "771200000001"
    scenario_one_linked_id = "771200000002"
    await db["students"].insert_many(
        [
            _base(
                scenario_one_id,
                first,
                at_first[0]["program_id"],
                student_name="Rohit Kumar Sharma",
                academic_year="2025-26",
                enrollment_date="2025-07-01",
                student_institute_roll_no="SCN-10001",
            ),
            _base(
                scenario_one_linked_id,
                second,
                at_second[0]["program_id"],
                student_name="Rohit K. Sharma",
                academic_year="2025-26",
                enrollment_date="2025-07-01",
                student_institute_roll_no="SCN-20001",
            ),
        ]
    )
    # The linked record carries the same APAAR ID, so the cross-institution
    # duplicate rule fires as well - which is exactly the point of the
    # scenario.
    await db["students"].update_one(
        {"apaar_id": scenario_one_linked_id},
        {"$set": {"apaar_id": scenario_one_id}},
    )
    scenario_one = await db["students"].find_one({"apaar_id": scenario_one_id})
    await VerificationTokenRepository(db["verification_tokens"]).issue(
        str(scenario_one["_id"]),
        {
            "institution_id": first,
            "program_id": at_first[0]["program_id"],
            "academic_year": "2025-26",
            "record_status": "ACTIVE",
        },
        issued_by="seed",
        minutes=60,
    )
    scenarios["1_academic_year_correction"] = (
        f"APAAR {scenario_one_id} is enrolled in 2025-26 with a live verification "
        "token and a linked record at another institution. Correcting the academic "
        "year to 2026-27 triggers CIA-C and CIA-F."
    )

    # 2. A programme change that pushes the destination over its sanctioned
    #    intake. The destination programme is filled to its cap by the bulk
    #    dataset, so moving one more enrolment into it breaches CIA-E.
    scenario_two_id = "772200000001"
    await db["students"].insert_one(
        _base(
            scenario_two_id,
            first,
            at_first[0]["program_id"],
            student_name="Priya Nair",
            academic_year="2024-25",
            student_institute_roll_no="SCN-10002",
        )
    )
    scenarios["2_programme_change_over_intake"] = (
        f"APAAR {scenario_two_id} can be moved into a programme that is already at "
        "its sanctioned intake, which triggers CIA-B and CIA-E."
    )

    # 3. An identifier change that collides with another institution. The
    #    target identifier belongs to a student of a different institution, so
    #    the finding is a potential conflict for review - never a conclusion.
    scenario_three_id = "773200000001"
    await db["students"].insert_one(
        _base(
            scenario_three_id,
            first,
            at_first[0]["program_id"],
            student_name="Arjun Menon",
            student_institute_roll_no="SCN-10003",
        )
    )
    other = await db["students"].find_one(
        {"institution_id": second, "record_status": "ACTIVE"}
    )
    scenarios["3_identifier_collision"] = (
        f"APAAR {scenario_three_id} can be given the identifier of a student at "
        f"{second}, which triggers CIA-A as a potential conflict for review."
        + (f" The colliding identifier is {other.get('apaar_id')}." if other else "")
    )

    # 4. A harmless correction. The contact e-mail is not bound into the seal,
    #    so changing it produces no downstream task at all.
    scenario_four_id = "774200000001"
    await db["students"].insert_one(
        _base(
            scenario_four_id,
            first,
            at_first[0]["program_id"],
            student_name="Sneha Kulkarni",
            student_institute_roll_no="SCN-10004",
        )
    )
    scenarios["4_harmless_correction"] = (
        f"APAAR {scenario_four_id} can have its contact e-mail corrected without "
        "any downstream task, because that field is not bound into the seal."
    )
    return scenarios


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the EduSynC registry.")
    parser.add_argument("--students", type=int, default=2219)
    parser.add_argument("--no-reset", action="store_true")
    args = parser.parse_args()

    # Seeding a real database is always a manual step. The script refuses to
    # touch a production database unless it is asked to, so a stray call can
    # never wipe the live registry.
    if settings.is_production and not settings.allow_production_seed:
        raise SystemExit(
            "Refusing to seed a production database. Set ALLOW_PRODUCTION_SEED=true "
            "if you really mean to overwrite the live registry."
        )

    summary = await seed(student_count=args.students, reset=not args.no_reset)
    print("EduSynC demo data seeded:")
    for key, value in summary.items():
        if key == "scenarios":
            print("  scenarios:")
            for name, detail in value.items():
                print(f"    {name}: {detail}")
        else:
            print(f"  {key:>16}: {value}")
    print()
    print("  The demo password is shown above. It is not stored in the repository;")
    print("  set DEMO_PASSWORD to choose your own before seeding.")


if __name__ == "__main__":
    asyncio.run(main())
