from __future__ import annotations

import uuid
from typing import List

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.enums import AuditStatus
from app.core.exceptions import ForbiddenException, NotFoundException
from app.repositories.audit_repo import AuditRepository
from app.repositories.project_repo import ProjectRepository
from app.repositories.report_repo import ReportRepository
from app.schemas.audit import (
    AuditCreate,
    AuditListResponse,
    AuditResponse,
    AuditSummaryResponse,
    PageResponse,
    SeverityBreakdown,
    ViolationResponse,
)

logger = structlog.get_logger(__name__)
settings = get_settings()


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_repo = AuditRepository(db)
        self.project_repo = ProjectRepository(db)
        self.report_repo = ReportRepository(db)

    async def create_audit(self, user_id: str, payload: AuditCreate) -> tuple[AuditResponse, str]:
        """
        Creates an audit record and resolves the target URL.
        Returns (AuditResponse, resolved_target_url) so the router can
        fire the pipeline background task with the correct URL.
        """
        project = await self.project_repo.get_by_id(payload.project_id)
        if not project:
            raise NotFoundException("Project", str(payload.project_id))
        if str(project.user_id) != user_id:
            raise ForbiddenException()

        target_url = str(payload.target_url) if payload.target_url else project.base_url

        audit = await self.audit_repo.create(project_id=payload.project_id)
        logger.info(
            "Audit created",
            audit_id=str(audit.id),
            project_id=str(payload.project_id),
            target_url=target_url,
        )
        return AuditResponse.model_validate(audit), target_url

    async def list_audits(self, user_id: str) -> list[AuditListResponse]:
        """List all audits for the user's projects."""
        audits = await self.audit_repo.list_by_user(user_id)

        project_repo = ProjectRepository(self.db)

        result = []
        for audit in audits:
            project = await project_repo.get_by_id(audit.project_id)
            project_name = project.name if project else "Unknown Project"

            # Check for report to get accessibility score
            report = await self.report_repo.get_by_audit_id(audit.id)
            score = report.accessibility_score if report else None

            result.append(AuditListResponse(
                id=audit.id,
                project_id=audit.project_id,
                project_name=project_name,
                status=audit.status,
                error_message=audit.error_message,
                started_at=audit.started_at,
                completed_at=audit.completed_at,
                accessibility_score=score,
            ))

        return result

    async def get_audit(self, user_id: str, audit_id: uuid.UUID) -> AuditResponse:
        audit = await self._get_owned_audit(user_id, audit_id)
        return AuditResponse.model_validate(audit)

    async def get_summary(self, user_id: str, audit_id: uuid.UUID) -> AuditSummaryResponse:
        """
        Returns a combined audit + report summary.
        Report fields are None while the pipeline is still running.
        """
        audit = await self._get_owned_audit(user_id, audit_id)
        report = await self.report_repo.get_by_audit_id(audit_id)

        return AuditSummaryResponse(
            audit_id=audit.id,
            project_id=audit.project_id,
            status=audit.status,
            started_at=audit.started_at,
            completed_at=audit.completed_at,
            error_message=audit.error_message,
            accessibility_score=report.accessibility_score if report else None,
            pages_scanned=report.pages_scanned if report else None,
            total_violations=report.total_violations if report else None,
            severity_breakdown=SeverityBreakdown(
                critical=report.critical_count,
                serious=report.serious_count,
                moderate=report.moderate_count,
                minor=report.minor_count,
            ) if report else None,
            summary_text=report.summary_text if report else None,
        )

    async def get_pages(self, user_id: str, audit_id: uuid.UUID) -> List[PageResponse]:
        await self._get_owned_audit(user_id, audit_id)
        pages = await self.audit_repo.get_pages(audit_id)
        return [PageResponse.model_validate(p) for p in pages]

    async def get_violations(self, user_id: str, audit_id: uuid.UUID) -> List[ViolationResponse]:
        await self._get_owned_audit(user_id, audit_id)
        violations = await self.audit_repo.get_violations(audit_id)
        return [ViolationResponse.model_validate(v) for v in violations]

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    async def _get_owned_audit(self, user_id: str, audit_id: uuid.UUID):
        audit = await self.audit_repo.get_by_id(audit_id)
        if not audit:
            raise NotFoundException("Audit", str(audit_id))
        project = await self.project_repo.get_by_id(audit.project_id)
        if not project or str(project.user_id) != user_id:
            raise ForbiddenException()
        return audit
