from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import structlog
from playwright.async_api import async_playwright

from app.config import get_settings
from app.engines.axe_engine import AxeEngine, AxeViolation
from app.services.crawler_service import CrawledPage

logger = structlog.get_logger(__name__)
settings = get_settings()


@dataclass
class ScanResult:
    page_url: str
    page_title: str | None
    violations: list[AxeViolation] = field(default_factory=list)
    scan_error: str | None = None

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def violations_by_severity(self) -> dict[str, list[AxeViolation]]:
        grouped: dict[str, list[AxeViolation]] = {}
        for v in self.violations:
            grouped.setdefault(v.severity.value, []).append(v)
        return grouped

    def to_dict(self) -> dict:
        return {
            "page_url": self.page_url,
            "page_title": self.page_title,
            "scan_error": self.scan_error,
            "violation_count": self.violation_count,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "severity": v.severity.value,
                    "description": v.description,
                    "help_url": v.help_url,
                    "html_snippet": v.html_snippet,
                    "selector": v.selector,
                    "wcag_criteria": v.wcag_criteria,
                    "disability_types": v.disability_types,
                }
                for v in self.violations
            ],
        }


class ScannerService:
    """
    Runs axe-core accessibility audits against each crawled page.
    Opens one browser session and reuses it across all pages for efficiency.
    """

    def __init__(self, axe_engine: AxeEngine | None = None):
        self._axe = axe_engine or AxeEngine()

    async def scan(self, pages: List[CrawledPage]) -> List[ScanResult]:
        """
        Scans all pages for accessibility violations.
        Returns one ScanResult per page. Never raises.
        """
        if not pages:
            logger.warning("Scanner received empty page list")
            return []

        logger.info("Scan started", page_count=len(pages))
        results: list[ScanResult] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=settings.crawler_headless,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                ignore_https_errors=True,
                java_script_enabled=True,
            )

            for crawled_page in pages:
                result = await self._scan_page(context, crawled_page)
                results.append(result)

            await context.close()
            await browser.close()

        total_violations = sum(r.violation_count for r in results)
        failed = sum(1 for r in results if r.scan_error)
        logger.info(
            "Scan completed",
            pages_scanned=len(results),
            total_violations=total_violations,
            failed_pages=failed,
        )

        return results

    async def scan_single(self, page_url: str, page_title: str | None = None) -> ScanResult:
        """Scans a single URL. Useful for re-scanning a specific page."""
        crawled = CrawledPage(url=page_url, title=page_title, html="")
        results = await self.scan([crawled])
        return results[0]

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    async def _scan_page(self, context, crawled_page: CrawledPage) -> ScanResult:
        page = None
        try:
            page = await context.new_page()
            timeout_ms = settings.crawler_timeout_seconds * 1000

            await page.goto(
                crawled_page.url,
                timeout=timeout_ms,
                wait_until="domcontentloaded",
            )
            await page.wait_for_load_state("domcontentloaded")

            violations = await self._axe.run(page, crawled_page.url)

            logger.info(
                "Page scanned",
                url=crawled_page.url,
                violations=len(violations),
            )

            return ScanResult(
                page_url=crawled_page.url,
                page_title=crawled_page.title,
                violations=violations,
            )

        except Exception as exc:
            logger.error("Page scan failed", url=crawled_page.url, error=str(exc))
            return ScanResult(
                page_url=crawled_page.url,
                page_title=crawled_page.title,
                scan_error=str(exc),
            )

        finally:
            if page and not page.is_closed():
                await page.close()
