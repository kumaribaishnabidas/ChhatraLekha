"""Regulatory reporting endpoints: CSV and PDF exports (requirement 9)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Principal, client_ip, require_permission
from app.audit import writer
from app.core import rbac
from app.core.database import get_db
from app.models import Anomaly, AuditLog, ProgramIntake, Student
from app.models.enums import AnomalySeverity, AnomalyType
from app.services import csv_export, pdf
from app.services.anomaly_engine import RegistrySnapshot, engine

router = APIRouter(prefix="/reports", tags=["reports"])


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _filename(prefix: str, extension: str) -> str:
    return f"edusync-{prefix}-{_stamp()}.{extension}"


async def _students(session: AsyncSession, institution_id: Optional[str]) -> list[Student]:
    statement = select(Student).order_by(Student.student_name)
    if institution_id:
        statement = statement.where(Student.institution_id == institution_id)
    return list((await session.execute(statement)).scalars().all())


async def _anomalies(
    session: AsyncSession,
    institution_id: Optional[str],
    severity: Optional[AnomalySeverity],
    anomaly_type: Optional[AnomalyType],
) -> list[Anomaly]:
    statement = select(Anomaly).order_by(Anomaly.detected_at.desc())
    if institution_id:
        statement = statement.where(Anomaly.institution_id == institution_id)
    if severity:
        statement = statement.where(Anomaly.severity == severity)
    if anomaly_type:
        statement = statement.where(Anomaly.anomaly_type == anomaly_type)
    return list((await session.execute(statement)).scalars().all())


@router.get("/students.csv", summary="Export the student register as CSV")
async def students_csv(
    request: Request,
    institution_id: Optional[str] = Query(None),
    principal: Principal = Depends(require_permission(rbac.Permission.EXPORT_REPORTS)),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Download the student register as a CSV file."""
    if principal.role != "aicte_admin":
        institution_id = principal.institution_id
    rows = await _students(session, institution_id)
    body = csv_export.students(rows)
    await writer.log(
        session,
        actor=principal.subject,
        actor_role=principal.role,
        action="EXPORT_REPORT",
        subject="students.csv",
        details=f"Exported {len(rows)} student record(s).",
        category="REPORTING",
        ip_address=client_ip(request),
    )
    await session.commit()
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{_filename("students", "csv")}"'},
    )


@router.get("/students.pdf", summary="Export the student register as PDF")
async def students_pdf(
    request: Request,
    institution_id: Optional[str] = Query(None),
    principal: Principal = Depends(require_permission(rbac.Permission.EXPORT_REPORTS)),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Download the student register as a PDF report."""
    if principal.role != "aicte_admin":
        institution_id = principal.institution_id
    rows = await _students(session, institution_id)
    body = pdf.build_students_report_pdf(rows, subtitle=f"{len(rows)} record(s)")
    await writer.log(
        session,
        actor=principal.subject,
        actor_role=principal.role,
        action="EXPORT_REPORT",
        subject="students.pdf",
        details=f"Exported {len(rows)} student record(s) as PDF.",
        category="REPORTING",
        ip_address=client_ip(request),
    )
    await session.commit()
    return Response(
        content=body,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{_filename("students", "pdf")}"'},
    )


@router.get("/anomalies.csv", summary="Export the anomaly register as CSV")
async def anomalies_csv(
    request: Request,
    institution_id: Optional[str] = Query(None),
    severity: Optional[AnomalySeverity] = Query(None),
    anomaly_type: Optional[AnomalyType] = Query(None),
    principal: Principal = Depends(require_permission(rbac.Permission.EXPORT_REPORTS)),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Download the anomaly register as a CSV file."""
    if principal.role != "aicte_admin":
        institution_id = principal.institution_id
    rows = await _anomalies(session, institution_id, severity, anomaly_type)
    body = csv_export.anomalies(rows)
    await writer.log(
        session,
        actor=principal.subject,
        actor_role=principal.role,
        action="EXPORT_REPORT",
        subject="anomalies.csv",
        details=f"Exported {len(rows)} anomaly record(s).",
        category="REPORTING",
        ip_address=client_ip(request),
    )
    await session.commit()
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{_filename("anomalies", "csv")}"'},
    )


@router.get("/anomalies.pdf", summary="Export the anomaly register as PDF")
async def anomalies_pdf(
    request: Request,
    institution_id: Optional[str] = Query(None),
    severity: Optional[AnomalySeverity] = Query(None),
    anomaly_type: Optional[AnomalyType] = Query(None),
    principal: Principal = Depends(require_permission(rbac.Permission.EXPORT_REPORTS)),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Download the anomaly register as a PDF report."""
    if principal.role != "aicte_admin":
        institution_id = principal.institution_id
    rows = await _anomalies(session, institution_id, severity, anomaly_type)
    body = pdf.build_anomaly_report_pdf(rows)
    await writer.log(
        session,
        actor=principal.subject,
        actor_role=principal.role,
        action="EXPORT_REPORT",
        subject="anomalies.pdf",
        details=f"Exported {len(rows)} anomaly record(s) as PDF.",
        category="REPORTING",
        ip_address=client_ip(request),
    )
    await session.commit()
    return Response(
        content=body,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{_filename("anomalies", "pdf")}"'},
    )


@router.get("/audit.csv", summary="Export the audit trail as CSV")
async def audit_csv(
    request: Request,
    limit: int = Query(1000, ge=1, le=10000),
    principal: Principal = Depends(require_permission(rbac.Permission.VIEW_AUDIT_TRAIL)),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Download the tamper-evident audit trail as a CSV file."""
    rows = (
        await session.execute(
            select(AuditLog).order_by(AuditLog.log_id.desc()).limit(limit)
        )
    ).scalars().all()
    body = csv_export.audit_trail(reversed(rows))
    await writer.log(
        session,
        actor=principal.subject,
        actor_role=principal.role,
        action="EXPORT_REPORT",
        subject="audit.csv",
        details=f"Exported {len(rows)} audit entr(ies).",
        category="REPORTING",
        ip_address=client_ip(request),
    )
    await session.commit()
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{_filename("audit", "csv")}"'},
    )


@router.get("/utilisation.csv", summary="Export the intake-utilisation matrix as CSV")
async def utilisation_csv(
    request: Request,
    institution_id: Optional[str] = Query(None),
    principal: Principal = Depends(require_permission(rbac.Permission.EXPORT_REPORTS)),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Download the programme utilisation matrix as a CSV file."""
    programs = (
        await session.execute(select(ProgramIntake).order_by(ProgramIntake.program_name))
    ).scalars().all()
    students = (await session.execute(select(Student))).scalars().all()
    snapshots = engine.build_snapshots(
        RegistrySnapshot(programs=programs, students=students)
    )
    if institution_id:
        snapshots = [
            snapshot
            for snapshot in snapshots
            if snapshot.program.institution_id == institution_id
        ]
    body = csv_export.programme_utilisation(snapshots)
    await writer.log(
        session,
        actor=principal.subject,
        actor_role=principal.role,
        action="EXPORT_REPORT",
        subject="utilisation.csv",
        details=f"Exported {len(snapshots)} programme row(s).",
        category="REPORTING",
        ip_address=client_ip(request),
    )
    await session.commit()
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{_filename("utilisation", "csv")}"'},
    )
