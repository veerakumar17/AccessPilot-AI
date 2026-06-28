"""
Quick script to check which axe-core 4.9.1 rule IDs are valid.
Downloads the minified axe-core and extracts rule IDs from the source.
"""
import httpx
import re

r = httpx.get("https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")

# Try multiple patterns
patterns = [
    r'ruleId:"([a-z][a-z0-9-]+)"',
    r'id:"([a-z][a-z0-9-]+)"',
    r'"ruleId":\s*"([a-z][a-z0-9-]+)"',
    r"ruleId:'([a-z][a-z0-9-]+)'",
]

all_matches = set()
for p in patterns:
    matches = re.findall(p, r.text)
    all_matches.update(matches)

rules = sorted(all_matches)
print(f"Total unique axe-core 4.9.1 rules found: {len(rules)}")
print()

# Check the specific IDs from our _RULE_DISABILITY_MAP
check_ids = [
    "image-alt", "input-image-alt", "area-alt", "role-img-alt", "svg-img-alt",
    "object-alt", "frame-title", "document-title",
    "aria-label", "aria-labelledby", "aria-required-attr", "aria-valid-attr",
    "aria-valid-attr-value", "aria-hidden-focus", "aria-hidden-body", "aria-roles",
    "aria-allowed-attr",
    "label", "label-content-name-mismatch", "select-name", "autocomplete-valid",
    "button-name", "input-button-name",
    "color-contrast", "color-contrast-enhanced",
    "keyboard", "focus-visible", "tabindex", "scrollable-region-focusable",
    "skip-link", "bypass",
    "heading-order", "landmark-one-main", "region", "list", "listitem",
    "definition-list", "dlitem", "link-name",
    "duplicate-id-active", "duplicate-id-aria",
    "meta-viewport", "text-spacing", "reflow", "valid-lang",
    "html-lang-valid", "html-has-lang",
]

print("Checking specific IDs:")
print("-" * 50)
for rid in check_ids:
    status = "VALID" if rid in rules else "INVALID"
    print(f"  [{status}] {rid}")