from __future__ import annotations

import json
import uuid
from typing import Dict, List

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.llm import get_llm_client
from app.models.page import Page
from app.models.violation import Violation

logger = structlog.get_logger(__name__)


class FixGeneratorService:
    """
    Generates AI-powered remediation suggestions for accessibility violations.

    For each unique rule_id in an audit, a fix is generated once via the LLM
    provider (Ollama or OpenAI) and cached. All violations sharing that rule_id
    receive the same generated fix via a single batch UPDATE.

    The generated fix is a JSON object persisted in the violation's ai_fix column:
      {
        "problem": "...",
        "recommended_fix": "...",
        "code_example": "...",
        "implementation_steps": ["...", "..."],
        "priority": "critical|serious|moderate|minor"
      }
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_fixes_for_audit(self, audit_id: uuid.UUID) -> int:
        """
        Generates and persists AI fixes for all violations in the given audit.

        Process:
          1. Fetch all violations for the audit.
          2. Skip violations that already have an ai_fix.
          3. Group remaining violations by rule_id.
          4. For each unique rule_id, generate one fix via the LLM.
          5. Batch-update all violations in each group with the cached fix.
          6. Commit all changes.

        Returns the total number of violations updated with fixes.
        """
        violations = await self._get_violations(audit_id)
        logger.info(
            "Fix generation started",
            audit_id=str(audit_id),
            violation_count=len(violations),
        )

        if not violations:
            logger.info("No violations to generate fixes for", audit_id=str(audit_id))
            return 0

        # Skip violations that already have fixes
        to_fix = [v for v in violations if not v.ai_fix]
        already_fixed = len(violations) - len(to_fix)
        if not to_fix:
            logger.info(
                "All violations already have fixes",
                audit_id=str(audit_id),
                count=already_fixed,
            )
            return already_fixed

        # Group remaining violations by rule_id
        groups: Dict[str, List[Violation]] = {}
        for v in to_fix:
            groups.setdefault(v.rule_id, []).append(v)

        unique_rules = len(groups)
        logger.info(
            "Unique rules to generate fixes for",
            audit_id=str(audit_id),
            unique_rules=unique_rules,
            total_violations=len(to_fix),
        )

        client = await get_llm_client()
        fixed_count = already_fixed
        rule_cache: Dict[str, str] = {}  # rule_id -> JSON fix string

        for rule_id, group in groups.items():
            logger.info(
                "Generating fix for rule",
                audit_id=str(audit_id),
                rule_id=rule_id,
                occurrences=len(group),
            )

            try:
                # Build prompt from the first violation in the group
                sample = group[0]
                prompt = self._build_prompt(sample)

                logger.info(
                    "LLM fix request started",
                    rule_id=rule_id,
                    prompt_len=len(prompt),
                )

                fix = await client.generate_fix(prompt)

                logger.info(
                    "LLM fix request completed",
                    rule_id=rule_id,
                )

                # Convert to structured JSON for storage
                fix_dict = fix.to_dict()
                json_fix = json.dumps(fix_dict)

                # Cache for reuse across duplicates
                rule_cache[rule_id] = json_fix

                # Batch-update ALL violations in this group
                stmt = (
                    update(Violation)
                    .where(Violation.id.in_([v.id for v in group]))
                    .values(ai_fix=json_fix)
                )
                await self.db.execute(stmt)

                fixed_count += len(group)

                logger.info(
                    "Database update completed for rule",
                    rule_id=rule_id,
                    violations_updated=len(group),
                )

            except Exception as exc:
                logger.error(
                    "Failed to generate fix for rule",
                    rule_id=rule_id,
                    error=str(exc),
                    exc_info=True,
                )
                # Continue with remaining rules — don't fail the entire batch

        await self.db.flush()

        total_fixes_generated = len(rule_cache)
        logger.info(
            "Fix generation complete",
            audit_id=str(audit_id),
            total_violations=len(violations),
            fixed_count=fixed_count,
            unique_fixes_generated=total_fixes_generated,
        )

        return fixed_count

    async def get_fix_for_violation(
        self, violation_id: uuid.UUID
    ) -> dict | None:
        """
        Retrieves the stored AI fix for a single violation.
        Returns the parsed dict or None if not yet generated.
        """
        result = await self.db.execute(
            select(Violation).where(Violation.id == violation_id)
        )
        violation = result.scalar_one_or_none()
        if not violation or not violation.ai_fix:
            return None
        return self._parse_stored(violation.ai_fix)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

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
        Constructs a detailed prompt from a violation record
        so the LLM has full context to generate an accurate fix.
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
            "\nPlease analyze this accessibility violation and provide "
            "a structured remediation including the problem description, "
            "recommended fix, a code example, implementation steps, "
            "and a priority level."
        )

        return "\n".join(lines)

    @staticmethod
    def _parse_stored(raw: str) -> dict:
        """Safely parses the stored JSON fix, falling back to raw text."""
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {
                "problem": raw,
                "recommended_fix": "",
                "code_example": "",
                "implementation_steps": [],
                "priority": "moderate",
            }