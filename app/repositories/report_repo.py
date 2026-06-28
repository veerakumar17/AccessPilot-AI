import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report


class ReportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_audit_id(self, audit_id: uuid.UUID) -> Report | None:
        result = await self.db.execute(select(Report).where(Report.audit_id == audit_id))
        return result.scalar_one_or_none()

    async def create(self, audit_id: uuid.UUID, **kwargs) -> Report:
        report = Report(audit_id=audit_id, **kwargs)
        self.db.add(report)
        await self.db.flush()
        await self.db.refresh(report)
        return report
