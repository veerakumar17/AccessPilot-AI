import uuid
from datetime import datetime, timezone

from sqlalchemy import ARRAY, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import DisabilityType, ViolationSeverity
from app.db.base import Base
from app.models.page import Page


class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)

    # axe-core fields
    rule_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    severity: Mapped[ViolationSeverity] = mapped_column(
        Enum(ViolationSeverity, name="violationseverity"), nullable=False, index=True
    )
    html_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    selector: Mapped[str | None] = mapped_column(Text, nullable=True)
    wcag_criteria: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # AI-enriched fields
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_fix: Mapped[str | None] = mapped_column(Text, nullable=True)
    fix_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_simulation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Disability impact (stored as array of enum strings)
    disability_types: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    page: Mapped["Page"] = relationship("Page", back_populates="violations")
