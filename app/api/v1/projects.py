import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter()


def get_project_service(db: AsyncSession = Depends(get_db)) -> ProjectService:
    return ProjectService(db)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    user_id: str = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service),
):
    return await service.create_project(user_id, payload)


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    user_id: str = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service),
):
    return await service.list_projects(user_id)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service),
):
    return await service.get_project(user_id, project_id)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service),
):
    await service.delete_project(user_id, project_id)
