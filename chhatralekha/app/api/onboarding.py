"""User Onboarding, Role Selection and Institution Joining API."""

from __future__ import annotations

import secrets
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import Principal, client_ip, get_db, get_principal
from app.audit import writer
from app.models.documents import utcnow
from app.models.enums import GuardianVerificationStatus
from app.repositories.audit import AuditRepository
from app.repositories.institutions import InstitutionRepository
from app.schemas.onboarding import (
    BasicProfileIn,
    InstitutionSearchItem,
    JoinRequestIn,
    JoinRequestOut,
    OnboardingCompletionIn,
    OnboardingStatusOut,
)

router = APIRouter(prefix="/onboarding", tags=["user-onboarding"])

RESTRICTED_ROLES = {
    "national_admin",
    "platform_operator",
    "aicte_admin",
    "university_admin",
    "state_admin",
    "district_admin",
    "regulator_admin",
}

ROLE_DASHBOARD_MAP = {
    "student": "/me",
    "parent": "/parent",
    "teacher": "/teacher",
    "institution_admin": "/institution",
    "college_admin": "/institution",
    "school_admin": "/institution",
    "university_admin": "/dashboard",
    "aicte_admin": "/dashboard",
    "national_admin": "/dashboard",
}


@router.get(
    "/institutions",
    response_model=List[InstitutionSearchItem],
    summary="Discover and search educational institutions for onboarding",
)
async def search_onboarding_institutions(
    q: Optional[str] = Query(None, description="Search query by name, city or ID"),
    category: Optional[str] = Query(None, description="Category filter (SCHOOL, COLLEGE, UNIVERSITY)"),
    state: Optional[str] = Query(None, description="State filter"),
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[InstitutionSearchItem]:
    """Search institutions registered or available on ChhatraLekha."""
    repository = InstitutionRepository(db["institutions"])
    inst_rows = await repository.all(state=state, q=q, category=category)

    results: List[InstitutionSearchItem] = []
    for row in inst_rows:
        is_active = bool(row.get("is_active", True))
        is_registered = row.get("verification_status") != "PENDING_REVIEW"
        results.append(
            InstitutionSearchItem(
                institution_id=row.get("institution_id", ""),
                name=row.get("name", ""),
                category=row.get("category") or "COLLEGE",
                institution_type=row.get("institution_type") or "ENGINEERING",
                city=row.get("city", ""),
                state=row.get("state", ""),
                is_registered=is_registered,
                is_active=is_active,
                affiliation=row.get("affiliation_university") or row.get("affiliation"),
            )
        )
    return results


@router.post(
    "/profile",
    summary="Update basic profile information during onboarding",
)
async def update_onboarding_basic_profile(
    payload: BasicProfileIn,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    """Save full name, preferred language, contact phone and optional avatar."""
    update_doc: dict[str, Any] = {
        "full_name": payload.full_name.strip(),
        "preferred_language": payload.preferred_language.strip().lower(),
        "updated_at": utcnow(),
    }
    if payload.phone:
        update_doc["phone"] = payload.phone.strip()
        update_doc["mobile"] = payload.phone.strip()

    if payload.avatar_url:
        update_doc["profile_pictures.common_url"] = payload.avatar_url
        update_doc["profile_pictures.web_url"] = payload.avatar_url

    await db["users"].update_one(
        {"user_id": principal.subject},
        {"$set": update_doc},
        upsert=True,
    )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="ONBOARDING_UPDATE_PROFILE",
        subject=principal.subject,
        details=f"User updated onboarding basic profile: {payload.full_name}.",
        category="ONBOARDING",
        ip_address=client_ip(request),
    )

    return {
        "status": "success",
        "message": "Basic profile saved.",
        "full_name": payload.full_name.strip(),
        "preferred_language": payload.preferred_language.strip().lower(),
    }


@router.post(
    "/join-request",
    response_model=JoinRequestOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an institution membership join request",
)
async def submit_institution_join_request(
    payload: JoinRequestIn,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> JoinRequestOut:
    """Submit a request to join an educational institution as student, parent, faculty or admin."""
    # 1. Prevent privileged role escalation
    requested_role_str = payload.requested_role.strip().lower()
    if requested_role_str in RESTRICTED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Security violation: Privileged role '{requested_role_str}' cannot be requested through self-service.",
        )

    # 2. Verify target institution exists
    inst_repo = InstitutionRepository(db["institutions"])
    inst = await inst_repo.get(payload.institution_id)
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Institution '{payload.institution_id}' was not found in the platform registry.",
        )

    # 3. Prevent duplicate active pending requests
    existing_pending = await db["membership_requests"].find_one({
        "user_id": principal.subject,
        "institution_id": payload.institution_id,
        "requested_role": requested_role_str,
        "status": "PENDING",
    })
    if existing_pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending join request for this role at this institution.",
        )

    now = utcnow()
    user_doc = await db["users"].find_one({"user_id": principal.subject}) or {}
    user_name = user_doc.get("full_name") or principal.display_name or "Applicant"
    user_email = user_doc.get("email") or principal.email

    # 4. Role-specific validation
    role_details: dict[str, Any] = {}

    if requested_role_str == "student":
        role_details = {
            "course_name": payload.course_name,
            "class_grade": payload.class_grade,
            "academic_year": payload.academic_year or "2024-25",
            "student_identifier": payload.student_identifier,
        }
        # If student identifier is provided, check if matching record exists
        if payload.student_identifier:
            matched_student = await db["students"].find_one({
                "institution_id": payload.institution_id,
                "$or": [
                    {"apaar_id": payload.student_identifier},
                    {"student_institute_roll_no": payload.student_identifier},
                ],
            })
            if matched_student:
                role_details["matched_student_name"] = matched_student.get("student_name")
                role_details["verified_record"] = True

    elif requested_role_str == "parent":
        if not payload.student_identifier or not payload.student_dob:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent verification requires both Student Identifier and Date of Birth.",
            )

        # Cryptographic matching check against student register
        matched_student = await db["students"].find_one({
            "$or": [
                {"apaar_id": payload.student_identifier},
                {"student_institute_roll_no": payload.student_identifier},
            ],
        })
        if not matched_student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No student record matches the provided identifier.",
            )

        if matched_student.get("date_of_birth") != payload.student_dob:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student identification details do not match.",
            )

        role_details = {
            "student_identifier": payload.student_identifier,
            "student_name": matched_student.get("student_name"),
            "relationship": payload.relationship or "Guardian",
            "verified_credentials": True,
        }

        # Store pending guardian relationship
        glink_id = f"GLINK-{secrets.token_hex(6).upper()}"
        await db["guardian_relationships"].insert_one({
            "_id": glink_id,
            "link_id": glink_id,
            "parent_user_id": principal.subject,
            "parent_email": user_email,
            "student_id": matched_student.get("apaar_id") or str(matched_student["_id"]),
            "student_name": matched_student.get("student_name", ""),
            "institution_id": payload.institution_id,
            "relationship": payload.relationship or "Guardian",
            "status": GuardianVerificationStatus.PENDING.value,
            "requested_at": now,
        })

    elif requested_role_str == "teacher":
        role_details = {
            "department": payload.department,
            "subject_specialization": payload.subject_specialization,
            "employee_id": payload.employee_id,
        }

    elif requested_role_str in ("institution_admin", "college_admin", "school_admin"):
        role_details = {
            "designation": payload.designation or "Administrator",
            "authority_proof_notes": payload.authority_proof_notes or "Submitted during onboarding",
        }

    # 5. Save join request
    request_id = f"MREQ-{secrets.token_hex(6).upper()}"
    join_doc = {
        "_id": request_id,
        "request_id": request_id,
        "user_id": principal.subject,
        "user_name": user_name,
        "user_email": user_email,
        "institution_id": payload.institution_id,
        "institution_name": inst.get("name", "Academic Institution"),
        "requested_role": requested_role_str,
        "role_details": role_details,
        "status": "PENDING",
        "created_at": now,
        "reviewed_by": None,
        "reviewed_at": None,
        "review_notes": None,
    }

    await db["membership_requests"].insert_one(join_doc)

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="SUBMIT_MEMBERSHIP_JOIN_REQUEST",
        subject=payload.institution_id,
        details=f"User {principal.subject} submitted join request {request_id} for role '{requested_role_str}' at {payload.institution_id}.",
        category="ONBOARDING",
        ip_address=client_ip(request),
    )

    return JoinRequestOut(
        request_id=request_id,
        user_id=principal.subject,
        user_name=user_name,
        user_email=user_email,
        institution_id=payload.institution_id,
        institution_name=inst.get("name", "Academic Institution"),
        requested_role=requested_role_str,
        role_details=role_details,
        status="PENDING",
        created_at=str(now),
    )


