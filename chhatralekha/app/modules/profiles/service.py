"""Profile Management Business Service."""

from __future__ import annotations

import base64
import secrets
from datetime import datetime, timezone
from typing import Any, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import Principal
from app.audit import writer
from app.core.config import get_settings
from app.models.documents import utcnow
from app.modules.profiles.schemas import (
    ActiveInstitutionSwitchRequest,
    EmailRegisterRequest,
    EmailType,
    EmailVerifyCodeRequest,
    InstitutionMembershipOut,
    PictureSettingsRequest,
    PictureUploadRequest,
    PlatformType,
    ProfilePictures,
    UserPreferenceOut,
    UserProfileOut,
    UserProfileUpdateRequest,
    UserSessionOut,
)
from app.repositories.audit import AuditRepository
from app.repositories.users import UserRepository

settings = get_settings()

ROLE_LABELS: dict[str, str] = {
    "student": "Student",
    "parent": "Parent / Guardian",
    "teacher": "Teacher / Faculty",
    "institution_admin": "Institution Administrator",
    "college_admin": "College Administrator",
    "school_admin": "School Administrator",
    "university_admin": "University Administrator",
    "aicte_admin": "Directorate / University Administrator",
    "national_admin": "National Administrator",
    "verifier": "Credential Verifier",
    "platform_operator": "Platform Operator",
}


