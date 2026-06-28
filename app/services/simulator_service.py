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


class SimulatorService:
    """
    Generates AI-powered disability simulations for accessibility violations.

    For each unique rule_id in an audit, a simulation is generated once via the
    LLM provider (Ollama or OpenAI) and cached. All violations sharing that
    rule_id receive the same generated simulation via a single batch UPDATE.

    The generated simulation is a JSON object persisted in the violation's
    ai_simulation column:
      {
        "affected_groups": [
          {"disability": "blind", "impact": "..."},
          {"disability": "low_vision", "impact": "..."},
          {"disability": "motor", "impact": "..."},
          {"disability": "cognitive", "impact": "..."}
        ],
        "severity_explanation": "...",
        "user_experience": "..."
      }
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_simulations_for_audit(self, audit_id: uuid.UUID) -> int:
        """
        Generates and persists AI simulations for all violations in the given audit.

        Process:
          1. Fetch all violations for the audit.
          2. Skip violations that already have an ai_simulation.
          3. Group remaining violations by rule_id.
          4. For each unique rule_id, generate one simulation via the LLM.
          5. Batch-update all violations in each group with the cached simulation.
          6. Commit all changes.

        Returns the total number of violations updated with simulations.
        """
        logger.info(
            "Simulation generation started",
            audit_id=str(audit_id),
        )

        violations = await self._get_violations(audit_id)

        if not violations:
            logger.info("No violations to generate simulations for", audit_id=str(audit_id))
            return 0

        # Skip violations that already have simulations
        to_simulate = [v for v in violations if not v.ai_simulation]
        already_simulated = len(violations) - len(to_simulate)

        if not to_simulate:
            logger.info(
                "All violations already have simulations",
                audit_id=str(audit_id),
                count=already_simulated,
            )
            return already_simulated

        # Group remaining violations by rule_id
        groups: Dict[str, List[Violation]] = {}
        for v in to_simulate:
            groups.setdefault(v.rule_id, []).append(v)

        unique_rules = len(groups)
        logger.info(
            "Unique rule count",
            audit_id=str(audit_id),
            unique_rules=unique_rules,
            total_violations=len(to_simulate),
        )

        client = await get_llm_client()
        simulated_count = already_simulated
        rule_cache: Dict[str, str] = {}  # rule_id -> JSON simulation string

        for rule_id, group in groups.items():
            logger.info(
                "Generating simulation for rule",
                audit_id=str(audit_id),
                rule_id=rule_id,
                occurrences=len(group),
            )

            try:
                # Build prompt from the first violation in the group
                sample = group[0]
                prompt = self._build_prompt(sample)

                logger.info(
                    "LLM request started",
                    rule_id=rule_id,
                    prompt_len=len(prompt),
                )

                simulation = await client.generate_simulation(prompt)

                logger.info(
                    "LLM request completed",
                    rule_id=rule_id,
                )

                # Convert to structured JSON for storage
                sim_dict = simulation.to_dict()
                json_sim = json.dumps(sim_dict)

                # Cache for reuse across duplicates
                rule_cache[rule_id] = json_sim

                # Batch-update ALL violations in this group
                stmt = (
                    update(Violation)
                    .where(Violation.id.in_([v.id for v in group]))
                    .values(ai_simulation=json_sim)
                )
                result = await self.db.execute(stmt)

                simulated_count += len(group)

                logger.info(
                    "Database update completed",
                    rule_id=rule_id,
                    violations_updated=len(group),
                )

            except Exception as exc:
                logger.error(
                    "Failed to generate simulation for rule",
                    rule_id=rule_id,
                    error=str(exc),
                    exc_info=True,
                )
                # Continue with remaining rules — don't fail the entire batch

        await self.db.flush()

        total_simulations_generated = len(rule_cache)
        logger.info(
            "Simulation generation complete",
            audit_id=str(audit_id),
            total_violations=len(violations),
            simulated_count=simulated_count,
            unique_simulations_generated=total_simulations_generated,
        )

        return simulated_count

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
        so the LLM has full context to generate an accurate simulation.
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

        if violation.ai_explanation:
            lines.append(f"Explanation: {violation.ai_explanation}")

        lines.append(
            "\nPlease simulate how this accessibility violation affects users "
            "with different disabilities. Describe the specific impact on blind "
            "users, users with low vision, users with motor disabilities, and "
            "users with cognitive disabilities. Also provide a severity "
            "explanation and a step-by-step walkthrough of the user experience.\n\n"
            "Additionally, explain how this issue affects GENERAL users (users without "
            "disabilities) — focusing on overall usability, readability, navigation, "
            "efficiency, or user experience. Return the result under the key "
            "\"general_user_impact\" in the JSON response."
        )

        return "\n".join(lines)