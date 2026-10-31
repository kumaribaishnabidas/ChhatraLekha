"""Correction, impact and review-task schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChangedFieldOut(BaseModel):
    """One field the correction changes."""

    field: str
    before: Any = None
    after: Any = None


class FindingOut(BaseModel):
    """One impact finding."""

    rule_id: str
    title: str = ""
    explanation: str = ""
    affected_refs: list[str] = []
    severity: str = "MEDIUM"
    certainty: str = "suspected"
    suggested_action: str = ""
    human_review_required: bool = True
    institution_id: str = ""
    rule_data: dict[str, Any] = {}


class ChecklistItemOut(BaseModel):
    """One generated review task."""

    rule_id: str
    title: str = ""
    explanation: str = ""
    suggested_action: str = ""
    severity: str = "MEDIUM"
    certainty: str = "suspected"
    institution_id: str = ""
    affected_refs: list[str] = []


class CorrectionPreviewResponse(BaseModel):
    """The result of a correction preview. Nothing was written."""

    preview: bool = True
    student_record_id: str = ""
    current_version: int = 1
    changed_fields: list[ChangedFieldOut] = []
    findings: list[FindingOut] = []
    checklist: list[ChecklistItemOut] = []
    highest_severity: str = "INFO"
    requires_review: bool = False
    policy: dict[str, Any] = {}
    notice: str = ""


class CorrectionApplyRequest(BaseModel):
    """The body used to apply a correction."""

    changes: dict[str, Any] = Field(
        ..., description="The proposed field values."
    )
    reason: str = Field(..., min_length=1, max_length=500)
    expected_version: int = Field(
        ..., ge=1, description="The version the reviewer saw in the preview."
    )


class CorrectionApplyResponse(BaseModel):
    """The result of an applied correction."""

    applied: bool = False
    changed: bool = False
    preview: bool = False
    student_record_id: str = ""
    version_no: int = 1
    assessment_id: str = ""
    changed_fields: list[ChangedFieldOut] = []
    findings: list[FindingOut] = []
    tasks_created: int = 0
    tokens_needing_reissue: int = 0
    highest_severity: str = "INFO"
    notice: str = ""


class ImpactAssessmentOut(BaseModel):
    """One impact assessment."""

    model_config = ConfigDict(from_attributes=True)

    assessment_id: str
    student_record_id: str = ""
    version_no: int = 1
    changed_fields: list[str] = []
    findings: list[dict[str, Any]] = []
    highest_severity: str = "INFO"
    status: str = "open"
    created_at: Optional[datetime] = None


class ReviewTaskOut(BaseModel):
    """One review task."""

    model_config = ConfigDict(from_attributes=True)

    task_id: str
    assessment_id: str = ""
    student_record_id: str = ""
    institution_id: str = ""
    affected_ref: str = ""
    rule_id: str = ""
    title: str = ""
    explanation: str = ""
    suggested_action: str = ""
    severity: str = "MEDIUM"
    certainty: str = "suspected"
    status: str = "open"
    review_note: str = ""
    outcome: str = ""
    reviewer: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class VersionOut(BaseModel):
    """One version of a student record."""

    model_config = ConfigDict(from_attributes=True)

    version_id: str = ""
    student_record_id: str = ""
    version_no: int = 1
    previous_values: dict[str, Any] = {}
    new_values: dict[str, Any] = {}
    changed_fields: list[str] = []
    actor: str = ""
    reason: str = ""
    created_at: Optional[datetime] = None
    assessment_id: str = ""
