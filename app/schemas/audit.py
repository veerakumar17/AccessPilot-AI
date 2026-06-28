import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, HttpUrl

from app.core.enums import AuditStatus, ViolationSeverity


class AuditCreate(BaseModel):
    project_id: uuid.UUID
    target_url: HttpUrl | None = None  # overrides project base_url if provided


class AuditResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    status: AuditStatus
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class AuditListResponse(BaseModel):
    """Returned by GET /audits — includes project name for display."""
    id: uuid.UUID
    project_id: uuid.UUID
    project_name: str
    status: AuditStatus
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None
    accessibility_score: float | None

    model_config = {"from_attributes": True}


class PageResponse(BaseModel):
    id: uuid.UUID
    audit_id: uuid.UUID
    url: str
    title: str | None
    violation_count: int
    crawled_at: datetime

    model_config = {"from_attributes": True}


class ViolationResponse(BaseModel):
    id: uuid.UUID
    page_id: uuid.UUID
    rule_id: str
    severity: ViolationSeverity
    html_snippet: str | None
    selector: str | None
    wcag_criteria: str | None
    ai_explanation: str | None
    ai_fix: str | None
    fix_type: str | None
    ai_simulation: str | None
    disability_types: List[str] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SeverityBreakdown(BaseModel):
    critical: int
    serious: int
    moderate: int
    minor: int


class AuditSummaryResponse(BaseModel):
    """
    Returned by GET /audits/{id}/summary once the pipeline completes.
    Combines audit status + report data into a single response.
    """
    audit_id: uuid.UUID
    project_id: uuid.UUID
    status: AuditStatus
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None

    # Report fields — None until pipeline completes
    accessibility_score: float | None
    pages_scanned: int | None
    total_violations: int | None
    severity_breakdown: SeverityBreakdown | None
    summary_text: str | None

    model_config = {"from_attributes": True}