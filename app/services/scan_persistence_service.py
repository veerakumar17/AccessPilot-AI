from __future__ import annotations

import uuid
from typing import List

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.page_repo import PageRepository
from app.services.scanner_service import ScanResult

logger = structlog.get_logger(__name__)


class ScanPersistenceService:
    """
    Persists ScanResult objects (pages + violations) into the database.
    Separated from ScannerService to keep DB concerns out of the scan engine.
    """

    def __init__(self, db: AsyncSession):
        self.repo = PageRepository(db)

    async def persist(self, audit_id: uuid.UUID, scan_results: List[ScanResult]) -> dict:
        """
        Saves all pages and their violations to the DB.
        Returns a summary dict with counts for reporting.
        """
        total_violations = 0
        pages_saved = 0

        for result in scan_results:
            page = await self.repo.create_page(
                audit_id=audit_id,
                url=result.page_url,
                title=result.page_title,
            )

            if result.violations:
                violation_dicts = [
                    {
                        "rule_id": v.rule_id,
                        "severity": v.severity,
                        "html_snippet": v.html_snippet or None,
                        "selector": v.selector or None,
                        "wcag_criteria": v.wcag_criteria,
                        "disability_types": v.disability_types,
                    }
                    for v in result.violations
                ]
                await self.repo.bulk_create_violations(page.id, violation_dicts)
                await self.repo.update_violation_count(page, len(result.violations))

            total_violations += result.violation_count
            pages_saved += 1

            logger.info(
                "Page persisted",
                url=result.page_url,
                violations=result.violation_count,
            )

        summary = {
            "pages_saved": pages_saved,
            "total_violations": total_violations,
        }
        logger.info("Scan persistence complete", audit_id=str(audit_id), **summary)
        return summary
