"""Institution-to-institution student transfer workflow."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import Principal, client_ip, get_db, require_any_permission, require_permission
from app.audit import writer
from app.core import rbac
from app.models.enums import StudentLifecycleState, TransferStatus
from app.repositories.audit import AuditRepository
from app.repositories.students import StudentRepository
from app.schemas.transfers import TransferOut, TransferRequestIn, TransferReviewIn

router = APIRouter(prefix="/transfers", tags=["transfers"])


def _to_transfer_out(doc: dict[str, Any]) -> TransferOut:
    return TransferOut(
        transfer_id=doc.get("transfer_id") or str(doc.get("_id", "")),
        apaar_id=doc.get("apaar_id", ""),
        student_name=doc.get("student_name", ""),
        from_institution_id=doc.get("from_institution_id", ""),
        to_institution_id=doc.get("to_institution_id", ""),
        from_program_id=doc.get("from_program_id", ""),
        to_program_id=doc.get("to_program_id", ""),
        status=doc.get("status", TransferStatus.SUBMITTED.value),
        reason=doc.get("reason", ""),
        review_notes=doc.get("review_notes"),
        requested_at=doc.get("requested_at"),
        requested_by=doc.get("requested_by", ""),
        reviewed_at=doc.get("reviewed_at"),
        reviewed_by=doc.get("reviewed_by"),
    )


@router.post("", response_model=TransferOut, summary="Initiate a student transfer request")
async def initiate_transfer(
    payload: TransferRequestIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.ONBOARD_STUDENTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TransferOut:
    """Initiate an inter-institutional student transfer.
    
    The receiving institution requests the transfer of an enrolled student.
    Strict tenant validation ensures receiving institutions only request for their own campus.
    """
    if principal.role != "aicte_admin" and principal.institution_id:
        if payload.to_institution_id != principal.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You may only request transfers into your own institution.",
            )

    student = await StudentRepository(db["students"]).get(payload.apaar_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student record with APAAR ID {payload.apaar_id} not found.",
        )

    from_inst = student.get("institution_id")
    if from_inst == payload.to_institution_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is already enrolled at the target institution.",
        )

    # Check for active pending transfers
    existing = await db["transfers"].find_one({
        "apaar_id": payload.apaar_id,
        "status": {"$in": [TransferStatus.SUBMITTED.value, TransferStatus.IN_REVIEW.value]},
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A transfer request is already pending for this student.",
        )

    now = datetime.now(timezone.utc)
    transfer_id = f"TRF-{secrets.token_hex(6).upper()}"
    transfer_doc = {
        "transfer_id": transfer_id,
        "apaar_id": payload.apaar_id,
        "student_name": student.get("student_name", "Unknown"),
        "from_institution_id": from_inst,
        "to_institution_id": payload.to_institution_id,
        "from_program_id": student.get("program_id", ""),
        "to_program_id": payload.to_program_id,
        "status": TransferStatus.SUBMITTED.value,
        "reason": payload.reason,
        "transfer_notes": payload.transfer_notes,
        "requested_at": now,
        "requested_by": principal.subject,
        "created_at": now,
        "updated_at": now,
    }

    await db["transfers"].insert_one(transfer_doc)

    # Create institutional notification for source institution
    await db["notifications"].insert_one({
        "user_id": from_inst,
        "institution_id": from_inst,
        "title": "Incoming Student Transfer Request",
        "message": f"Transfer requested for {student.get('student_name')} ({payload.apaar_id}) to {payload.to_institution_id}.",
        "category": "TRANSFER",
        "is_read": False,
        "created_at": now,
        "link": f"/transfers/{transfer_id}",
    })

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="INITIATE_TRANSFER",
        subject=payload.apaar_id,
        details=f"Transfer initiated from {from_inst} to {payload.to_institution_id}. Reason: {payload.reason}",
        category="STUDENT_LIFECYCLE",
        ip_address=client_ip(request),
    )

    return _to_transfer_out(transfer_doc)


@router.get("", response_model=list[TransferOut], summary="List institution transfers")
async def list_transfers(
    status_filter: Optional[str] = Query(None, alias="status"),
    principal: Principal = Depends(
        require_any_permission(
            rbac.Permission.VIEW_STUDENT_REGISTER,
            rbac.Permission.VIEW_NATIONAL_DASHBOARD,
        )
    ),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[TransferOut]:
    """List transfer requests involving the caller's institution."""
    query: dict[str, Any] = {}
    if principal.role != "aicte_admin" and principal.institution_id:
        query["$or"] = [
            {"from_institution_id": principal.institution_id},
            {"to_institution_id": principal.institution_id},
        ]

    if status_filter:
        query["status"] = status_filter

    rows = await db["transfers"].find(query).sort("requested_at", -1).to_list(length=1000)
    return [_to_transfer_out(r) for r in rows]


