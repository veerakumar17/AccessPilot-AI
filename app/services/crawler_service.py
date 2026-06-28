from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import List

import structlog

from app.core.exceptions import AuditPipelineException
from app.engines.playwright_engine import PageButton, PageContent, PageForm, PageImage, PageLink, PlaywrightEngine

logger = structlog.get_logger(__name__)

MAX_PAGES_HARD_LIMIT = 50


@dataclass
class CrawledPage:
    url: str
    title: str | None
    html: str
    images: list[PageImage] = field(default_factory=list)
    forms: list[PageForm] = field(default_factory=list)
    buttons: list[PageButton] = field(default_factory=list)
    links: list[PageLink] = field(default_factory=list)
    internal_urls: list[str] = field(default_factory=list)
    status_code: int | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "title": self.title,
            "status_code": self.status_code,
            "error": self.error,
            "images": [
                {"src": img.src, "alt": img.alt, "width": img.width, "height": img.height}
                for img in self.images
            ],
            "forms": [
                {
                    "action": f.action,
                    "method": f.method,
                    "input_count": f.input_count,
                    "has_labels": f.has_labels,
                }
                for f in self.forms
            ],
            "buttons": [
                {
                    "text": b.text,
                    "type": b.button_type,
                    "aria_label": b.aria_label,
                    "is_empty": b.is_empty,
                }
                for b in self.buttons
            ],
            "links": [
                {"href": lnk.href, "text": lnk.text, "is_internal": lnk.is_internal}
                for lnk in self.links
            ],
            "internal_urls": self.internal_urls,
        }


class CrawlerService:
    """
    BFS crawler that starts from base_url, discovers internal pages,
    and extracts structured DOM data from each page via PlaywrightEngine.
    """

    def __init__(self, engine: PlaywrightEngine | None = None):
        self._engine = engine

    async def crawl(self, base_url: str, max_pages: int = MAX_PAGES_HARD_LIMIT) -> List[CrawledPage]:
        """
        Crawls up to max_pages internal pages starting from base_url.
        Returns a list of CrawledPage objects with full structured data.
        Raises AuditPipelineException if the start URL itself fails completely.
        """
        max_pages = min(max_pages, MAX_PAGES_HARD_LIMIT)
        base_url = base_url.rstrip("/")

        logger.info("Crawl started", base_url=base_url, max_pages=max_pages)

        visited: set[str] = set()
        queue: deque[str] = deque([base_url])
        results: list[CrawledPage] = []

        async with (self._engine or PlaywrightEngine()) as engine:
            while queue and len(results) < max_pages:
                url = queue.popleft()

                if url in visited:
                    continue
                visited.add(url)

                logger.info("Crawling page", url=url, crawled=len(results), remaining=len(queue))

                page_content: PageContent = await engine.get_page_content(url)

                crawled = _to_crawled_page(page_content)
                results.append(crawled)

                if page_content.error:
                    logger.warning("Page had error, skipping link discovery", url=url, error=page_content.error)
                    continue

                # Enqueue undiscovered internal URLs
                for internal_url in page_content.internal_urls:
                    if internal_url not in visited and internal_url not in queue:
                        queue.append(internal_url)

        if not results:
            raise AuditPipelineException(f"Crawler returned no pages for '{base_url}'")

        logger.info(
            "Crawl completed",
            base_url=base_url,
            total_pages=len(results),
            failed_pages=sum(1 for p in results if p.error),
        )

        return results

    async def crawl_single(self, url: str) -> CrawledPage:
        """Crawls a single URL without following links. Useful for targeted scans."""
        async with (self._engine or PlaywrightEngine()) as engine:
            content = await engine.get_page_content(url)
            return _to_crawled_page(content)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _to_crawled_page(content: PageContent) -> CrawledPage:
    return CrawledPage(
        url=content.url,
        title=content.title,
        html=content.html,
        images=content.images,
        forms=content.forms,
        buttons=content.buttons,
        links=content.links,
        internal_urls=content.internal_urls,
        status_code=content.status_code,
        error=content.error,
    )