@router.get(
    "/my-requests",
    response_model=List[JoinRequestOut],
    summary="List all join requests submitted by current user",
)
async def get_my_join_requests(
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[JoinRequestOut]:
    """Retrieve applicant's join requests to track real-time approval status."""
    cursor = db["membership_requests"].find({"user_id": principal.subject}).sort("created_at", -1)
    results: List[JoinRequestOut] = []
    async for doc in cursor:
        results.append(
            JoinRequestOut(
                request_id=doc.get("request_id"),
                user_id=doc.get("user_id"),
                user_name=doc.get("user_name"),
                user_email=doc.get("user_email"),
                institution_id=doc.get("institution_id"),
                institution_name=doc.get("institution_name"),
                requested_role=doc.get("requested_role"),
                role_details=doc.get("role_details", {}),
                status=doc.get("status", "PENDING"),
                created_at=str(doc.get("created_at")),
                reviewed_by=doc.get("reviewed_by"),
                reviewed_at=str(doc.get("reviewed_at")) if doc.get("reviewed_at") else None,
                review_notes=doc.get("review_notes"),
            )
        )
    return results


@router.get(
    "/status",
    response_model=OnboardingStatusOut,
    summary="Fetch current onboarding readiness status for the user",
)
async def get_onboarding_status(
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> OnboardingStatusOut:
    """Return onboarding status, membership readiness, and recommended dashboard."""
    user = await db["users"].find_one({"user_id": principal.subject}) or {}
    full_name = user.get("full_name") or principal.display_name or "User"
    email = user.get("email") or principal.email
    profile_completed = bool(user.get("full_name") and (user.get("phone") or user.get("mobile")))

    # Query active memberships
    memberships_cursor = db["institution_memberships"].find({
        "user_id": principal.subject,
        "member_status": "ACTIVE",
    })
    memberships = await memberships_cursor.to_list(length=20)

    # Query pending requests
    pending_cursor = db["membership_requests"].find({
        "user_id": principal.subject,
        "status": "PENDING",
    }).sort("created_at", -1)
    pending_requests: List[JoinRequestOut] = []
    async for doc in pending_cursor:
        pending_requests.append(
            JoinRequestOut(
                request_id=doc.get("request_id"),
                user_id=doc.get("user_id"),
                user_name=doc.get("user_name"),
                user_email=doc.get("user_email"),
                institution_id=doc.get("institution_id"),
                institution_name=doc.get("institution_name"),
                requested_role=doc.get("requested_role"),
                role_details=doc.get("role_details", {}),
                status="PENDING",
                created_at=str(doc.get("created_at")),
            )
        )

    active_inst_id = user.get("institution_id") or principal.institution_id or (
        memberships[0]["institution_id"] if memberships else None
    )
    active_inst_name = None
    if active_inst_id:
        inst = await db["institutions"].find_one({"institution_id": active_inst_id})
        if inst:
            active_inst_name = inst.get("name")

    current_role = (user.get("role") or principal.role).lower()
    can_proceed = bool(memberships or user.get("is_demo") or user.get("onboarding_completed"))
    recommended = ROLE_DASHBOARD_MAP.get(current_role, "/dashboard")

    return OnboardingStatusOut(
        user_id=principal.subject,
        full_name=full_name,
        email=email,
        profile_completed=profile_completed,
        selected_role=current_role,
        active_institution_id=active_inst_id,
        active_institution_name=active_inst_name,
        memberships_count=len(memberships),
        pending_requests=pending_requests,
        can_proceed_to_dashboard=can_proceed,
        recommended_dashboard=recommended,
    )


@router.post(
    "/complete",
    summary="Finalize onboarding journey and transition user to their workspace",
)
async def complete_onboarding(
    payload: OnboardingCompletionIn,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    """Mark onboarding finished without granting a role or a tenant.

    ``selected_role`` and ``institution_id`` are recorded in the audit trail
    only. Authorization continues to come from the user document, which is
    changed when an administrator approves an institution membership, not
    when the applicant finishes the wizard.
    """
    requested_role = payload.selected_role.strip().lower()
    if requested_role in RESTRICTED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Privileged roles cannot be set via self-service onboarding.",
        )

    user_doc = await db["users"].find_one({"user_id": principal.subject})
    if user_doc is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The account is not active.",
        )

    authorized_role = (user_doc.get("role") or principal.role or "").strip().lower()
    now = utcnow()
    await db["users"].update_one(
        {"user_id": principal.subject},
        {"$set": {
            "onboarding_completed": True,
            "onboarded_at": now,
            "updated_at": now,
        }},
    )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="COMPLETE_ONBOARDING",
        subject=principal.subject,
        details=(
            f"Onboarding completed. Requested role '{requested_role}' was not "
            "applied. Authorization remains "
            f"'{authorized_role or 'unset'}' at institution "
            f"'{user_doc.get('institution_id') or ''}'."
        ),
        category="ONBOARDING",
        ip_address=client_ip(request),
    )

    target_dashboard = ROLE_DASHBOARD_MAP.get(authorized_role, "/dashboard")
    return {
        "status": "completed",
        "message": (
            "Onboarding completed. Institution access is granted only after "
            "an approved membership."
        ),
        "target_dashboard": target_dashboard,
        "selected_role": authorized_role,
    }
