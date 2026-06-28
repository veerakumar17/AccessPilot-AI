from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.enums import ViolationSeverity
from app.engines.axe_engine import AxeViolation
from app.services.crawler_service import CrawledPage
from app.services.scanner_service import ScanResult, ScannerService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_axe_violation(
    rule_id: str = "image-alt",
    severity: ViolationSeverity = ViolationSeverity.CRITICAL,
    description: str = "Images must have alt text",
    selector: str = "img.hero",
    html_snippet: str = '<img src="hero.jpg">',
    wcag_criteria: str = "1.1.1",
    disability_types: list[str] | None = None,
) -> AxeViolation:
    return AxeViolation(
        rule_id=rule_id,
        severity=severity,
        description=description,
        help_url="https://dequeuniversity.com/rules/axe/image-alt",
        html_snippet=html_snippet,
        selector=selector,
        wcag_criteria=wcag_criteria,
        disability_types=disability_types or ["blind"],
        impact="critical",
    )


def make_crawled_page(url: str = "https://example.com", title: str = "Home") -> CrawledPage:
    return CrawledPage(url=url, title=title, html="<html/>")


def make_mock_axe(violations: list[AxeViolation] | None = None) -> AsyncMock:
    mock = AsyncMock()
    mock.run.return_value = violations or []
    return mock


# ---------------------------------------------------------------------------
# ScanResult helpers
# ---------------------------------------------------------------------------

def test_scan_result_violation_count():
    result = ScanResult(
        page_url="https://example.com",
        page_title="Home",
        violations=[make_axe_violation(), make_axe_violation()],
    )
    assert result.violation_count == 2


def test_scan_result_violation_count_zero_when_no_violations():
    result = ScanResult(page_url="https://example.com", page_title="Home")
    assert result.violation_count == 0


def test_scan_result_violations_by_severity_groups_correctly():
    result = ScanResult(
        page_url="https://example.com",
        page_title="Home",
        violations=[
            make_axe_violation(severity=ViolationSeverity.CRITICAL),
            make_axe_violation(severity=ViolationSeverity.CRITICAL),
            make_axe_violation(severity=ViolationSeverity.MODERATE),
        ],
    )
    grouped = result.violations_by_severity()
    assert len(grouped["critical"]) == 2
    assert len(grouped["moderate"]) == 1


def test_scan_result_to_dict_structure():
    violation = make_axe_violation()
    result = ScanResult(
        page_url="https://example.com",
        page_title="Home",
        violations=[violation],
    )
    d = result.to_dict()
    assert d["page_url"] == "https://example.com"
    assert d["violation_count"] == 1
    assert d["violations"][0]["rule_id"] == "image-alt"
    assert d["violations"][0]["severity"] == "critical"
    assert d["violations"][0]["wcag_criteria"] == "1.1.1"
    assert d["violations"][0]["disability_types"] == ["blind"]


def test_scan_result_to_dict_with_error():
    result = ScanResult(
        page_url="https://example.com",
        page_title=None,
        scan_error="Timeout",
    )
    d = result.to_dict()
    assert d["scan_error"] == "Timeout"
    assert d["violation_count"] == 0


# ---------------------------------------------------------------------------
# ScannerService.scan
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scan_returns_empty_list_for_empty_pages():
    service = ScannerService()
    results = await service.scan([])
    assert results == []


@pytest.mark.asyncio
async def test_scan_returns_one_result_per_page():
    pages = [
        make_crawled_page("https://example.com"),
        make_crawled_page("https://example.com/about"),
    ]
    mock_axe = make_mock_axe([make_axe_violation()])

    with patch("app.services.scanner_service.async_playwright") as mock_pw_cls:
        mock_pw = _build_mock_playwright(violation_count=1)
        mock_pw_cls.return_value.__aenter__.return_value = mock_pw

        service = ScannerService(axe_engine=mock_axe)
        results = await service.scan(pages)

    assert len(results) == 2


@pytest.mark.asyncio
async def test_scan_captures_page_error_without_raising():
    pages = [make_crawled_page("https://example.com")]

    with patch("app.services.scanner_service.async_playwright") as mock_pw_cls:
        mock_pw = _build_mock_playwright(raise_on_goto=True)
        mock_pw_cls.return_value.__aenter__.return_value = mock_pw

        service = ScannerService(axe_engine=make_mock_axe())
        results = await service.scan(pages)

    assert len(results) == 1
    assert results[0].scan_error is not None
    assert results[0].violation_count == 0


@pytest.mark.asyncio
async def test_scan_violations_populated_from_axe():
    pages = [make_crawled_page()]
    violations = [make_axe_violation("image-alt"), make_axe_violation("color-contrast")]
    mock_axe = make_mock_axe(violations)

    with patch("app.services.scanner_service.async_playwright") as mock_pw_cls:
        mock_pw = _build_mock_playwright()
        mock_pw_cls.return_value.__aenter__.return_value = mock_pw

        service = ScannerService(axe_engine=mock_axe)
        results = await service.scan(pages)

    assert results[0].violation_count == 2
    rule_ids = [v.rule_id for v in results[0].violations]
    assert "image-alt" in rule_ids
    assert "color-contrast" in rule_ids


@pytest.mark.asyncio
async def test_scan_page_title_carried_over():
    pages = [make_crawled_page("https://example.com", title="My Homepage")]
    mock_axe = make_mock_axe()

    with patch("app.services.scanner_service.async_playwright") as mock_pw_cls:
        mock_pw = _build_mock_playwright()
        mock_pw_cls.return_value.__aenter__.return_value = mock_pw

        service = ScannerService(axe_engine=mock_axe)
        results = await service.scan(pages)

    assert results[0].page_title == "My Homepage"


# ---------------------------------------------------------------------------
# ScannerService.scan_single
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scan_single_returns_scan_result():
    mock_axe = make_mock_axe([make_axe_violation()])

    with patch("app.services.scanner_service.async_playwright") as mock_pw_cls:
        mock_pw = _build_mock_playwright()
        mock_pw_cls.return_value.__aenter__.return_value = mock_pw

        service = ScannerService(axe_engine=mock_axe)
        result = await service.scan_single("https://example.com", "Home")

    assert isinstance(result, ScanResult)
    assert result.page_url == "https://example.com"


# ---------------------------------------------------------------------------
# Mock builder
# ---------------------------------------------------------------------------

def _build_mock_playwright(violation_count: int = 0, raise_on_goto: bool = False) -> MagicMock:
    """Builds a mock async_playwright context with browser, context, and page."""
    mock_page = AsyncMock()
    mock_page.is_closed.return_value = False

    if raise_on_goto:
        mock_page.goto.side_effect = Exception("net::ERR_NAME_NOT_RESOLVED")
    else:
        mock_page.goto.return_value = MagicMock(status=200)
        mock_page.wait_for_load_state.return_value = None

    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page

    mock_browser = AsyncMock()
    mock_browser.new_context.return_value = mock_context

    mock_pw = AsyncMock()
    mock_pw.chromium.launch.return_value = mock_browser

    return mock_pw
