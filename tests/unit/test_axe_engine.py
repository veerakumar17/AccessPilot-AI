from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.enums import DisabilityType, ViolationSeverity
from app.engines.axe_engine import (
    AxeEngine,
    AxeViolation,
    _extract_selector,
    _get_wcag,
    _IMPACT_MAP,
    _RULE_DISABILITY_MAP,
)


# ---------------------------------------------------------------------------
# _extract_selector
# ---------------------------------------------------------------------------

def test_extract_selector_simple():
    node = {"target": ["#main-nav > a.skip-link"]}
    assert _extract_selector(node) == "#main-nav > a.skip-link"


def test_extract_selector_multiple_targets():
    node = {"target": ["#form1 input", "#form2 input"]}
    assert _extract_selector(node) == "#form1 input, #form2 input"


def test_extract_selector_nested_shadow_dom():
    node = {"target": [["custom-element", "button"]]}
    assert _extract_selector(node) == "custom-element > button"


def test_extract_selector_empty_target():
    assert _extract_selector({"target": []}) == ""
    assert _extract_selector({}) == ""


# ---------------------------------------------------------------------------
# _get_wcag
# ---------------------------------------------------------------------------

def test_get_wcag_from_tags():
    violation = {"tags": ["wcag2a", "wcag143", "best-practice"]}
    result = _get_wcag(violation, "color-contrast")
    assert result == "1.4.3"


def test_get_wcag_falls_back_to_static_map():
    violation = {"tags": ["best-practice"]}
    result = _get_wcag(violation, "image-alt")
    assert result == "1.1.1"


def test_get_wcag_returns_none_for_unknown_rule():
    violation = {"tags": []}
    result = _get_wcag(violation, "some-unknown-rule")
    assert result is None


# ---------------------------------------------------------------------------
# _IMPACT_MAP
# ---------------------------------------------------------------------------

def test_impact_map_covers_all_severities():
    assert _IMPACT_MAP["critical"] == ViolationSeverity.CRITICAL
    assert _IMPACT_MAP["serious"] == ViolationSeverity.SERIOUS
    assert _IMPACT_MAP["moderate"] == ViolationSeverity.MODERATE
    assert _IMPACT_MAP["minor"] == ViolationSeverity.MINOR


# ---------------------------------------------------------------------------
# _RULE_DISABILITY_MAP
# ---------------------------------------------------------------------------

def test_image_alt_maps_to_blind():
    assert DisabilityType.BLIND in _RULE_DISABILITY_MAP["image-alt"]


def test_color_contrast_maps_to_color_blind_and_low_vision():
    types = _RULE_DISABILITY_MAP["color-contrast"]
    assert DisabilityType.COLOR_BLIND in types
    assert DisabilityType.LOW_VISION in types


def test_keyboard_maps_to_keyboard():
    assert DisabilityType.KEYBOARD in _RULE_DISABILITY_MAP["keyboard"]


def test_label_maps_to_blind_and_cognitive():
    types = _RULE_DISABILITY_MAP["label"]
    assert DisabilityType.BLIND in types
    assert DisabilityType.COGNITIVE in types


# ---------------------------------------------------------------------------
# AxeEngine.parse_violations
# ---------------------------------------------------------------------------

def make_raw_violation(
    rule_id="image-alt",
    impact="critical",
    description="Images must have alt text",
    tags=["wcag2a", "wcag111"],
    nodes=None,
) -> dict:
    return {
        "id": rule_id,
        "impact": impact,
        "description": description,
        "helpUrl": f"https://dequeuniversity.com/rules/axe/{rule_id}",
        "tags": tags,
        "nodes": nodes or [
            {
                "html": '<img src="hero.jpg">',
                "target": ["img.hero"],
                "any": [],
                "all": [],
                "none": [],
            }
        ],
    }


def test_parse_violations_returns_one_record_per_node():
    engine = AxeEngine()
    raw = [make_raw_violation(nodes=[
        {"html": "<img src='a.jpg'>", "target": ["img:nth-child(1)"]},
        {"html": "<img src='b.jpg'>", "target": ["img:nth-child(2)"]},
    ])]
    results = engine.parse_violations(raw)
    assert len(results) == 2


