import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.schemas.report import ReportResponse
from app.services.reporter_service import ReporterService
from app.services.pdf_service import PdfService

router = APIRouter()


def get_reporter_service(db: AsyncSession = Depends(get_db)) -> ReporterService:
    return ReporterService(db)


def get_pdf_service(db: AsyncSession = Depends(get_db)) -> PdfService:
    return PdfService(db)


@router.get("/{audit_id}", response_model=ReportResponse)
async def get_report(
    audit_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    service: ReporterService = Depends(get_reporter_service),
):
    return await service.get_report(audit_id)


@router.get("/{audit_id}/pdf")
async def export_pdf(
    audit_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    service: PdfService = Depends(get_pdf_service),
):
    """Generate and download a PDF report for the given audit."""
    pdf_buffer = await service.generate_pdf(user_id, audit_id)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=audit_{audit_id}.pdf",
        },
    )
