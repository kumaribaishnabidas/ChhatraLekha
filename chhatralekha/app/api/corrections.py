"""Correction and impact endpoints.

The preview endpoint writes nothing. The apply endpoint writes the new
version, the version history, the impact assessment, the review tasks and the
chained audit entry - and never modifies a linked record.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import Principal, client_ip, get_db, require_permission
from app.core import rbac
from app.models.documents import Doc
from app.repositories.students import StudentRepository
from app.repositories.versions import (
    ImpactAssessmentRepository,
    RecordVersionRepository,
    ReviewTaskRepository,
)
from app.schemas.corrections import (
    CorrectionApplyRequest,
    CorrectionApplyResponse,
    CorrectionPreviewResponse,
    ImpactAssessmentOut,
    ReviewTaskOut,
    VersionOut,
)
from app.services import corrections
from app.services.corrections import CorrectionConflict

router = APIRouter(tags=["corrections"])


def _assessment_out(row: Doc) -> ImpactAssessmentOut:
    return ImpactAssessmentOut(
        assessment_id=row.get("assessment_id", ""),
        student_record_id=row.get("student_record_id", ""),
        version_no=int(row.get("version_no", 1) or 1),
        changed_fields=list(row.get("changed_fields") or []),
        findings=list(row.get("findings") or []),
        highest_severity=row.get("highest_severity", "INFO"),
        status=row.get("status", "open"),
        created_at=row.get("created_at"),
    )


def _task_out(row: Doc) -> ReviewTaskOut:
    return ReviewTaskOut(
        task_id=row.get("task_id", ""),
        assessment_id=row.get("assessment_id", ""),
        student_record_id=row.get("student_record_id", ""),
        institution_id=row.get("institution_id", ""),
        affected_ref=row.get("affected_ref", ""),
        rule_id=row.get("rule_id", ""),
        title=row.get("title", ""),
        explanation=row.get("explanation", ""),
        suggested_action=row.get("suggested_action", ""),
        severity=row.get("severity", "MEDIUM"),
        certainty=row.get("certainty", "suspected"),
        status=row.get("status", "open"),
        review_note=row.get("review_note", ""),
        outcome=row.get("outcome", ""),
        reviewer=row.get("reviewer", ""),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _version_out(row: Doc) -> VersionOut:
    return VersionOut(
        version_id=row.get("version_id", ""),
        student_record_id=row.get("student_record_id", ""),
        version_no=int(row.get("version_no", 1) or 1),
        previous_values=dict(row.get("previous_values") or {}),
        new_values=dict(row.get("new_values") or {}),
        changed_fields=list(row.get("changed_fields") or []),
        actor=row.get("actor", ""),
        reason=row.get("reason", ""),
        created_at=row.get("created_at"),
        assessment_id=row.get("assessment_id", ""),
    )


# ----------------------------------------------------------------- preview


@router.post(
    "/students/{record_id}/correction-preview",
    response_model=CorrectionPreviewResponse,
    summary="Assess a correction without writing anything",
)
async def correction_preview(
    record_id: str,
    payload: dict[str, Any],
    principal: Principal = Depends(
        require_permission(rbac.Permission.PREVIEW_CORRECTION)
    ),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> CorrectionPreviewResponse:
    """Preview the impact of a correction.

    The response carries ``"preview": true``. Nothing is written to any
    collection, and no linked record is touched.
    """
    student = await StudentRepository(db["students"]).get_by_record_id(record_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such student record."
        )
    principal.require_scope(str(student.get("institution_id", "")))

    proposed = payload.get("changes") or payload
    if not isinstance(proposed, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The body must carry the proposed field values.",
        )

    try:
        result = await corrections.preview(db, record_id, proposed)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return CorrectionPreviewResponse(**result)


# ------------------------------------------------------------------- apply


@router.post(
    "/students/{record_id}/corrections",
    response_model=CorrectionApplyResponse,
    summary="Apply a reviewed correction",
)
async def apply_correction(
    record_id: str,
    payload: CorrectionApplyRequest,
    request: Request,
    principal: Principal = Depends(
        require_permission(rbac.Permission.APPLY_CORRECTION)
    ),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> CorrectionApplyResponse:
    """Apply a correction that was previewed first.

    The record is re-read and compared with the version the reviewer saw; if
    it moved, the correction is refused with ``409`` rather than overwriting
    a change the reviewer did not see.
    """
    student = await StudentRepository(db["students"]).get_by_record_id(record_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such student record."
        )
    principal.require_scope(str(student.get("institution_id", "")))

    try:
        result = await corrections.apply(
            db,
            record_id,
            payload.changes,
            reason=payload.reason,
            expected_version=payload.expected_version,
            actor=principal.subject,
            actor_role=principal.role,
            ip_address=client_ip(request),
        )
    except CorrectionConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return CorrectionApplyResponse(**result)


# ----------------------------------------------------------------- impacts


@router.get(
    "/impacts",
    response_model=list[ImpactAssessmentOut],
    summary="The impact assessments of the applied corrections",
)
async def list_impacts(
    status_filter: Optional[str] = Query(None, alias="status"),
    student_record_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(require_permission(rbac.Permission.VIEW_IMPACTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[ImpactAssessmentOut]:
    """Every impact assessment, newest first."""
    rows = await ImpactAssessmentRepository(db["impact_assessments"]).page(
        offset=offset, limit=limit, status=status_filter, student_record_id=student_record_id
    )
    return [_assessment_out(row) for row in rows]


@router.get(
    "/impacts/{assessment_id}",
    summary="One impact assessment with its review checklist",
)
async def get_impact(
    assessment_id: str,
    principal: Principal = Depends(require_permission(rbac.Permission.VIEW_IMPACTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    """The assessment together with the tasks it generated."""
    repository = ImpactAssessmentRepository(db["impact_assessments"])
    row = await repository.get(assessment_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such assessment."
        )
    tasks = await ReviewTaskRepository(db["review_tasks"]).for_assessment(assessment_id)
    assessment = _assessment_out(row)
    return {
        "assessment": assessment.model_dump(),
        "tasks": [_task_out(task).model_dump() for task in tasks],
    }


# ------------------------------------------------------------ review tasks


@router.get(
    "/review-tasks",
    response_model=list[ReviewTaskOut],
    summary="The review checklist",
)
async def list_review_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    institution_id: Optional[str] = Query(None),
    assessment_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(require_permission(rbac.Permission.REVIEW_TASKS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[ReviewTaskOut]:
    """The review tasks, filtered by status, severity, institution or assessment."""
    if principal.role != "aicte_admin" and principal.institution_id:
        institution_id = principal.institution_id
    rows = await ReviewTaskRepository(db["review_tasks"]).page(
        offset=offset,
        limit=limit,
        status=status_filter,
        severity=severity,
        institution_id=institution_id,
        assessment_id=assessment_id,
    )
    return [_task_out(row) for row in rows]


@router.patch(
    "/review-tasks/{task_id}",
    response_model=ReviewTaskOut,
    summary="Record the outcome of a review task",
)
async def update_review_task(
    task_id: str,
    payload: dict[str, Any],
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.REVIEW_TASKS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ReviewTaskOut:
    """Move a review task along its lifecycle.

    A dismissal has to carry a reason, because a dismissed finding is a
    decision that somebody has to be able to read.
    """
    from app.audit import writer
    from app.repositories.audit import AuditRepository

    repository = ReviewTaskRepository(db["review_tasks"])
    task = await repository.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such review task."
        )
    if principal.role != "aicte_admin" and principal.institution_id:
        if task.get("institution_id") != principal.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to review another institution's task.",
            )

    new_status = str(payload.get("status", "")).strip().lower()
    if new_status not in {"open", "in_progress", "resolved", "dismissed"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The status must be open, in_progress, resolved or dismissed.",
        )

    note = str(payload.get("review_note", "")).strip()
    outcome = str(payload.get("outcome", "")).strip()
    if new_status == "dismissed" and not note:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A dismissal has to record a reason.",
        )

    changes = {
        "status": new_status,
        "review_note": note,
        "outcome": outcome,
        "reviewer": principal.subject,
    }
    updated = await repository.update(task_id, changes)

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="REVIEW_TASK_UPDATED",
        subject=task.get("student_record_id", ""),
        details=(
            f"Task {task_id} ({task.get('rule_id')}) moved to '{new_status}'. "
            f"Note: {note or '-'}."
        ),
        category="CORRECTION_REVIEW",
        ip_address=client_ip(request),
    )
    return _task_out(updated)


# ---------------------------------------------------------------- versions


@router.get(
    "/students/{record_id}/versions",
    response_model=list[VersionOut],
    summary="The version history of one record",
)
async def list_versions(
    record_id: str,
    principal: Principal = Depends(require_permission(rbac.Permission.VIEW_IMPACTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[VersionOut]:
    """Every version of the record, newest first."""
    student = await StudentRepository(db["students"]).get_by_record_id(record_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such student record."
        )
    principal.require_scope(str(student.get("institution_id", "")))
    rows = await RecordVersionRepository(db["record_versions"]).for_record(record_id)
    return [_version_out(row) for row in rows]
