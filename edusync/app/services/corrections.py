"""The correction workflow.

A correction is a **proposed change** to one enrolment record. The workflow
has three stages:

1. **Preview** - the impact engine runs over the proposed values and returns
   the findings and the generated checklist. Nothing is written.
2. **Apply** - the correction is written together with the new version of the
   record, the version-history entry, the impact assessment, the review tasks
   and the chained audit event.
3. **Review** - an authorised reviewer works through the checklist.

Two invariants hold throughout:

* **A linked record is never modified.** A dependent fix is a separate
  authorised action that writes its own audit entry.
* **A half-applied correction is never left silently.** When the deployment
  cannot run a transaction, the operation is recorded in ``operation_status``
  before it starts, so a crash leaves a visible, recoverable state.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import mongo
from app.repositories.students import StudentRepository
from app.repositories.tokens import VerificationTokenRepository
from app.repositories.versions import (
    ImpactAssessmentRepository,
    OperationStatusRepository,
    RecordVersionRepository,
    ReviewTaskRepository,
)
from app.services import impact_engine
from app.services.policy import active_policy

#: The fields the workflow is allowed to change.
CORRECTABLE_FIELDS = set(impact_engine.CORRECTABLE_FIELDS)


class CorrectionConflict(RuntimeError):
    """The record changed between the preview and the application."""


async def _snapshot(
    db: AsyncIOMotorDatabase,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """The registry snapshot the engine works on."""
    students = await db["students"].find({}).to_list(length=None)
    programs = await db["programmes"].find({}).to_list(length=None)
    return students, programs


async def _student_context(
    db: AsyncIOMotorDatabase, student: dict[str, Any]
) -> dict[str, Any]:
    """Everything the engine needs about one student."""
    apaar_id = str(student.get("apaar_id", ""))
    anomalies = await db["anomalies"].find({"student_apaar_id": apaar_id}).to_list(
        length=None
    )
    consents = await db["consents"].find({"student_apaar_id": apaar_id}).to_list(
        length=None
    )
    revoked = await db["revoked_credentials"].find({"apaar_id": apaar_id}).to_list(
        length=None
    )
    tokens = await VerificationTokenRepository(
        db["verification_tokens"]
    ).for_record(str(student.get("_id", "")))
    return {
        "anomalies": anomalies,
        "consents": consents,
        "revoked": revoked,
        "tokens": tokens,
    }


async def preview(
    db: AsyncIOMotorDatabase,
    record_id: str,
    proposed: dict[str, Any],
) -> dict[str, Any]:
    """Assess a proposed correction **without writing anything**.

    The response carries ``"preview": true`` so that a client cannot mistake
    the result for an applied correction.
    """
    students_repo = StudentRepository(db["students"])
    student = await students_repo.get_by_record_id(record_id)
    if student is None:
        raise LookupError("No such student record.")

    unknown = sorted(set(proposed) - CORRECTABLE_FIELDS)
    if unknown:
        raise ValueError(
            "These fields cannot be corrected: " + ", ".join(unknown)
        )

    all_students, programs = await _snapshot(db)
    context = await _student_context(db, student)
    policy = await active_policy(db)

    assessment = impact_engine.assess(
        dict(student),
        proposed,
        students=all_students,
        programs=programs,
        anomalies=context["anomalies"],
        consents=context["consents"],
        tokens=context["tokens"],
        revoked=context["revoked"],
        policy=policy,
    )

    changes = impact_engine.changed_fields(dict(student), proposed)
    checklist = [
        {
            "rule_id": finding.rule_id,
            "title": finding.title,
            "explanation": finding.explanation,
            "suggested_action": finding.suggested_action,
            "severity": finding.severity,
            "certainty": finding.certainty,
            "institution_id": finding.institution_id,
            "affected_refs": finding.affected_refs,
        }
        for finding in assessment.findings
        if finding.human_review_required
    ]

    return {
        "preview": True,
        "student_record_id": record_id,
        "current_version": int(student.get("version", 1) or 1),
        "changed_fields": [
            {
                "field": field,
                "before": before,
                "after": after,
            }
            for field, (before, after) in sorted(changes.items())
        ],
        "findings": [finding.to_dict() for finding in assessment.findings],
        "checklist": checklist,
        "highest_severity": assessment.highest_severity,
        "requires_review": assessment.requires_review,
        "policy": {
            "policy_id": policy.policy_id,
            "version": policy.version,
            "source": policy.source,
        },
        "notice": (
            "Preview only: nothing has been saved and no linked record has been "
            "changed."
        ),
    }


def _task_documents(
    assessment_id: str,
    version_no: int,
    student_record_id: str,
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Turn the findings into the review checklist."""
    tasks: list[dict[str, Any]] = []
    for finding in findings:
        if not finding.get("human_review_required", True):
            continue
        tasks.append(
            {
                "task_id": f"TASK-{secrets.token_hex(6).upper()}",
                "assessment_id": assessment_id,
                "student_record_id": student_record_id,
                "version_no": version_no,
                "institution_id": finding.get("institution_id", ""),
                "affected_ref": finding.get("affected_refs", [None])[0]
                if finding.get("affected_refs")
                else student_record_id,
                "rule_id": finding.get("rule_id", ""),
                "title": finding.get("title", ""),
                "explanation": finding.get("explanation", ""),
                "suggested_action": finding.get("suggested_action", ""),
                "severity": finding.get("severity", "MEDIUM"),
                "certainty": finding.get("certainty", "suspected"),
                "status": "open",
            }
        )
    return tasks


