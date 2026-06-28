from __future__ import annotations

import uuid
from typing import List

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.page import Page
from app.models.violation import Violation

logger = structlog.get_logger(__name__)


class PageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_page(
        self,
        audit_id: uuid.UUID,
        url: str,
        title: str | None,
        html_snapshot: str | None = None,
    ) -> Page:
        page = Page(
            audit_id=audit_id,
            url=url,
            title=title,
            html_snapshot=html_snapshot,
        )
        self.db.add(page)
        await self.db.flush()
        await self.db.refresh(page)
        return page

    async def bulk_create_violations(
        self,
        page_id: uuid.UUID,
        violations: List[dict],
    ) -> List[Violation]:
        """
        Bulk inserts violations for a page.
        Each dict must contain: rule_id, severity, html_snippet, selector,
        wcag_criteria, disability_types.
        """
        records = [
            Violation(
                page_id=page_id,
                rule_id=v["rule_id"],
                severity=v["severity"],
                html_snippet=v.get("html_snippet"),
                selector=v.get("selector"),
                wcag_criteria=v.get("wcag_criteria"),
                disability_types=v.get("disability_types", []),
            )
            for v in violations
        ]
        self.db.add_all(records)
        await self.db.flush()
        return records

    async def update_violation_count(self, page: Page, count: int) -> None:
        page.violation_count = count
        await self.db.flush()
