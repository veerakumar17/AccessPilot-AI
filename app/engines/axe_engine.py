from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import httpx
import structlog
from playwright.async_api import Page

from app.core.enums import DisabilityType, ViolationSeverity

logger = structlog.get_logger(__name__)

AXE_CDN_URL = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js"

# axe impact → our severity
_IMPACT_MAP: dict[str, ViolationSeverity] = {
    "critical": ViolationSeverity.CRITICAL,
    "serious": ViolationSeverity.SERIOUS,
    "moderate": ViolationSeverity.MODERATE,
    "minor": ViolationSeverity.MINOR,
}

# axe rule → disability types affected
# NOTE: Only keys that are valid axe-core 4.9.1 rule IDs are listed here.
# Non-rule descriptors (e.g. "aria-label", "aria-labelledby", "aria-hidden-body")
# are NOT valid axe-core rules and must NOT be included.
_RULE_DISABILITY_MAP: dict[str, list[DisabilityType]] = {
    # Blind / screen reader
    "image-alt":              [DisabilityType.BLIND],
    "input-image-alt":        [DisabilityType.BLIND],
    "area-alt":               [DisabilityType.BLIND],
    "role-img-alt":           [DisabilityType.BLIND],
    "svg-img-alt":            [DisabilityType.BLIND],
    "object-alt":             [DisabilityType.BLIND],
    "frame-title":            [DisabilityType.BLIND],
    "document-title":         [DisabilityType.BLIND],
    "aria-allowed-attr":      [DisabilityType.BLIND],
    "aria-required-attr":     [DisabilityType.BLIND],
    "aria-valid-attr":        [DisabilityType.BLIND],
    "aria-valid-attr-value":  [DisabilityType.BLIND],
    "aria-hidden-focus":      [DisabilityType.BLIND],
    "aria-roles":             [DisabilityType.BLIND],
    # Forms / labels
    "label":                  [DisabilityType.BLIND, DisabilityType.COGNITIVE],
    "select-name":            [DisabilityType.BLIND, DisabilityType.COGNITIVE],
    "autocomplete-valid":     [DisabilityType.COGNITIVE],
    # Buttons
    "button-name":            [DisabilityType.BLIND, DisabilityType.COGNITIVE],
    "input-button-name":      [DisabilityType.BLIND],
    # Color contrast
    "color-contrast":         [DisabilityType.COLOR_BLIND, DisabilityType.LOW_VISION],
    "color-contrast-enhanced": [DisabilityType.COLOR_BLIND, DisabilityType.LOW_VISION],
    # Keyboard
    "keyboard":               [DisabilityType.KEYBOARD],
    "focus-visible":          [DisabilityType.KEYBOARD],
    "tabindex":               [DisabilityType.KEYBOARD],
    "scrollable-region-focusable": [DisabilityType.KEYBOARD],
    "skip-link":              [DisabilityType.KEYBOARD],
    "bypass":                 [DisabilityType.KEYBOARD],
    # Semantic / cognitive
    "heading-order":          [DisabilityType.COGNITIVE, DisabilityType.BLIND],
    "landmark-one-main":      [DisabilityType.BLIND, DisabilityType.COGNITIVE],
    "region":                 [DisabilityType.BLIND],
    "list":                   [DisabilityType.BLIND],
    "listitem":               [DisabilityType.BLIND],
    "definition-list":        [DisabilityType.BLIND],
    "dlitem":                 [DisabilityType.BLIND],
    "link-name":              [DisabilityType.BLIND, DisabilityType.COGNITIVE],
    "duplicate-id-active":    [DisabilityType.BLIND],
    "duplicate-id-aria":      [DisabilityType.BLIND],
    # Low vision
    "meta-viewport":          [DisabilityType.LOW_VISION],
    "text-spacing":           [DisabilityType.LOW_VISION],
    "reflow":                 [DisabilityType.LOW_VISION],
    "valid-lang":             [DisabilityType.COGNITIVE],
    "html-has-lang":          [DisabilityType.COGNITIVE],
    "html-lang-valid":        [DisabilityType.COGNITIVE],
}

# axe rule → WCAG success criterion
_RULE_WCAG_MAP: dict[str, str] = {
    "image-alt":              "1.1.1",
    "input-image-alt":        "1.1.1",
    "area-alt":               "1.1.1",
    "color-contrast":         "1.4.3",
    "color-contrast-enhanced": "1.4.6",
    "label":                  "1.3.1",
    "button-name":            "4.1.2",
    "keyboard":               "2.1.1",
    "focus-visible":          "2.4.7",
    "bypass":                 "2.4.1",
    "document-title":         "2.4.2",
    "link-name":              "2.4.4",
    "heading-order":          "1.3.1",
    "html-has-lang":          "3.1.1",
    "html-lang-valid":        "3.1.1",
    "valid-lang":             "3.1.2",
    "meta-viewport":          "1.4.4",
    "tabindex":               "2.4.3",
    "aria-required-attr":     "4.1.2",
    "aria-valid-attr":        "4.1.2",
    "aria-roles":             "4.1.2",
    "frame-title":            "2.4.1",
    "select-name":            "1.3.1",
    "skip-link":              "2.4.1",
    "landmark-one-main":      "1.3.6",
}

