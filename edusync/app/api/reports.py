"""Regulatory reporting endpoints: CSV and PDF exports (requirement 7.10)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, Response
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import Principal, client_ip, get_db, require_permission
from app.audit import writer
from app.core import rbac
from app.repositories.audit import AuditRepository
from app.services import csv_export, pdf
from app.services.anomaly_engine import engine
from app.services.registry import build_snapshot

router = APIRouter(prefix="/reports", tags=["reports"])


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _filename(prefix: str, extension: str) -> str:
    return f"edusync-{prefix}-{_stamp()}.{extension}"


async def _students(db, institution_id: Optional[str], limit: int = 100000) -> list:
    query = {"record_status": "ACTIVE"}
    if institution_id:
        query["institution_id"] = institution_id
    rows = await db["students"].find(query).sort("student_name", 1).to_list(length=limit)
    return rows


async def _anomalies(
    db,
    institution_id: Optional[str],
    severity: Optional[str],
    anomaly_type: Optional[str],
    limit: int = 5000,
) -> list:
    query: dict = {}
    if institution_id:
        query["institution_id"] = institution_id
    if severity:
        query["severity"] = severity
    if anomaly_type:
        query["anomaly_type"] = anomaly_type
    rows = await db["anomalies"].find(query).sort("detected_at", -1).to_list(length=limit)
    return rows


@router.get("/students.csv", summary="Export the student register as CSV")
async def students_csv(
    request: Request,
    institution_id: Optional[str] = Query(None),
    principal: Principal = Depends(require_permission(rbac.Permission.EXPORT_REPORTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Response:
    """Download the student register as a CSV file."""
    if principal.role != "aicte_admin":
        institution_id = principal.institution_id
    rows = await _students(db, institution_id)
    body = csv_export.students(rows)
    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="EXPORT_REPORT",
        subject="students.csv",
        details=f"Exported {len(rows)} student record(s).",
        category="REPORTING",
        ip_address=client_ip(request),
    )
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
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Response:
    """Download the student register as a PDF report."""
    if principal.role != "aicte_admin":
        institution_id = principal.institution_id
    rows = await _students(db, institution_id)
    body = pdf.build_students_report_pdf(rows, subtitle=f"{len(rows)} record(s)")
    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="EXPORT_REPORT",
        subject="students.pdf",
        details=f"Exported {len(rows)} student record(s) as PDF.",
        category="REPORTING",
        ip_address=client_ip(request),
    )
    return Response(
        content=body,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{_filename("students", "pdf")}"'},
    )


@router.get("/anomalies.csv", summary="Export the anomaly register as CSV")
async def anomalies_csv(
    request: Request,
    institution_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    anomaly_type: Optional[str] = Query(None),
    principal: Principal = Depends(require_permission(rbac.Permission.EXPORT_REPORTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Response:
    """Download the anomaly register as a CSV file."""
    if principal.role != "aicte_admin":
        institution_id = principal.institution_id
    rows = await _anomalies(db, institution_id, severity, anomaly_type)
    body = csv_export.anomalies(rows)
    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="EXPORT_REPORT",
        subject="anomalies.csv",
        details=f"Exported {len(rows)} anomaly record(s).",
        category="REPORTING",
        ip_address=client_ip(request),
    )
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{_filename("anomalies", "csv")}"'},
    )


@router.get("/anomalies.pdf", summary="Export the anomaly register as PDF")
async def anomalies_pdf(
    request: Request,
    institution_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    anomaly_type: Optional[str] = Query(None),
    principal: Principal = Depends(require_permission(rbac.Permission.EXPORT_REPORTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Response:
    """Download the anomaly register as a PDF report."""
    if principal.role != "aicte_admin":
        institution_id = principal.institution_id
    rows = await _anomalies(db, institution_id, severity, anomaly_type)
    body = pdf.build_anomaly_report_pdf(rows)
    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="EXPORT_REPORT",
        subject="anomalies.pdf",
        details=f"Exported {len(rows)} anomaly record(s) as PDF.",
        category="REPORTING",
        ip_address=client_ip(request),
    )
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
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Response:
    """Download the tamper-evident audit trail as a CSV file."""
    rows = await AuditRepository(db["audit_events"]).recent(limit=limit)
    body = csv_export.audit_trail(rows)
    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="EXPORT_REPORT",
        subject="audit.csv",
        details=f"Exported {len(rows)} audit entr(ies).",
        category="REPORTING",
        ip_address=client_ip(request),
    )
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
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Response:
    """Download the programme utilisation matrix as a CSV file."""
    snapshot = await build_snapshot(db)
    snapshots = engine.build_snapshots(snapshot)
    if institution_id:
        snapshots = [
            item
            for item in snapshots
            if item.program.get("institution_id") == institution_id
        ]
    body = csv_export.programme_utilisation(snapshots)
    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="EXPORT_REPORT",
        subject="utilisation.csv",
        details=f"Exported {len(snapshots)} programme row(s).",
        category="REPORTING",
        ip_address=client_ip(request),
    )
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{_filename("utilisation", "csv")}"'},
    )
