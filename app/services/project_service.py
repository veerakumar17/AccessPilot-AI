import uuid
from typing import List

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.repositories.project_repo import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

logger = structlog.get_logger(__name__)


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.repo = ProjectRepository(db)

    async def create_project(self, user_id: str, payload: ProjectCreate) -> ProjectResponse:
        project = await self.repo.create(
            user_id=uuid.UUID(user_id),
            name=payload.name,
            base_url=str(payload.base_url),
            description=payload.description,
        )
        logger.info("Project created", project_id=str(project.id), user_id=user_id)
        return ProjectResponse.model_validate(project)

    async def list_projects(self, user_id: str) -> List[ProjectResponse]:
        projects = await self.repo.get_by_user(uuid.UUID(user_id))
        return [ProjectResponse.model_validate(p) for p in projects]

    async def get_project(self, user_id: str, project_id: uuid.UUID) -> ProjectResponse:
        project = await self.repo.get_by_id(project_id)
        if not project:
            raise NotFoundException("Project", str(project_id))
        if str(project.user_id) != user_id:
            raise ForbiddenException()
        return ProjectResponse.model_validate(project)

    async def delete_project(self, user_id: str, project_id: uuid.UUID) -> None:
        project = await self.repo.get_by_id(project_id)
        if not project:
            raise NotFoundException("Project", str(project_id))
        if str(project.user_id) != user_id:
            raise ForbiddenException()
        await self.repo.delete(project)
        logger.info("Project deleted", project_id=str(project_id))
