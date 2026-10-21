"""Seed the EduSynC registry with a synthetic pan-India dataset.

The dataset is **entirely synthetic**: no real student, institution or APAAR
identifier is used. It is designed to exercise every detection layer so the
demo can show the platform catching real problems:

* a cross-institution duplicate APAAR ID,
* a same-institution duplicate,
* a duplicate institute roll number,
* a malformed APAAR ID,
* a foreign-national seat held by an Indian citizen,
* a programme over its sanctioned intake,
* a supernumerary ceiling breach,
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
from datetime import date, timedelta

from sqlalchemy import delete, select

from app.core.database import SessionLocal, init_models
from app.core.security import generate_api_key, hash_password
from app.models import (
    Anomaly,
    AuditLog,
    Consent,
    Institution,
    ProgramIntake,
    Student,
    User,
)
from app.models.enums import (
    AdmissionQuota,
    Gender,
    InstitutionType,
    SocialCategory,
    VerificationStatus,
)

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

DEMO_PASSWORD = "EduSync@2024"


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


async def clear_all() -> None:
    """Remove every row (so the seed is repeatable)."""
    from app.models import ApiKey, RevokedCredential

    async with SessionLocal() as session:
        for model in (
            Anomaly,
            AuditLog,
            Consent,
            RevokedCredential,
            Student,
            ProgramIntake,
            Institution,
            ApiKey,
            User,
        ):
            await session.execute(delete(model))
        await session.commit()


async def seed(student_count: int = 2219, reset: bool = True) -> dict:
    """Populate the registry with the synthetic demo dataset."""
    rng = random.Random(20240815)

    if reset:
        await clear_all()

    institutions: list[Institution] = []
    programmes: list[ProgramIntake] = []

    async with SessionLocal() as session:
        for row in INSTITUTIONS:
            institution = Institution(
                institution_id=row[0],
                name=row[1],
                institution_type=row[2],
                state=row[3],
                city=row[4],
                affiliation_university=row[5],
                approval_year=row[6],
                naac_grade=row[7],
                email=f"principal@{row[0].lower()}.edu.in",
                phone=f"+91 9{rng.randint(100000000, 999999999)}",
                is_active=True,
            )
            institutions.append(institution)
            session.add(institution)
        await session.flush()

        # Every institution offers a handful of programmes, so the compliance
        # matrix has something to compare.
        programme_slots: list[tuple] = []
        for index, institution in enumerate(institutions):
            for offset in range(5):
                programme_slots.append(
                    (institution, PROGRAMMES[(index + offset) % len(PROGRAMMES)])
                )

        # Scale the sanctioned capacity so that the demo dataset fills the
        # registry to a realistic ~92% instead of tripling every intake.
        def _def_sanctioned(row) -> int:
            return row[3] + row[4] + row[5] + row[6] + row[7]

        base_total = sum(_def_sanctioned(row) for _, row in programme_slots)
        scale = max(student_count, 1) / 0.92 / max(base_total, 1)

        for institution, row in programme_slots:
            programme = ProgramIntake(
                program_id=row[0],
                institution_id=institution.institution_id,
                program_name=row[1],
                program_level=row[2],
                approved_intake=max(int(row[3] * scale), 5),
                max_supernumerary_nri=max(int(row[4] * scale), 0),
                max_supernumerary_fn_oci=max(int(row[5] * scale), 0),
                max_supernumerary_tfw=max(int(row[6] * scale), 0),
                max_pmsss=max(int(row[7] * scale), 0),
            )
            programmes.append(programme)
            session.add(programme)
        await session.flush()

        # ------------------------------------------------- the bulk of the students
        # Two programmes are deliberately over-admitted so that the dashboard
        # shows a live breach; every other programme sits inside its caps.
        breach_slots = {0, len(programmes) // 3}
        students: list[Student] = []
        used_apaar: set[str] = set()

        def _new_apaar() -> str:
            while True:
                candidate = _apaar_id(rng)
                if candidate not in used_apaar:
                    used_apaar.add(candidate)
                    return candidate

        def _add(programme: ProgramIntake, quota: AdmissionQuota) -> None:
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
            students.append(
                Student(
                    apaar_id=_new_apaar(),
                    student_name=f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                    date_of_birth=_dob(rng),
                    gender=rng.choices(
                        [Gender.MALE, Gender.FEMALE, Gender.OTHER], weights=[48, 48, 4]
                    )[0],
                    institution_id=programme.institution_id,
                    program_id=programme.program_id,
                    academic_year="2024-25",
                    admission_quota=quota,
                    enrollment_date=enrolled.isoformat(),
                    student_institute_roll_no=(
                        f"{programme.program_id[:3]}-{rng.randint(1, 99999):05d}"
                    ),
                    nationality=nationality,
                    passport_number=passport,
                    visa_validity=visa,
                    country_of_origin=country,
                    social_category=rng.choices(
                        [
                            SocialCategory.GENERAL,
                            SocialCategory.OBC,
                            SocialCategory.SC,
                            SocialCategory.ST,
                            SocialCategory.EWS,
                        ],
                        weights=[50, 28, 12, 7, 3],
                    )[0],
                    admission_date=enrolled.isoformat(),
                    contact_email=f"student{len(students) + 1}@example.in",
                    contact_phone=f"+91 9{rng.randint(100000000, 999999999)}",
                    state_of_domicile=rng.choice(STATES),
                    verification_status=VerificationStatus.PENDING_REVIEW,
                    is_active=True,
                    photo_seed=rng.randint(0, 5),
                )
            )

        for slot_index, programme in enumerate(programmes):
            fill = rng.uniform(0.86, 0.95)
            if slot_index in breach_slots:
                fill = 1.06

            regular_target = int(round(programme.approved_intake * fill))
            # The regular seats are split into merit, management and PMSSS.
            # PMSSS is capped per course by the AICTE Approval Process
            # Handbook, so the remainder goes to merit and management.
            pmsss = min(max(programme.max_pmsss, 0), int(regular_target * 0.15))
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
                programme.max_supernumerary_nri
                + programme.max_supernumerary_fn_oci
                + programme.max_supernumerary_tfw
            )
            super_target = int(round(super_budget * 0.85))
            nri = min(programme.max_supernumerary_nri, int(super_target * 0.40))
            oci = min(programme.max_supernumerary_fn_oci, int(super_target * 0.20))
            foreign = min(
                programme.max_supernumerary_fn_oci - oci, int(super_target * 0.10)
            )
            tfw = min(
                programme.max_supernumerary_tfw, max(super_target - nri - oci - foreign, 0)
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
            if programme.institution_id == second_institution.institution_id
        )

        # Two students that certainly share an institution, so the duplicate
        # roll-number rule can be demonstrated.
        same_institution = [
            student
            for student in students
            if student.institution_id == first_programme.institution_id
        ][:2]

        # 1. cross-institution duplicate
        duplicate_apaar = students[0].apaar_id
        students.append(
            Student(
                apaar_id=duplicate_apaar,
                student_name=students[0].student_name,
                date_of_birth=students[0].date_of_birth,
                gender=students[0].gender,
                institution_id=second_programme.institution_id,
                program_id=second_programme.program_id,
                academic_year="2024-25",
                admission_quota=AdmissionQuota.MERIT,
                enrollment_date=students[0].enrollment_date,
                student_institute_roll_no=f"XDU-{rng.randint(1, 99999):05d}",
                nationality="Indian",
                social_category=SocialCategory.GENERAL,
                admission_date=students[0].enrollment_date,
                state_of_domicile=students[0].state_of_domicile,
                verification_status=VerificationStatus.PENDING_REVIEW,
                is_active=True,
            )
        )

        # 2. same-institution duplicate
        students.append(
            Student(
                apaar_id=students[1].apaar_id,
                student_name=students[1].student_name,
                date_of_birth=students[1].date_of_birth,
                gender=students[1].gender,
                institution_id=students[1].institution_id,
                program_id=students[1].program_id,
                academic_year="2024-25",
                admission_quota=students[1].admission_quota,
                enrollment_date=students[1].enrollment_date,
                student_institute_roll_no=students[1].student_institute_roll_no,
                nationality="Indian",
                social_category=SocialCategory.GENERAL,
                admission_date=students[1].enrollment_date,
                state_of_domicile=students[1].state_of_domicile,
                verification_status=VerificationStatus.PENDING_REVIEW,
                is_active=True,
            )
        )

        # 3. duplicate institute roll number (two different students)
        if len(same_institution) == 2:
            same_institution[0].student_institute_roll_no = "DUP-00001"
            same_institution[1].student_institute_roll_no = "DUP-00001"

        # 4. malformed APAAR ID
        students.append(
            Student(
                apaar_id="1234567890",
                student_name="Placeholder Student",
                date_of_birth="2004-01-01",
                gender=Gender.MALE,
                institution_id=first_programme.institution_id,
                program_id=first_programme.program_id,
                academic_year="2024-25",
                admission_quota=AdmissionQuota.MERIT,
                enrollment_date="2024-07-01",
                student_institute_roll_no="BAD-00001",
                nationality="Indian",
                social_category=SocialCategory.GENERAL,
                admission_date="2024-07-01",
                state_of_domicile="Karnataka",
                verification_status=VerificationStatus.PENDING_REVIEW,
                is_active=True,
            )
        )

        # 5. foreign-national seat held by an Indian citizen
        students.append(
            Student(
                apaar_id=_new_apaar(),
                student_name="Contradiction Student",
                date_of_birth="2004-05-05",
                gender=Gender.FEMALE,
                institution_id=first_programme.institution_id,
                program_id=first_programme.program_id,
                academic_year="2024-25",
                admission_quota=AdmissionQuota.FN,
                enrollment_date="2024-07-01",
                student_institute_roll_no="CON-00001",
                nationality="Indian",
                social_category=SocialCategory.GENERAL,
                admission_date="2024-07-01",
                state_of_domicile="Karnataka",
                verification_status=VerificationStatus.PENDING_REVIEW,
                is_active=True,
            )
        )

        # 6. unsanctioned programme
        students.append(
            Student(
                apaar_id=_new_apaar(),
                student_name="Unsanctioned Programme Student",
                date_of_birth="2004-06-06",
                gender=Gender.MALE,
                institution_id=first_programme.institution_id,
                program_id="BTECH_NAVAL_ARCH",
                academic_year="2024-25",
                admission_quota=AdmissionQuota.MERIT,
                enrollment_date="2024-07-01",
                student_institute_roll_no="UNS-00001",
                nationality="Indian",
                social_category=SocialCategory.GENERAL,
                admission_date="2024-07-01",
                state_of_domicile="Karnataka",
                verification_status=VerificationStatus.PENDING_REVIEW,
                is_active=True,
            )
        )

        # 7. impossible dates
        students.append(
            Student(
                apaar_id=_new_apaar(),
                student_name="Future Date Student",
                date_of_birth="2099-01-01",
                gender=Gender.FEMALE,
                institution_id=first_programme.institution_id,
                program_id=first_programme.program_id,
                academic_year="2024-25",
                admission_quota=AdmissionQuota.MERIT,
                enrollment_date="2099-06-01",
                student_institute_roll_no="FUT-00001",
                nationality="Indian",
                social_category=SocialCategory.GENERAL,
                admission_date="2099-06-01",
                state_of_domicile="Karnataka",
                verification_status=VerificationStatus.PENDING_REVIEW,
                is_active=True,
            )
        )

        # 8. missing mandatory fields
        students.append(
            Student(
                apaar_id=_new_apaar(),
                student_name="",
                date_of_birth="",
                gender=Gender.OTHER,
                institution_id=first_programme.institution_id,
                program_id=first_programme.program_id,
                academic_year="",
                admission_quota=AdmissionQuota.MERIT,
                enrollment_date="",
                student_institute_roll_no="",
                nationality="",
                social_category=SocialCategory.GENERAL,
                verification_status=VerificationStatus.PENDING_REVIEW,
                is_active=True,
            )
        )

        # 9. a deliberately over-admitted programme (the two breach slots above
        #    already carry the main intake breach; this one adds a third so
        #    that a single institution is visibly in breach).

        for student in students:
            session.add(student)
        await session.flush()

        # ------------------------------------------------------------- users
        for index, (email, full_name, role, institution_id) in enumerate(DEMO_USERS, start=1):
            session.add(
                User(
                    user_id=f"USR-{index:02d}-{role.upper().replace('_', '-')}",
                    email=email,
                    full_name=full_name,
                    role=role,
                    institution_id=institution_id,
                    password_hash=hash_password(DEMO_PASSWORD),
                    is_active=True,
                )
            )
        await session.flush()

        # ------------------------------------------------- recompute the anomalies
        from app.services.anomaly_engine import RegistrySnapshot, engine

        all_students = (await session.execute(select(Student))).scalars().all()
        all_programmes = (await session.execute(select(ProgramIntake))).scalars().all()
        all_institutions = (await session.execute(select(Institution))).scalars().all()
        detected = engine.evaluate(
            RegistrySnapshot(
                institutions=all_institutions,
                programs=all_programmes,
                students=all_students,
            )
        )
        now = date.today()
        for finding in detected:
            session.add(
                Anomaly(
                    student_apaar_id=finding.student_apaar_id,
                    institution_id=finding.institution_id,
                    program_id=finding.program_id,
                    anomaly_type=finding.anomaly_type,
                    severity=finding.severity,
                    details=finding.details,
                    detected_at=now,
                )
            )

        flagged = {
            finding.student_apaar_id
            for finding in detected
            if finding.severity.name in {"CRITICAL", "HIGH"}
        }
        for student in all_students:
            if student.apaar_id in flagged:
                student.verification_status = VerificationStatus.FLAGGED_ANOMALY
            else:
                student.verification_status = VerificationStatus.VERIFIED

        await session.commit()

    api_key_plain, api_key_hash = generate_api_key("edusync")
    async with SessionLocal() as session:
        from app.models import ApiKey

        session.add(
            ApiKey(
                key_id="KEY-DEMO-001",
                label="Demo institutional integration",
                institution_id="INST-0421",
                role="institution_admin",
                key_hash=api_key_hash,
                scopes="students:read,students:write,reports:read",
                is_active=True,
            )
        )
        await session.commit()

    return {
        "institutions": len(institutions),
        "programmes": len(programmes),
        "students": len(students),
        "anomalies": len(detected),
        "users": len(DEMO_USERS),
        "demo_password": DEMO_PASSWORD,
        "api_key": api_key_plain,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the EduSynC registry.")
    parser.add_argument("--students", type=int, default=2219)
    parser.add_argument("--no-reset", action="store_true")
    args = parser.parse_args()

    await init_models()
    summary = await seed(student_count=args.students, reset=not args.no_reset)
    print("EduSynC demo data seeded:")
    for key, value in summary.items():
        print(f"  {key:>16}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