def test_parse_violations_severity_mapped_correctly():
    engine = AxeEngine()
    raw = [make_raw_violation(impact="serious")]
    results = engine.parse_violations(raw)
    assert results[0].severity == ViolationSeverity.SERIOUS


def test_parse_violations_unknown_impact_defaults_to_minor():
    engine = AxeEngine()
    raw = [make_raw_violation(impact="unknown_level")]
    results = engine.parse_violations(raw)
    assert results[0].severity == ViolationSeverity.MINOR


def test_parse_violations_disability_types_populated():
    engine = AxeEngine()
    raw = [make_raw_violation(rule_id="image-alt")]
    results = engine.parse_violations(raw)
    assert "blind" in results[0].disability_types


def test_parse_violations_color_contrast_disability_types():
    engine = AxeEngine()
    raw = [make_raw_violation(rule_id="color-contrast", impact="serious")]
    results = engine.parse_violations(raw)
    assert "color_blind" in results[0].disability_types
    assert "low_vision" in results[0].disability_types


def test_parse_violations_wcag_extracted_from_tags():
    engine = AxeEngine()
    raw = [make_raw_violation(rule_id="image-alt", tags=["wcag2a", "wcag111"])]
    results = engine.parse_violations(raw)
    assert results[0].wcag_criteria == "1.1.1"


def test_parse_violations_selector_extracted():
    engine = AxeEngine()
    raw = [make_raw_violation(nodes=[{"html": "<img>", "target": ["#hero img"]}])]
    results = engine.parse_violations(raw)
    assert results[0].selector == "#hero img"


def test_parse_violations_no_nodes_creates_one_record():
    engine = AxeEngine()
    raw = [make_raw_violation(nodes=[])]
    results = engine.parse_violations(raw)
    assert len(results) == 1
    assert results[0].html_snippet == ""
    assert results[0].selector == ""


def test_parse_violations_empty_input():
    engine = AxeEngine()
    assert engine.parse_violations([]) == []


def test_parse_violations_html_snippet_captured():
    engine = AxeEngine()
    raw = [make_raw_violation(nodes=[{"html": '<button></button>', "target": ["button.cta"]}])]
    results = engine.parse_violations(raw)
    assert results[0].html_snippet == "<button></button>"


# ---------------------------------------------------------------------------
# AxeEngine.get_axe_script — caching
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_axe_script_cached_after_first_call():
    engine = AxeEngine()
    mock_response = MagicMock()
    mock_response.text = "/* axe-core */"
    mock_response.raise_for_status = MagicMock()

    with patch("app.engines.axe_engine.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        script1 = await engine.get_axe_script()
        script2 = await engine.get_axe_script()

    assert script1 == "/* axe-core */"
    assert script2 == "/* axe-core */"
    # Only one HTTP call despite two invocations
    assert mock_client.get.call_count == 1


# ---------------------------------------------------------------------------
# AxeEngine.run — success and error paths
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_returns_parsed_violations_on_success():
    engine = AxeEngine()
    engine._axe_script = "/* axe-core */"  # bypass HTTP fetch

    mock_page = AsyncMock()
    mock_page.evaluate.side_effect = [
        None,  # script injection
        {"violations": [make_raw_violation()]},  # axe.run()
    ]

    results = await engine.run(mock_page, "https://example.com")
    assert len(results) == 1
    assert isinstance(results[0], AxeViolation)


@pytest.mark.asyncio
async def test_run_returns_empty_list_on_exception():
    engine = AxeEngine()
    engine._axe_script = "/* axe-core */"

    mock_page = AsyncMock()
    mock_page.evaluate.side_effect = Exception("JS execution error")

    results = await engine.run(mock_page, "https://example.com")
    assert results == []


@pytest.mark.asyncio
async def test_run_returns_empty_list_when_no_violations():
    engine = AxeEngine()
    engine._axe_script = "/* axe-core */"

    mock_page = AsyncMock()
    mock_page.evaluate.side_effect = [None, {"violations": []}]

    results = await engine.run(mock_page, "https://example.com")
    assert results == []