async def apply(
    db: AsyncIOMotorDatabase,
    record_id: str,
    proposed: dict[str, Any],
    *,
    reason: str,
    expected_version: int,
    actor: str,
    actor_role: str = "",
    ip_address: Optional[str] = None,
) -> dict[str, Any]:
    """Apply a correction.

    The record is re-read and compared with the version the reviewer saw. If
    it moved in the meantime the correction is refused with a conflict, so a
    reviewer never overwrites a change they did not see.
    """
    from app.audit import writer
    from app.repositories.audit import AuditRepository

    unknown = sorted(set(proposed) - CORRECTABLE_FIELDS)
    if unknown:
        raise ValueError("These fields cannot be corrected: " + ", ".join(unknown))
    if not reason.strip():
        raise ValueError("A correction has to record why it is being made.")

    operation_id = f"OP-{secrets.token_hex(8).upper()}"
    operations = OperationStatusRepository(db["operation_status"])

    students_repo = StudentRepository(db["students"])
    student = await students_repo.get_by_record_id(record_id)
    if student is None:
        raise LookupError("No such student record.")

    current_version = int(student.get("version", 1) or 1)
    if int(expected_version) != current_version:
        raise CorrectionConflict(
            "The record changed since the preview was taken "
            f"(the preview saw version {expected_version}, the record is now "
            f"version {current_version}). Preview the correction again."
        )

    changes = impact_engine.changed_fields(dict(student), proposed)
    if not changes:
        return {
            "applied": True,
            "changed": False,
            "version_no": current_version,
            "student_record_id": record_id,
            "notice": "Nothing changed, so no correction was applied.",
        }

    all_students, programs = await _snapshot(db)
    context = await _student_context(db, student)
    policy = await active_policy(db)
    assessment = impact_engine.assess(
        dict(student),
        proposed,
        students=all_students,
        programs=programs,
        anomalies=context["anomalies"],
        consents=context["consents"],
        tokens=context["tokens"],
        revoked=context["revoked"],
        policy=policy,
    )

    # The first correction takes the record from version 1 (the original) to
    # version 2, so the new version number is the current one plus one.
    version_no = current_version + 1
    assessment_id = f"ASM-{secrets.token_hex(8).upper()}"
    new_values = {field: after for field, (_, after) in changes.items()}
    previous_values = {field: before for field, (before, _) in changes.items()}

    await operations.start(
        operation_id,
        {
            "record_id": record_id,
            "version_no": version_no,
            "assessment_id": assessment_id,
            "actor": actor,
        },
    )

    # ---------------------------------------------------------- the writes
    async def _write_everything(session: Any = None) -> dict[str, Any]:
        """Perform every write of the correction, in order.

        When a session is given the writes join the surrounding transaction.
        """
        await students_repo.update_by_record_id(record_id, new_values, session=session)
        await students_repo.set_version(record_id, version_no, session=session)

        await RecordVersionRepository(db["record_versions"]).insert(
            {
                "version_id": f"VER-{secrets.token_hex(8).upper()}",
                "student_record_id": record_id,
                "version_no": version_no,
                "previous_values": previous_values,
                "new_values": new_values,
                "changed_fields": sorted(changes),
                "actor": actor,
                "reason": reason,
                "created_at": datetime.now(timezone.utc),
                "assessment_id": assessment_id,
            },
            session=session,
        )

        await ImpactAssessmentRepository(db["impact_assessments"]).insert(
            {
                "assessment_id": assessment_id,
                "student_record_id": record_id,
                "version_no": version_no,
                "changed_fields": sorted(changes),
                "findings": [finding.to_dict() for finding in assessment.findings],
                "highest_severity": assessment.highest_severity,
                "status": "open" if assessment.findings else "closed",
                "created_at": datetime.now(timezone.utc),
            },
            session=session,
        )

        tasks = _task_documents(
            assessment_id,
            version_no,
            record_id,
            [finding.to_dict() for finding in assessment.findings],
        )
        await ReviewTaskRepository(db["review_tasks"]).insert_many(tasks, session=session)

        # CIA-F: a correction that changes a sealed field makes the issued
        # verification tokens describe outdated data.
        reissued = await VerificationTokenRepository(
            db["verification_tokens"]
        ).mark_needs_reissue(record_id, session=session)

        await writer.log(
            AuditRepository(db["audit_events"]),
            actor=actor,
            actor_role=actor_role,
            action="APPLY_CORRECTION",
            subject=str(student.get("apaar_id", "")),
            details=(
                f"Applied correction {sorted(changes)} as version {version_no}. "
                f"Reason: {reason}. {len(tasks)} review task(s) created; "
                f"{reissued} verification token(s) flagged for reissue. "
                "No linked record was modified."
            ),
            category="CORRECTION",
            ip_address=ip_address,
            session=session,
        )
        return {"tasks": tasks, "reissued": reissued}

    if mongo.supports_transactions:
        # A replica set (MongoDB Atlas always is) can run the whole correction
        # as one transaction, so a failure half way through leaves nothing
        # behind.
        session = await mongo.client.start_session()
        try:
            async with session.start_transaction():
                outcome = await _write_everything(session=session)
        finally:
            await session.end_session()
    else:
        # A standalone server has no transactions, so the operation is
        # recorded first and can be recovered by hand.
        outcome = await _write_everything(session=None)

    tasks = outcome["tasks"]
    reissued = outcome["reissued"]

    await operations.finish(
        operation_id,
        "completed",
        {
            "version_no": version_no,
            "assessment_id": assessment_id,
            "tasks": len(tasks),
        },
    )

    return {
        "applied": True,
        "changed": True,
        "preview": False,
        "student_record_id": record_id,
        "version_no": version_no,
        "assessment_id": assessment_id,
        "changed_fields": [
            {"field": field, "before": before, "after": after}
            for field, (before, after) in sorted(changes.items())
        ],
        "findings": [finding.to_dict() for finding in assessment.findings],
        "tasks_created": len(tasks),
        "tokens_needing_reissue": reissued,
        "highest_severity": assessment.highest_severity,
        "notice": (
            "The correction was applied. The previous version is preserved and no "
            "linked record was modified - the linked work is listed in the review "
            "checklist."
        ),
    }