class ProfileService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.users_repo = UserRepository(db["users"])
        self.audit_repo = AuditRepository(db["audit_events"])

    async def get_user_doc(self, principal: Principal) -> dict[str, Any]:
        """Fetch user document or synthesize active demo principal."""
        user = await self.users_repo.by_user_id(principal.subject)
        if not user:
            user = {
                "user_id": principal.subject,
                "full_name": principal.display_name or "ChhatraLekha User",
                "display_name": principal.display_name or "ChhatraLekha User",
                "email": principal.email,
                "personal_email": principal.email,
                "personal_email_verified": True,
                "role": principal.role,
                "institution_id": principal.institution_id or "INST-0421",
                "account_status": "ACTIVE",
                "created_at": utcnow(),
            }
        return user

    async def get_profile(self, principal: Principal) -> UserProfileOut:
        """Fetch complete role-tailored profile with memberships and preferences."""
        user = await self.get_user_doc(principal)
        role = (user.get("role") or principal.role).lower()
        role_label = ROLE_LABELS.get(role, role.title())

        # Profile pictures
        pics_doc = user.get("profile_pictures") or {}
        profile_pictures = ProfilePictures(
            common_url=pics_doc.get("common_url"),
            web_url=pics_doc.get("web_url"),
            android_url=pics_doc.get("android_url"),
            ios_url=pics_doc.get("ios_url"),
            use_common=pics_doc.get("use_common", True),
        )

        # Active avatar determination
        if profile_pictures.use_common:
            active_avatar = profile_pictures.common_url or profile_pictures.web_url
        else:
            active_avatar = profile_pictures.web_url or profile_pictures.common_url

        # Preferences
        pref_doc = user.get("preferences") or {}
        preferences = UserPreferenceOut(
            preferred_language=pref_doc.get("preferred_language", user.get("preferred_language", "en")),
            theme=pref_doc.get("theme", "system"),
            high_contrast=pref_doc.get("high_contrast", False),
            screen_reader_optimized=pref_doc.get("screen_reader_optimized", False),
            directory_visible=pref_doc.get("directory_visible", True),
        )

        # Memberships (fetch or populate default)
        memberships = await self.get_memberships(principal, user)

        # Active institution
        active_inst = user.get("active_institution_id") or principal.institution_id or (
            memberships[0].institution_id if memberships else "INST-0421"
        )

        # Role-specific metadata
        role_metadata = await self._resolve_role_metadata(user, role, active_inst)

        # Profile completion percentage
        completion = 20
        if user.get("full_name"):
            completion += 15
        if user.get("personal_email_verified"):
            completion += 25
        elif user.get("personal_email") or user.get("email"):
            completion += 10
        if active_avatar:
            completion += 15
        if user.get("phone") or user.get("mobile"):
            completion += 15
        if user.get("institution_email_verified") or role == "student":
            completion += 10
        completion = min(completion, 100)

        created_at_val = user.get("created_at")
        created_at_str = created_at_val.isoformat() if isinstance(created_at_val, datetime) else str(created_at_val or utcnow().isoformat())

        return UserProfileOut(
            user_id=user["user_id"],
            full_name=user.get("full_name") or user.get("display_name") or "User",
            display_name=user.get("display_name") or user.get("full_name") or "User",
            phone=user.get("phone") or user.get("mobile"),
            bio=user.get("bio"),
            role=role,
            role_label=role_label,
            account_status=user.get("account_status", "ACTIVE"),
            profile_completion_percentage=completion,
            personal_email=user.get("personal_email") or user.get("email"),
            personal_email_verified=bool(user.get("personal_email_verified", False)),
            institution_email=user.get("institution_email"),
            institution_email_verified=bool(user.get("institution_email_verified", False)),
            profile_pictures=profile_pictures,
            active_avatar_url=active_avatar,
            preferences=preferences,
            memberships=memberships,
            role_metadata=role_metadata,
            active_institution_id=active_inst,
            created_at=created_at_str,
        )

    async def get_memberships(self, principal: Principal, user: dict[str, Any]) -> List[InstitutionMembershipOut]:
        """Fetch all institutional memberships for the user."""
        cursor = self.db["institution_memberships"].find({"user_id": principal.subject})
        items = []
        async for doc in cursor:
            items.append(
                InstitutionMembershipOut(
                    membership_id=doc["membership_id"],
                    user_id=doc["user_id"],
                    institution_id=doc["institution_id"],
                    institution_name=doc.get("institution_name", "Academic Institution"),
                    role=doc.get("role", principal.role),
                    role_label=ROLE_LABELS.get(doc.get("role", principal.role), doc.get("role", principal.role).title()),
                    department=doc.get("department"),
                    academic_year=doc.get("academic_year"),
                    is_primary=doc.get("is_primary", False),
                    member_status=doc.get("member_status", "ACTIVE"),
                )
            )

        if not items:
            inst_id = user.get("institution_id") or principal.institution_id or "INST-0421"
            inst_name = "Vidya Vikas Institute of Technology" if "0421" in inst_id else "Delhi Public School RK Puram"
            items.append(
                InstitutionMembershipOut(
                    membership_id=f"MEM-{principal.subject[-6:]}",
                    user_id=principal.subject,
                    institution_id=inst_id,
                    institution_name=inst_name,
                    role=principal.role,
                    role_label=ROLE_LABELS.get(principal.role, principal.role.title()),
                    department="Engineering & Technology" if "INST" in inst_id else "Secondary Education",
                    academic_year="2024-25",
                    is_primary=True,
                    member_status="ACTIVE",
                )
            )
        return items

    async def update_profile(
        self,
        principal: Principal,
        payload: UserProfileUpdateRequest,
        client_ip_addr: str,
    ) -> UserProfileOut:
        """Update personal information, display name, and preferences."""
        update_fields: dict[str, Any] = {"updated_at": utcnow()}
        if payload.full_name is not None:
            update_fields["full_name"] = payload.full_name
        if payload.display_name is not None:
            update_fields["display_name"] = payload.display_name
        if payload.phone is not None:
            update_fields["phone"] = payload.phone
            update_fields["mobile"] = payload.phone
        if payload.bio is not None:
            update_fields["bio"] = payload.bio
        if payload.preferences is not None:
            for k, v in payload.preferences.dict(exclude_unset=True).items():
                update_fields[f"preferences.{k}"] = v
                if k == "preferred_language":
                    update_fields["preferred_language"] = v

        await self.db["users"].update_one(
            {"user_id": principal.subject},
            {"$set": update_fields},
            upsert=True,
        )

        await writer.log(
            self.audit_repo,
            actor=principal.subject,
            actor_role=principal.role,
            action="UPDATE_PROFILE",
            subject=principal.subject,
            details="User updated profile details and preferences.",
            category="USER_PROFILE",
            ip_address=client_ip_addr,
        )

        return await self.get_profile(principal)

    async def upload_picture(
        self,
        principal: Principal,
        payload: PictureUploadRequest,
        client_ip_addr: str,
    ) -> ProfilePictures:
        """Upload and store a platform-specific or common profile picture."""
        raw_b64 = payload.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]

        try:
            decoded = base64.b64decode(raw_b64)
            if len(decoded) > 2 * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Profile picture exceeds maximum allowed size of 2MB.",
                )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed base64 image encoding.",
            )

        data_uri = payload.image_base64 if payload.image_base64.startswith("data:") else f"data:image/png;base64,{raw_b64}"
        field_name = f"profile_pictures.{payload.platform.value}_url"

        await self.db["users"].update_one(
            {"user_id": principal.subject},
            {"$set": {field_name: data_uri, "updated_at": utcnow()}},
            upsert=True,
        )

        await writer.log(
            self.audit_repo,
            actor=principal.subject,
            actor_role=principal.role,
            action="UPLOAD_PROFILE_PICTURE",
            subject=principal.subject,
            details=f"Updated avatar for platform: {payload.platform.value}.",
            category="USER_PROFILE",
            ip_address=client_ip_addr,
        )

        profile = await self.get_profile(principal)
        return profile.profile_pictures

    async def remove_picture(
        self,
        principal: Principal,
        platform: PlatformType,
        client_ip_addr: str,
    ) -> ProfilePictures:
        """Remove picture for platform, falling back to default."""
        field_name = f"profile_pictures.{platform.value}_url"
        await self.db["users"].update_one(
            {"user_id": principal.subject},
            {"$set": {field_name: None, "updated_at": utcnow()}},
        )

        await writer.log(
            self.audit_repo,
            actor=principal.subject,
            actor_role=principal.role,
            action="REMOVE_PROFILE_PICTURE",
            subject=principal.subject,
            details=f"Removed avatar for platform: {platform.value}.",
            category="USER_PROFILE",
            ip_address=client_ip_addr,
        )

        profile = await self.get_profile(principal)
        return profile.profile_pictures

    async def update_picture_settings(
        self,
        principal: Principal,
        payload: PictureSettingsRequest,
        client_ip_addr: str,
    ) -> ProfilePictures:
        """Toggle whether to use a single common avatar across all devices."""
        await self.db["users"].update_one(
            {"user_id": principal.subject},
            {"$set": {"profile_pictures.use_common": payload.use_common, "updated_at": utcnow()}},
            upsert=True,
        )

        profile = await self.get_profile(principal)
        return profile.profile_pictures

    async def register_email(
        self,
        principal: Principal,
        payload: EmailRegisterRequest,
        client_ip_addr: str,
    ) -> dict[str, Any]:
        """Initiate email binding and generate a 6-digit verification code."""
        email_clean = payload.email.strip().lower()

        # Check duplicate
        existing = await self.db["users"].find_one({
            "user_id": {"$ne": principal.subject},
            "$or": [
                {"email": email_clean},
                {"personal_email": email_clean},
                {"institution_email": email_clean},
            ],
        })
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This email address is already registered to another ChhatraLekha account.",
            )

        code = f"{secrets.randbelow(900000) + 100000:06d}"
        now = utcnow()

        update_data = {
            f"pending_verifications.{email_clean}": {
                "code": code,
                "email_type": payload.email_type.value,
                "institution_id": payload.institution_id,
                "created_at": now,
            },
            "updated_at": now,
        }

        if payload.email_type == EmailType.INSTITUTIONAL:
            update_data["institution_email"] = email_clean
            update_data["institution_email_verified"] = False
        else:
            update_data["personal_email"] = email_clean
            update_data["personal_email_verified"] = False

        await self.db["users"].update_one(
            {"user_id": principal.subject},
            {"$set": update_data},
            upsert=True,
        )

        await writer.log(
            self.audit_repo,
            actor=principal.subject,
            actor_role=principal.role,
            action="REQUEST_EMAIL_VERIFICATION",
            subject=principal.subject,
            details=f"Initiated verification for {payload.email_type.value} email: {email_clean}.",
            category="SECURITY",
            ip_address=client_ip_addr,
        )

        return {
            "status": "PENDING_VERIFICATION",
            "message": "Verification code generated. Please enter the 6-digit code to complete verification.",
            "email": email_clean,
            "email_type": payload.email_type.value,
            "demo_code": code,  # In prototype mode, return for easy testing
        }

    async def verify_email_code(
        self,
        principal: Principal,
        payload: EmailVerifyCodeRequest,
        client_ip_addr: str,
    ) -> dict[str, Any]:
        """Confirm 6-digit code and mark email as verified."""
        user = await self.db["users"].find_one({"user_id": principal.subject})
        email_clean = payload.email.strip().lower()

        pending = (user.get("pending_verifications") or {}).get(email_clean)
        # Allow demo verification code fallback '123456' in prototype
        is_valid_code = pending and pending.get("code") == payload.code
        if not is_valid_code and payload.code == "123456":
            is_valid_code = True

        if not is_valid_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code.",
            )

        email_type = pending.get("email_type") if pending else EmailType.PERSONAL.value
        set_updates: dict[str, Any] = {
            f"pending_verifications.{email_clean}": None,
            "updated_at": utcnow(),
        }

        if email_type == EmailType.INSTITUTIONAL.value or email_clean == user.get("institution_email"):
            set_updates["institution_email"] = email_clean
            set_updates["institution_email_verified"] = True
            set_updates["institution_email_verified_at"] = utcnow()
        else:
            set_updates["personal_email"] = email_clean
            set_updates["personal_email_verified"] = True
            set_updates["personal_email_verified_at"] = utcnow()
            set_updates["email"] = email_clean

        await self.db["users"].update_one(
            {"user_id": principal.subject},
            {"$set": set_updates},
        )

        await writer.log(
            self.audit_repo,
            actor=principal.subject,
            actor_role=principal.role,
            action="VERIFY_EMAIL_SUCCESS",
            subject=principal.subject,
            details=f"Successfully verified email address: {email_clean}.",
            category="SECURITY",
            ip_address=client_ip_addr,
        )

        return {
            "status": "VERIFIED",
            "message": "Email address successfully verified.",
            "email": email_clean,
            "verified_at": utcnow().isoformat(),
        }

    async def switch_active_institution(
        self,
        principal: Principal,
        payload: ActiveInstitutionSwitchRequest,
        client_ip_addr: str,
    ) -> UserProfileOut:
        """Switch active tenant institution for multi-affiliated accounts."""
        await self.db["users"].update_one(
            {"user_id": principal.subject},
            {"$set": {"active_institution_id": payload.institution_id, "updated_at": utcnow()}},
            upsert=True,
        )

        await writer.log(
            self.audit_repo,
            actor=principal.subject,
            actor_role=principal.role,
            action="SWITCH_ACTIVE_INSTITUTION",
            subject=principal.subject,
            details=f"Switched active tenant to: {payload.institution_id}.",
            category="TENANT_ISOLATION",
            ip_address=client_ip_addr,
        )

        return await self.get_profile(principal)

    async def _resolve_role_metadata(
        self,
        user: dict[str, Any],
        role: str,
        institution_id: str,
    ) -> dict[str, Any]:
        """Fetch role-specific attributes (student academic data, teacher classes, etc.)."""
        meta: dict[str, Any] = {}
        if role == "student":
            stu = await self.db["students"].find_one({"student_name": user.get("full_name")}) or await self.db["students"].find_one()
            if stu:
                apaar = stu.get("apaar_id", "929312345678")
                masked = f"{apaar[:4]} **** ****" if len(apaar) >= 8 else "****"
                meta["student_details"] = {
                    "student_id": stu.get("student_id", "CL-STU-042189AB"),
                    "student_name": stu.get("student_name", user.get("full_name")),
                    "apaar_id_masked": masked,
                    "institute_roll_no": stu.get("institute_roll_no", "D-2024-001"),
                    "institution_id": institution_id,
                    "institution_name": "Vidya Vikas Institute of Technology",
                    "programme_name": stu.get("programme_name", "B.Tech Computer Science & Engineering"),
                    "department": stu.get("department", "Department of Computer Science & Engineering"),
                    "class_section": "Class 3rd Year - Section A",
                    "academic_year": "2024-25",
                    "current_semester": "Semester 5",
                    "admission_quota": "MERIT",
                    "attendance_percentage": 94.2,
                    "cumulative_cgpa": 8.75,
                    "guardian_name": "Sunita Sharma",
                    "guardian_relationship": "Mother / Legal Guardian",
                    "guardian_phone_masked": "+91 98**** **12",
                    "verified_credentials_count": 3,
                }
        elif role == "teacher":
            meta["teacher_details"] = {
                "faculty_id": f"FAC-{institution_id[-4:]}-012",
                "designation": "Assistant Professor",
                "department": "Computer Science & Engineering",
                "teaching_classes": ["CSE 3A", "CSE 3B", "IT 2A"],
                "total_students_mentored": 142,
            }
        elif "admin" in role:
            meta["admin_details"] = {
                "admin_code": f"ADM-{institution_id[-4:]}",
                "access_tier": "Full Administrative Control",
                "sanctioned_intake_managed": 680,
                "compliance_status": "APPROVED",
            }
        elif role == "parent":
            meta["parent_details"] = {
                "wards": [
                    {
                        "student_name": "Aarav Sharma",
                        "institution_name": "Vidya Vikas Institute of Technology",
                        "class_section": "CSE 3A",
                        "attendance": 94.2,
                    }
                ]
            }
        return meta
