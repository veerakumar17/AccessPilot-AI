import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: uuid.UUID) -> List[Project]:
        result = await self.db.execute(select(Project).where(Project.user_id == user_id).order_by(Project.created_at.desc()))
        return list(result.scalars().all())

    async def create(self, user_id: uuid.UUID, name: str, base_url: str, description: str | None) -> Project:
        project = Project(user_id=user_id, name=name, base_url=base_url, description=description)
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        await self.db.delete(project)
        await self.db.flush()
