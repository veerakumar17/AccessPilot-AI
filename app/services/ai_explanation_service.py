from __future__ import annotations

import json
import uuid
from typing import List

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.llm import get_llm_client
from app.models.page import Page
from app.models.violation import Violation

logger = structlog.get_logger(__name__)


class AIExplanationService:
    """
    Enriches accessibility violations with AI-generated explanations.

    For each violation in an audit, constructs a prompt describing the issue
    (rule ID, HTML snippet, WCAG criterion, affected disability types) and
    calls the OpenAI client to generate:
      - plain_english   -> human-readable explanation
      - business_impact  -> how this affects real users
      - recommendation   -> actionable fix advice

    Results are persisted back to the violation record's ai_explanation field
    as a JSON string for forward compatibility with the frontend.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def enrich_audit_violations(self, audit_id: uuid.UUID) -> int:
        """
        Fetches all violations for the given audit and enriches them
        with AI-generated explanations.
        
        Optimisation: generates ONE explanation per unique rule_id, then
        reuses the cached result for all violations with the same rule_id.
        This reduces 66 sequential LLM calls down to ~10-15.
        """
        violations = await self._get_violations(audit_id)
        logger.info("AI enrichment entry", audit_id=str(audit_id), violations_found=len(violations))

        if not violations:
            return 0

        # Skip violations that already have explanations
        to_enrich = [v for v in violations if not v.ai_explanation]
        already_enriched = len(violations) - len(to_enrich)
        if not to_enrich:
            return already_enriched

        # Group remaining violations by rule_id
        groups: dict[str, list[Violation]] = {}
        for v in to_enrich:
            groups.setdefault(v.rule_id, []).append(v)

        logger.info(
            "AI enrichment grouped by rule_id",
            audit_id=str(audit_id),
            unique_rules=len(groups),
            total_violations=len(to_enrich),
        )

        client = await get_llm_client()
        enriched_count = already_enriched
        rule_cache: dict[str, str] = {}  # rule_id -> JSON explanation string

        for rule_id, group in groups.items():
            try:
                # Build prompt from the FIRST violation in the group
                # (all share the same rule_id)
                sample = group[0]
                prompt = self._build_prompt(sample)
                logger.info(
                    "Calling LLM for rule",
                    rule_id=rule_id,
                    prompt_len=len(prompt),
                    occurrences=len(group),
                )

                explanation = await client.generate_explanation(prompt)

                # Map to structured JSON
                structured = {
                    "plain_english": explanation.explanation,
                    "business_impact": explanation.affected_users,
                    "recommendation": explanation.why_it_matters,
                }
                json_explanation = json.dumps(structured)

                # Cache for reuse
                rule_cache[rule_id] = json_explanation

                # Update ALL violations in this group with the same explanation
                stmt = (
                    update(Violation)
                    .where(Violation.id.in_([v.id for v in group]))
                    .values(ai_explanation=json_explanation)
                )
                await self.db.execute(stmt)

                enriched_count += len(group)
                logger.info(
                    "Rule enriched",
                    rule_id=rule_id,
                    violations_updated=len(group),
                )

            except Exception as exc:
                import traceback
                traceback.print_exc()
                logger.error(
                    "Failed to enrich rule",
                    rule_id=rule_id,
                    error=str(exc),
                    exc_info=True,
                )
                # Continue with remaining rules — don't fail the entire batch

        await self.db.flush()
        logger.info(
            "AI enrichment complete",
            audit_id=str(audit_id),
            total=len(violations),
            enriched=enriched_count,
            unique_rules_generated=len(rule_cache),
        )
        return enriched_count

    async def get_explanation_for_violation(
        self, violation_id: uuid.UUID
    ) -> dict | None:
        """
        Retrieves the stored AI explanation for a single violation.
        Returns the parsed dict or None if not enriched yet.
        """
        result = await self.db.execute(
            select(Violation).where(Violation.id == violation_id)
        )
        violation = result.scalar_one_or_none()
        if not violation or not violation.ai_explanation:
            return None
        return self._parse_stored(violation.ai_explanation)

    # ---------------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------------

    async def _get_violations(self, audit_id: uuid.UUID) -> List[Violation]:
        """Fetch all violations for an audit, ordered by page and rule."""
        result = await self.db.execute(
            select(Violation)
            .join(Page, Page.id == Violation.page_id)
            .where(Page.audit_id == audit_id)
            .order_by(Page.url, Violation.rule_id)
        )
        return list(result.scalars().all())

    def _build_prompt(self, violation: Violation) -> str:
        """
        Constructs a detailed user prompt from a violation record
        so the AI has full context to generate an accurate explanation.
        """
        lines = [
            f"Accessibility Violation: {violation.rule_id}",
            f"Severity: {violation.severity.value}",
        ]

        if violation.wcag_criteria:
            lines.append(f"WCAG Criterion: {violation.wcag_criteria}")

        if violation.html_snippet:
            lines.append(f"HTML:\n{violation.html_snippet}")

        if violation.selector:
            lines.append(f"CSS Selector: {violation.selector}")

        if violation.disability_types:
            types = ", ".join(violation.disability_types)
            lines.append(f"Affects: {types}")

        lines.append(
            "\nPlease explain this issue in plain English, describe the "
            "business impact, and provide a clear recommendation."
        )

        return "\n".join(lines)

    @staticmethod
    def _parse_stored(raw: str) -> dict:
        """Safely parses the stored JSON explanation, falling back to raw text."""
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {"plain_english": raw, "business_impact": "", "recommendation": ""}