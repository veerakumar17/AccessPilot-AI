import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import select, join
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import AuditStatus
from app.models.audit import Audit
from app.models.page import Page
from app.models.violation import Violation


class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, audit_id: uuid.UUID) -> Audit | None:
        result = await self.db.execute(select(Audit).where(Audit.id == audit_id))
        return result.scalar_one_or_none()

    async def get_by_project(self, project_id: uuid.UUID) -> List[Audit]:
        result = await self.db.execute(
            select(Audit).where(Audit.project_id == project_id).order_by(Audit.started_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_user(self, user_id: str) -> List[Audit]:
        """
        Returns all audits belonging to the user's projects,
        ordered by started_at descending.
        """
        from app.models.project import Project

        result = await self.db.execute(
            select(Audit)
            .join(Project, Audit.project_id == Project.id)
            .where(Project.user_id == user_id)
            .order_by(Audit.started_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, project_id: uuid.UUID) -> Audit:
        audit = Audit(project_id=project_id, status=AuditStatus.PENDING)
        self.db.add(audit)
        await self.db.flush()
        await self.db.refresh(audit)
        return audit

    async def update_status(self, audit: Audit, status: AuditStatus, error: str | None = None) -> Audit:
        audit.status = status
        if error:
            audit.error_message = error
        if status in (AuditStatus.COMPLETED, AuditStatus.FAILED):
            audit.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return audit

    async def get_pages(self, audit_id: uuid.UUID) -> List[Page]:
        result = await self.db.execute(select(Page).where(Page.audit_id == audit_id))
        return list(result.scalars().all())

    async def get_violations(self, audit_id: uuid.UUID) -> List[Violation]:
        result = await self.db.execute(
            select(Violation)
            .join(Page, Page.id == Violation.page_id)
            .where(Page.audit_id == audit_id)
        )
        return list(result.scalars().all())