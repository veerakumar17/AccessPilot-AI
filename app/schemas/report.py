import uuid
from datetime import datetime

from pydantic import BaseModel


class ReportResponse(BaseModel):
    id: uuid.UUID
    audit_id: uuid.UUID
    accessibility_score: float
    total_violations: int
    critical_count: int
    serious_count: int
    moderate_count: int
    minor_count: int
    pages_scanned: int
    summary_text: str | None
    generated_at: datetime

    model_config = {"from_attributes": True}
