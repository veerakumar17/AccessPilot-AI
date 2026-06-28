from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.engines.playwright_engine import (
    PlaywrightEngine,
    _extract_buttons,
    _extract_forms,
    _extract_images,
    _extract_links,
    _normalize_url,
    _get_origin,
)


# ---------------------------------------------------------------------------
# URL utilities
# ---------------------------------------------------------------------------

def test_normalize_url_strips_fragment():
    assert _normalize_url("https://example.com/page#section") == "https://example.com/page"


def test_normalize_url_strips_trailing_slash():
    assert _normalize_url("https://example.com/page/") == "https://example.com/page"


def test_normalize_url_keeps_query_string():
    assert _normalize_url("https://example.com/search?q=test") == "https://example.com/search?q=test"


def test_get_origin_lowercases():
    assert _get_origin("HTTPS://Example.COM/page") == "https://example.com"


def test_get_origin_includes_port():
    assert _get_origin("http://localhost:8000/api") == "http://localhost:8000"


# ---------------------------------------------------------------------------
# DOM extraction helpers (mocked page.evaluate)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_extract_images_returns_correct_fields():
    mock_page = AsyncMock()
    mock_page.evaluate.return_value = [
        {"src": "/img/logo.png", "alt": "Logo", "width": "100", "height": "50"},
        {"src": "", "alt": None, "width": None, "height": None},
    ]
    images = await _extract_images(mock_page, "https://example.com")
    assert len(images) == 1  # empty src is skipped
    assert images[0].src == "https://example.com/img/logo.png"
    assert images[0].alt == "Logo"


@pytest.mark.asyncio
async def test_extract_images_resolves_relative_src():
    mock_page = AsyncMock()
    mock_page.evaluate.return_value = [{"src": "images/hero.jpg", "alt": "Hero", "width": None, "height": None}]
    images = await _extract_images(mock_page, "https://example.com/about/")
    assert images[0].src == "https://example.com/about/images/hero.jpg"


@pytest.mark.asyncio
async def test_extract_forms_parses_correctly():
    mock_page = AsyncMock()
    mock_page.evaluate.return_value = [
        {"action": "/submit", "method": "POST", "input_count": 3, "has_labels": True},
        {"action": None, "method": "get", "input_count": 1, "has_labels": False},
    ]
    forms = await _extract_forms(mock_page)
    assert len(forms) == 2
    assert forms[0].method == "post"
    assert forms[0].has_labels is True
    assert forms[1].has_labels is False


@pytest.mark.asyncio
async def test_extract_buttons_detects_empty():
    mock_page = AsyncMock()
    mock_page.evaluate.return_value = [
        {"text": "Submit", "button_type": "submit", "aria_label": None, "is_empty": False},
        {"text": None, "button_type": "button", "aria_label": None, "is_empty": True},
        {"text": None, "button_type": "button", "aria_label": "Close dialog", "is_empty": False},
    ]
    buttons = await _extract_buttons(mock_page)
    assert len(buttons) == 3
    assert buttons[1].is_empty is True
    assert buttons[2].aria_label == "Close dialog"


@pytest.mark.asyncio
async def test_extract_links_separates_internal_external():
    mock_page = AsyncMock()
    mock_page.evaluate.return_value = [
        {"href": "/about", "text": "About"},
        {"href": "https://example.com/contact", "text": "Contact"},
        {"href": "https://external.com/page", "text": "External"},
        {"href": "#section", "text": "Skip"},           # fragment — skipped
        {"href": "mailto:a@b.com", "text": "Email"},    # mailto — skipped
    ]
    links, internal_urls = await _extract_links(mock_page, "https://example.com", "https://example.com")

    assert len(links) == 3
    internal = [lnk for lnk in links if lnk.is_internal]
    external = [lnk for lnk in links if not lnk.is_internal]
    assert len(internal) == 2
    assert len(external) == 1
    assert len(internal_urls) == 2


@pytest.mark.asyncio
async def test_extract_links_deduplicates_internal():
    mock_page = AsyncMock()
    mock_page.evaluate.return_value = [
        {"href": "/about", "text": "About"},
        {"href": "/about", "text": "About Us"},  # duplicate
    ]
    links, internal_urls = await _extract_links(mock_page, "https://example.com", "https://example.com")
    assert len(internal_urls) == 1


# ---------------------------------------------------------------------------
# PlaywrightEngine.get_page_content
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_page_content_returns_page_content_on_success():
    engine = PlaywrightEngine()

    mock_page = AsyncMock()
    mock_page.title.return_value = "Home Page"
    mock_page.content.return_value = "<html><body>Hello</body></html>"
    mock_page.is_closed.return_value = False
    mock_page.evaluate.return_value = []

    mock_response = MagicMock()
    mock_response.status = 200
    mock_page.goto.return_value = mock_response

    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page
    engine._context = mock_context

    content = await engine.get_page_content("https://example.com")

    assert content.url == "https://example.com"
    assert content.title == "Home Page"
    assert content.status_code == 200
    assert content.error is None


@pytest.mark.asyncio
async def test_get_page_content_captures_timeout_as_error():
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError

    engine = PlaywrightEngine()

    mock_page = AsyncMock()
    mock_page.goto.side_effect = PlaywrightTimeoutError("Timeout")
    mock_page.is_closed.return_value = False

    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page
    engine._context = mock_context

    content = await engine.get_page_content("https://slow-site.com")

    assert content.error is not None
    assert "Timeout" in content.error
    assert content.html == ""


@pytest.mark.asyncio
async def test_get_page_content_captures_generic_error():
    engine = PlaywrightEngine()

    mock_page = AsyncMock()
    mock_page.goto.side_effect = Exception("net::ERR_NAME_NOT_RESOLVED")
    mock_page.is_closed.return_value = False

    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page
    engine._context = mock_context

    content = await engine.get_page_content("https://nonexistent-domain-xyz.com")

    assert content.error is not None
    assert content.html == ""
