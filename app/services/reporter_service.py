from __future__ import annotations

import uuid
from typing import List

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ViolationSeverity
from app.core.exceptions import NotFoundException
from app.models.page import Page
from app.models.violation import Violation
from app.repositories.audit_repo import AuditRepository
from app.repositories.report_repo import ReportRepository
from app.schemas.report import ReportResponse

logger = structlog.get_logger(__name__)

# Severity weights used in score calculation.
# Higher weight = bigger score penalty per violation.
_SEVERITY_WEIGHTS: dict[ViolationSeverity, float] = {
    ViolationSeverity.CRITICAL: 10.0,
    ViolationSeverity.SERIOUS:   5.0,
    ViolationSeverity.MODERATE:  2.0,
    ViolationSeverity.MINOR:     0.5,
}

# Maximum total penalty before score floors at 0.
_MAX_PENALTY = 100.0


class ReporterService:
    """
    Reads persisted violations for a completed audit,
    calculates an accessibility score, and saves a Report record.
    """

    def __init__(self, db: AsyncSession):
        self.report_repo = ReportRepository(db)
        self.audit_repo = AuditRepository(db)
        self.db = db

    async def build_report(self, audit_id: uuid.UUID) -> ReportResponse:
        logger.info("Building report", audit_id=str(audit_id))

        pages = await self._get_pages(audit_id)
        violations = await self._get_violations(audit_id)

        counts = _count_by_severity(violations)
        score = _calculate_score(violations)
        summary = _build_summary_text(score, counts, len(pages))

        report = await self.report_repo.create(
            audit_id=audit_id,
            accessibility_score=score,
            total_violations=len(violations),
            critical_count=counts[ViolationSeverity.CRITICAL],
            serious_count=counts[ViolationSeverity.SERIOUS],
            moderate_count=counts[ViolationSeverity.MODERATE],
            minor_count=counts[ViolationSeverity.MINOR],
            pages_scanned=len(pages),
            summary_text=summary,
        )

        logger.info(
            "Report built",
            audit_id=str(audit_id),
            score=score,
            total_violations=len(violations),
            pages=len(pages),
        )

        return ReportResponse.model_validate(report)

    async def get_report(self, audit_id: uuid.UUID) -> ReportResponse:
        report = await self.report_repo.get_by_audit_id(audit_id)
        if not report:
            raise NotFoundException("Report", str(audit_id))
        return ReportResponse.model_validate(report)

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    async def _get_pages(self, audit_id: uuid.UUID) -> List[Page]:
        result = await self.db.execute(
            select(Page).where(Page.audit_id == audit_id)
        )
        return list(result.scalars().all())

    async def _get_violations(self, audit_id: uuid.UUID) -> List[Violation]:
        result = await self.db.execute(
            select(Violation)
            .join(Page, Page.id == Violation.page_id)
            .where(Page.audit_id == audit_id)
        )
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Pure score calculation helpers (no DB — easy to unit test)
# ---------------------------------------------------------------------------

def _count_by_severity(violations: List[Violation]) -> dict[ViolationSeverity, int]:
    counts: dict[ViolationSeverity, int] = {s: 0 for s in ViolationSeverity}
    for v in violations:
        counts[v.severity] = counts.get(v.severity, 0) + 1
    return counts


def _calculate_score(violations: List[Violation]) -> float:
    """
    Weighted penalty model:
      penalty = sum(weight[severity] for each violation)
      score   = max(0, 100 - (penalty / MAX_PENALTY * 100))

    A site with zero violations scores 100.
    A site with 10 critical violations scores 0.
    Score is rounded to 1 decimal place.
    """
    if not violations:
        return 100.0

    penalty = sum(_SEVERITY_WEIGHTS.get(v.severity, 0.5) for v in violations)
    score = max(0.0, 100.0 - (penalty / _MAX_PENALTY * 100.0))
    return round(score, 1)


def _build_summary_text(score: float, counts: dict[ViolationSeverity, int], pages: int) -> str:
    total = sum(counts.values())

    if score == 100.0:
        return (
            f"Excellent! No accessibility violations were found across {pages} page(s). "
            "This website meets the scanned WCAG criteria."
        )

    grade = _score_to_grade(score)
    critical = counts[ViolationSeverity.CRITICAL]
    serious = counts[ViolationSeverity.SERIOUS]

    headline = (
        f"Accessibility score: {score}/100 ({grade}). "
        f"Found {total} violation(s) across {pages} page(s)."
    )

    if critical > 0:
        headline += (
            f" {critical} critical issue(s) require immediate attention — "
            "they block access entirely for some users."
        )
    elif serious > 0:
        headline += (
            f" {serious} serious issue(s) should be addressed soon — "
            "they significantly impact users with disabilities."
        )

    return headline


def _score_to_grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"