# axe-core rules to run during the audit.
# Set to None to run ALL axe-core rules (full scan).
_TARGET_RULES = None


@dataclass
class AxeViolation:
    rule_id: str
    severity: ViolationSeverity
    description: str
    help_url: str
    html_snippet: str
    selector: str
    wcag_criteria: str | None
    disability_types: list[str]
    impact: str | None


class AxeEngine:
    """
    Injects axe-core into a live Playwright page, runs the audit,
    and returns a flat list of AxeViolation dataclasses.
    """

    def __init__(self):
        self._axe_script: str | None = None
        self._script_lock = asyncio.Lock()

    async def get_axe_script(self) -> str:
        """Fetches axe-core script from CDN once and caches it in memory."""
        async with self._script_lock:
            if self._axe_script is None:
                logger.info("Fetching axe-core script", url=AXE_CDN_URL)
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(AXE_CDN_URL)
                    response.raise_for_status()
                    self._axe_script = response.text
                    logger.info("axe-core script cached", size_bytes=len(self._axe_script))
        return self._axe_script

    async def run(self, page: Page, page_url: str) -> list[AxeViolation]:
        """
        Injects axe-core into the page, runs the audit scoped to target rules,
        and returns parsed violations. Never raises — errors are logged and
        an empty list is returned.
        """
        try:
            axe_script = await self.get_axe_script()
            await page.evaluate(axe_script)

            raw_results: dict[str, Any] = await page.evaluate(
                """(rules) => {
                    const opts = {
                        resultTypes: ['violations'],
                        elementRef: false
                    };
                    if (rules !== null) {
                        opts.runOnly = { type: 'rule', values: rules };
                    }
                    return axe.run(document, opts)
                        .then(r => ({ violations: r.violations }));
                }""",
                _TARGET_RULES,
            )

            violations = self.parse_violations(raw_results.get("violations", []))
            logger.info("axe scan complete", url=page_url, violations=len(violations))
            return violations

        except Exception as exc:
            logger.error("axe scan failed", url=page_url, error=str(exc))
            return []

    def parse_violations(self, raw_violations: list[dict]) -> list[AxeViolation]:
        """
        Flattens axe violations (each with multiple nodes) into individual
        AxeViolation records — one per DOM node instance.
        """
        results: list[AxeViolation] = []

        for violation in raw_violations:
            rule_id: str = violation.get("id", "unknown")
            impact: str | None = violation.get("impact")
            description: str = violation.get("description", "")
            help_url: str = violation.get("helpUrl", "")
            severity = _IMPACT_MAP.get(impact or "", ViolationSeverity.MINOR)
            wcag_criteria = _get_wcag(violation, rule_id)
            disability_types = [d.value for d in _RULE_DISABILITY_MAP.get(rule_id, [])]

            nodes: list[dict] = violation.get("nodes", [])

            if not nodes:
                # Violation exists but no specific nodes — record once with empty context
                results.append(AxeViolation(
                    rule_id=rule_id,
                    severity=severity,
                    description=description,
                    help_url=help_url,
                    html_snippet="",
                    selector="",
                    wcag_criteria=wcag_criteria,
                    disability_types=disability_types,
                    impact=impact,
                ))
                continue

            for node in nodes:
                html_snippet = node.get("html", "")
                selector = _extract_selector(node)

                results.append(AxeViolation(
                    rule_id=rule_id,
                    severity=severity,
                    description=description,
                    help_url=help_url,
                    html_snippet=html_snippet,
                    selector=selector,
                    wcag_criteria=wcag_criteria,
                    disability_types=disability_types,
                    impact=impact,
                ))

        return results


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _extract_selector(node: dict) -> str:
    """Extracts the most specific CSS selector from an axe node."""
    target = node.get("target", [])
    if not target:
        return ""
    # target is a list of selectors (for shadow DOM it can be nested lists)
    # We join the outermost list with " > " for specificity
    parts = []
    for item in target:
        if isinstance(item, list):
            parts.append(" > ".join(item))
        else:
            parts.append(str(item))
    return ", ".join(parts)


def _get_wcag(violation: dict, rule_id: str) -> str | None:
    """Extracts WCAG criterion from axe tags, falls back to our static map."""
    tags: list[str] = violation.get("tags", [])
    for tag in tags:
        if tag.startswith("wcag") and tag[4:].replace("_", ".").replace("a", "").replace("A", "").strip():
            # e.g. "wcag143" → "1.4.3"
            digits = tag[4:]
            if digits.isdigit() and len(digits) >= 3:
                return f"{digits[0]}.{digits[1]}.{digits[2:]}"
    return _RULE_WCAG_MAP.get(rule_id)