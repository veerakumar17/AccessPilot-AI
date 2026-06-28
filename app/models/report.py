import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("audits.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    accessibility_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_violations: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    critical_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    serious_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    moderate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    minor_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pages_scanned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    audit: Mapped["Audit"] = relationship("Audit", back_populates="report")
