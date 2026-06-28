import uuid
from typing import List

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.dependencies import get_current_user_id, get_db
from app.schemas.audit import (
    AuditCreate,
    AuditListResponse,
    AuditResponse,
    AuditSummaryResponse,
    PageResponse,
    ViolationResponse,
)
from app.services.audit_pipeline import run_audit_pipeline
from app.services.audit_service import AuditService

logger = structlog.get_logger(__name__)

router = APIRouter()


def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(db)


@router.get("", response_model=List[AuditListResponse])
async def list_audits(
    user_id: str = Depends(get_current_user_id),
    service: AuditService = Depends(get_audit_service),
):
    """List all audits for the current user's projects."""
    return await service.list_audits(user_id)


@router.post("", response_model=AuditResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_audit(
    payload: AuditCreate,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    service: AuditService = Depends(get_audit_service),
    settings: Settings = Depends(get_settings),
):
    """
    Creates an audit record and immediately returns 202 Accepted.
    The full crawl → scan → score → report pipeline runs in the background.
    Poll GET /audits/{id} to check status, or GET /audits/{id}/summary for results.
    """
    audit, target_url = await service.create_audit(user_id, payload)
    logger.info("Registering background task", audit_id=str(audit.id), target_url=target_url)

    background_tasks.add_task(
        run_audit_pipeline,
        audit_id=audit.id,
        target_url=target_url,
        max_pages=settings.crawler_max_pages,
    )

    logger.info("Background task registered", audit_id=str(audit.id))


    return audit


@router.get("/{audit_id}", response_model=AuditResponse)
async def get_audit(
    audit_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    service: AuditService = Depends(get_audit_service),
):
    """Poll this endpoint to check audit status (pending → running → completed/failed)."""
    result = await service.get_audit(user_id, audit_id)
    logger.info("GET audit status", audit_id=str(audit_id), status=result.status, error=result.error_message)
    return result


@router.get("/{audit_id}/summary", response_model=AuditSummaryResponse)
async def get_audit_summary(
    audit_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    service: AuditService = Depends(get_audit_service),
):
    """
    Returns combined audit status + report data.
    Report fields are null while the pipeline is still running.
    """
    return await service.get_summary(user_id, audit_id)


@router.get("/{audit_id}/pages", response_model=List[PageResponse])
async def get_audit_pages(
    audit_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    service: AuditService = Depends(get_audit_service),
):
    return await service.get_pages(user_id, audit_id)


@router.get("/{audit_id}/violations", response_model=List[ViolationResponse])
async def get_audit_violations(
    audit_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    service: AuditService = Depends(get_audit_service),
):
    return await service.get_violations(user_id, audit_id)
