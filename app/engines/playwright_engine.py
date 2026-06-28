from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, urlunparse

import structlog
from playwright.async_api import Browser, BrowserContext, Page, async_playwright, TimeoutError as PlaywrightTimeoutError

from app.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


@dataclass
class PageImage:
    src: str
    alt: str | None
    width: str | None
    height: str | None


@dataclass
class PageForm:
    action: str | None
    method: str
    input_count: int
    has_labels: bool


@dataclass
class PageButton:
    text: str | None
    button_type: str | None
    aria_label: str | None
    is_empty: bool


@dataclass
class PageLink:
    href: str
    text: str | None
    is_internal: bool


@dataclass
class PageContent:
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


class PlaywrightEngine:
    """
    Manages Playwright browser lifecycle and full DOM extraction per page.
    Used as an async context manager.
    """

    def __init__(self):
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def __aenter__(self) -> PlaywrightEngine:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=settings.crawler_headless,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            java_script_enabled=True,
            ignore_https_errors=True,
            user_agent="AccessPilot-AI/1.0 Accessibility-Crawler",
        )
        logger.info("Playwright browser launched")
        return self

    async def __aexit__(self, *args) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Playwright browser closed")

    async def get_page_content(self, url: str) -> PageContent:
        """
        Navigates to a URL and extracts full DOM content.
        Returns a PageContent dataclass. Never raises — errors are captured in PageContent.error.
        """
        timeout_ms = settings.crawler_timeout_seconds * 1000
        page: Page | None = None

        try:
            page = await self._context.new_page()
            response = await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            status_code = response.status if response else None

            await page.wait_for_load_state("domcontentloaded")

            title = await page.title()
            html = await page.content()
            base_origin = _get_origin(url)

            images = await _extract_images(page, url)
            forms = await _extract_forms(page)
            buttons = await _extract_buttons(page)
            links, internal_urls = await _extract_links(page, url, base_origin)

            logger.info(
                "Page extracted",
                url=url,
                images=len(images),
                forms=len(forms),
                buttons=len(buttons),
                links=len(links),
                internal_urls=len(internal_urls),
            )

            return PageContent(
                url=url,
                title=title or None,
                html=html,
                images=images,
                forms=forms,
                buttons=buttons,
                links=links,
                internal_urls=internal_urls,
                status_code=status_code,
            )

        except PlaywrightTimeoutError:
            logger.warning("Page timeout", url=url)
            return PageContent(url=url, title=None, html="", error=f"Timeout after {settings.crawler_timeout_seconds}s")

        except Exception as exc:
            logger.warning("Page extraction failed", url=url, error=str(exc))
            return PageContent(url=url, title=None, html="", error=str(exc))

        finally:
            if page and not page.is_closed():
                await page.close()


# ---------------------------------------------------------------------------
# Private extraction helpers
# ---------------------------------------------------------------------------

async def _extract_images(page: Page, base_url: str) -> list[PageImage]:
    raw = await page.evaluate("""
        () => Array.from(document.querySelectorAll('img')).map(img => ({
            src: img.getAttribute('src') || '',
            alt: img.getAttribute('alt'),
            width: img.getAttribute('width'),
            height: img.getAttribute('height'),
        }))
    """)
    result = []
    for item in raw:
        src = item.get("src", "")
        if src:
            src = urljoin(base_url, src)
        result.append(PageImage(
            src=src,
            alt=item.get("alt"),
            width=item.get("width"),
            height=item.get("height"),
        ))
    return result


async def _extract_forms(page: Page) -> list[PageForm]:
    raw = await page.evaluate("""
        () => Array.from(document.querySelectorAll('form')).map(form => {
            const inputs = form.querySelectorAll('input, select, textarea');
            const labels = form.querySelectorAll('label');
            return {
                action: form.getAttribute('action'),
                method: form.getAttribute('method') || 'get',
                input_count: inputs.length,
                has_labels: labels.length > 0,
            };
        })
    """)
    return [
        PageForm(
            action=item.get("action"),
            method=item.get("method", "get").lower(),
            input_count=item.get("input_count", 0),
            has_labels=item.get("has_labels", False),
        )
        for item in raw
    ]


async def _extract_buttons(page: Page) -> list[PageButton]:
    raw = await page.evaluate("""
        () => {
            const btns = [
                ...document.querySelectorAll('button'),
                ...document.querySelectorAll('[role="button"]'),
                ...document.querySelectorAll('input[type="button"]'),
                ...document.querySelectorAll('input[type="submit"]'),
            ];
            return btns.map(btn => {
                const text = (btn.textContent || btn.value || '').trim();
                return {
                    text: text || null,
                    button_type: btn.getAttribute('type'),
                    aria_label: btn.getAttribute('aria-label'),
                    is_empty: !text && !btn.getAttribute('aria-label'),
                };
            });
        }
    """)
    return [
        PageButton(
            text=item.get("text"),
            button_type=item.get("button_type"),
            aria_label=item.get("aria_label"),
            is_empty=item.get("is_empty", False),
        )
        for item in raw
    ]


async def _extract_links(page: Page, base_url: str, base_origin: str) -> tuple[list[PageLink], list[str]]:
    raw = await page.evaluate("""
        () => Array.from(document.querySelectorAll('a[href]')).map(a => ({
            href: a.getAttribute('href') || '',
            text: (a.textContent || '').trim() || null,
        }))
    """)

    links: list[PageLink] = []
    internal_urls: list[str] = []
    seen: set[str] = set()

    for item in raw:
        href = item.get("href", "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        absolute = urljoin(base_url, href)
        normalized = _normalize_url(absolute)
        is_internal = _get_origin(normalized) == base_origin

        links.append(PageLink(href=normalized, text=item.get("text"), is_internal=is_internal))

        if is_internal and normalized not in seen:
            seen.add(normalized)
            internal_urls.append(normalized)

    return links, internal_urls


def _normalize_url(url: str) -> str:
    """Strips fragments and trailing slashes for consistent deduplication."""
    parsed = urlparse(url)
    clean = parsed._replace(fragment="")
    result = urlunparse(clean).rstrip("/")
    return result or url


def _get_origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}".lower()