@router.get("/{transfer_id}", response_model=TransferOut, summary="Get transfer request details")
async def get_transfer(
    transfer_id: str,
    principal: Principal = Depends(
        require_any_permission(
            rbac.Permission.VIEW_STUDENT_REGISTER,
            rbac.Permission.VIEW_NATIONAL_DASHBOARD,
        )
    ),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TransferOut:
    """Fetch transfer request details with institution-level access control."""
    query = {"$or": [{"transfer_id": transfer_id}]}
    if ObjectId.is_valid(transfer_id):
        query["$or"].append({"_id": ObjectId(transfer_id)})

    transfer = await db["transfers"].find_one(query)
    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer request not found.",
        )

    if principal.role != "aicte_admin" and principal.institution_id:
        if (
            transfer.get("from_institution_id") != principal.institution_id
            and transfer.get("to_institution_id") != principal.institution_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view transfers for other institutions.",
            )

    return _to_transfer_out(transfer)


@router.post("/{transfer_id}/review", response_model=TransferOut, summary="Review student transfer")
async def review_transfer(
    transfer_id: str,
    payload: TransferReviewIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.ONBOARD_STUDENTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TransferOut:
    """Approve or reject a student transfer.
    
    The relieving (source) institution reviews and releases the student.
    """
    query = {"$or": [{"transfer_id": transfer_id}]}
    if ObjectId.is_valid(transfer_id):
        query["$or"].append({"_id": ObjectId(transfer_id)})

    transfer = await db["transfers"].find_one(query)
    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer request not found.",
        )

    if transfer.get("status") not in {TransferStatus.SUBMITTED.value, TransferStatus.IN_REVIEW.value}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transfer has already been finalized ({transfer.get('status')}).",
        )

    # Only relieving institution or AICTE admin can approve/reject the release
    if principal.role != "aicte_admin" and principal.institution_id:
        if transfer.get("from_institution_id") != principal.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the source/relieving institution or regulatory admin can review this transfer.",
            )

    now = datetime.now(timezone.utc)
    new_status = TransferStatus.APPROVED.value if payload.decision == "APPROVED" else TransferStatus.REJECTED.value

    # If approved, update student enrolment records
    if payload.decision == "APPROVED":
        apaar_id = transfer["apaar_id"]
        to_inst = transfer["to_institution_id"]
        to_prog = transfer["to_program_id"]

        # 1. Update source student record to TRANSFERRED
        await db["students"].update_one(
            {"apaar_id": apaar_id},
            {
                "$set": {
                    "record_status": StudentLifecycleState.TRANSFERRED.value,
                    "is_active": False,
                    "updated_at": now,
                },
                "$push": {
                    "lifecycle_history": {
                        "from_status": "ACTIVE",
                        "to_status": StudentLifecycleState.TRANSFERRED.value,
                        "reason": f"Transferred to {to_inst}: {payload.notes}",
                        "reviewed_by": principal.subject,
                        "timestamp": now,
                    }
                },
            },
        )

        # 2. Reassign student to receiving institution
        await db["students"].update_one(
            {"apaar_id": apaar_id},
            {
                "$set": {
                    "institution_id": to_inst,
                    "program_id": to_prog,
                    "record_status": StudentLifecycleState.ACTIVE.value,
                    "is_active": True,
                    "updated_at": now,
                },
                "$push": {
                    "lifecycle_history": {
                        "from_status": StudentLifecycleState.TRANSFERRED.value,
                        "to_status": StudentLifecycleState.ACTIVE.value,
                        "reason": f"Enrolled via transfer approval at {to_inst}",
                        "reviewed_by": principal.subject,
                        "timestamp": now,
                    }
                },
            },
        )

    # Update transfer document
    await db["transfers"].update_one(
        {"_id": transfer["_id"]},
        {
            "$set": {
                "status": new_status,
                "review_notes": payload.notes,
                "reviewed_at": now,
                "reviewed_by": principal.subject,
                "updated_at": now,
            }
        },
    )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="REVIEW_TRANSFER",
        subject=transfer["apaar_id"],
        details=f"Transfer from {transfer['from_institution_id']} to {transfer['to_institution_id']} was {new_status}. Notes: {payload.notes}",
        category="STUDENT_LIFECYCLE",
        ip_address=client_ip(request),
    )

    updated_transfer = await db["transfers"].find_one({"_id": transfer["_id"]})
    return _to_transfer_out(updated_transfer)
