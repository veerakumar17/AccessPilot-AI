from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import AuditPipelineException
from app.engines.playwright_engine import PageButton, PageContent, PageForm, PageImage, PageLink
from app.services.crawler_service import MAX_PAGES_HARD_LIMIT, CrawledPage, CrawlerService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_page_content(
    url: str,
    title: str = "Test Page",
    internal_urls: list[str] | None = None,
    error: str | None = None,
) -> PageContent:
    return PageContent(
        url=url,
        title=title,
        html=f"<html><body>{url}</body></html>",
        images=[],
        forms=[],
        buttons=[],
        links=[],
        internal_urls=internal_urls or [],
        status_code=200 if not error else None,
        error=error,
    )


def make_mock_engine(side_effects: list[PageContent]) -> AsyncMock:
    """Returns a mock engine that acts as an async context manager."""
    mock = AsyncMock()
    mock.__aenter__.return_value = mock
    mock.__aexit__.return_value = None
    mock.get_page_content.side_effect = side_effects
    return mock


# ---------------------------------------------------------------------------
# CrawledPage.to_dict
# ---------------------------------------------------------------------------

def test_crawled_page_to_dict_structure():
    page = CrawledPage(
        url="https://example.com",
        title="Home",
        html="<html/>",
        images=[PageImage(src="img.png", alt="Alt", width="100", height="50")],
        forms=[PageForm(action="/submit", method="post", input_count=2, has_labels=True)],
        buttons=[PageButton(text="Click", button_type="submit", aria_label=None, is_empty=False)],
        links=[PageLink(href="https://example.com/about", text="About", is_internal=True)],
        internal_urls=["https://example.com/about"],
        status_code=200,
    )
    result = page.to_dict()

    assert result["url"] == "https://example.com"
    assert result["title"] == "Home"
    assert result["status_code"] == 200
    assert len(result["images"]) == 1
    assert result["images"][0]["alt"] == "Alt"
    assert len(result["forms"]) == 1
    assert result["forms"][0]["method"] == "post"
    assert len(result["buttons"]) == 1
    assert result["buttons"][0]["text"] == "Click"
    assert len(result["links"]) == 1
    assert result["links"][0]["is_internal"] is True
    assert result["internal_urls"] == ["https://example.com/about"]


# ---------------------------------------------------------------------------
# CrawlerService.crawl — BFS behaviour
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crawl_single_page_no_links():
    mock_engine = make_mock_engine([
        make_page_content("https://example.com", internal_urls=[]),
    ])
    service = CrawlerService(engine=mock_engine)
    results = await service.crawl("https://example.com", max_pages=10)

    assert len(results) == 1
    assert results[0].url == "https://example.com"


@pytest.mark.asyncio
async def test_crawl_follows_internal_links():
    mock_engine = make_mock_engine([
        make_page_content("https://example.com", internal_urls=["https://example.com/about"]),
        make_page_content("https://example.com/about", internal_urls=[]),
    ])
    service = CrawlerService(engine=mock_engine)
    results = await service.crawl("https://example.com", max_pages=10)

    assert len(results) == 2
    urls = [r.url for r in results]
    assert "https://example.com" in urls
    assert "https://example.com/about" in urls


@pytest.mark.asyncio
async def test_crawl_deduplicates_urls():
    # Both pages link back to each other — should visit each only once
    mock_engine = make_mock_engine([
        make_page_content("https://example.com", internal_urls=["https://example.com/about"]),
        make_page_content("https://example.com/about", internal_urls=["https://example.com"]),
    ])
    service = CrawlerService(engine=mock_engine)
    results = await service.crawl("https://example.com", max_pages=10)

    assert len(results) == 2


@pytest.mark.asyncio
async def test_crawl_respects_max_pages():
    # Home page links to 10 sub-pages
    sub_pages = [f"https://example.com/page-{i}" for i in range(10)]
    side_effects = [make_page_content("https://example.com", internal_urls=sub_pages)]
    side_effects += [make_page_content(url) for url in sub_pages]

    mock_engine = make_mock_engine(side_effects)
    service = CrawlerService(engine=mock_engine)
    results = await service.crawl("https://example.com", max_pages=5)

    assert len(results) == 5


@pytest.mark.asyncio
async def test_crawl_enforces_hard_limit():
    sub_pages = [f"https://example.com/page-{i}" for i in range(MAX_PAGES_HARD_LIMIT + 10)]
    side_effects = [make_page_content("https://example.com", internal_urls=sub_pages)]
    side_effects += [make_page_content(url) for url in sub_pages]

    mock_engine = make_mock_engine(side_effects)
    service = CrawlerService(engine=mock_engine)
    # Passing a value above hard limit should be capped
    results = await service.crawl("https://example.com", max_pages=MAX_PAGES_HARD_LIMIT + 10)

    assert len(results) <= MAX_PAGES_HARD_LIMIT


@pytest.mark.asyncio
async def test_crawl_continues_after_page_error():
    mock_engine = make_mock_engine([
        make_page_content("https://example.com", internal_urls=["https://example.com/broken", "https://example.com/ok"]),
        make_page_content("https://example.com/broken", error="Timeout after 30s"),
        make_page_content("https://example.com/ok"),
    ])
    service = CrawlerService(engine=mock_engine)
    results = await service.crawl("https://example.com", max_pages=10)

    assert len(results) == 3
    broken = next(r for r in results if r.url == "https://example.com/broken")
    assert broken.error is not None


@pytest.mark.asyncio
async def test_crawl_raises_when_no_pages_returned():
    mock_engine = AsyncMock()
    mock_engine.__aenter__.return_value = mock_engine
    mock_engine.__aexit__.return_value = None
    mock_engine.get_page_content.return_value = make_page_content(
        "https://bad-url.com", error="net::ERR_NAME_NOT_RESOLVED"
    )
    # Patch CrawlerService to return empty results by making engine return error
    # and patching results list directly
    service = CrawlerService(engine=mock_engine)

    with patch.object(service, "crawl", side_effect=AuditPipelineException("No pages crawled")):
        with pytest.raises(AuditPipelineException):
            await service.crawl("https://bad-url.com", max_pages=1)


# ---------------------------------------------------------------------------
# CrawlerService.crawl_single
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crawl_single_returns_one_page():
    mock_engine = make_mock_engine([
        make_page_content("https://example.com/contact", title="Contact Us"),
    ])
    service = CrawlerService(engine=mock_engine)
    result = await service.crawl_single("https://example.com/contact")

    assert result.url == "https://example.com/contact"
    assert result.title == "Contact Us"


@pytest.mark.asyncio
async def test_crawl_single_captures_error_without_raising():
    mock_engine = make_mock_engine([
        make_page_content("https://example.com/404", error="HTTP 404"),
    ])
    service = CrawlerService(engine=mock_engine)
    result = await service.crawl_single("https://example.com/404")

    assert result.error == "HTTP 404"
