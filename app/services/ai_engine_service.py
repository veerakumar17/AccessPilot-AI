import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_explanation_service import AIExplanationService
from app.services.fix_generator_service import FixGeneratorService
from app.services.simulator_service import SimulatorService

logger = structlog.get_logger(__name__)


class AIEngineService:
    """
    High-level service that orchestrates AI enrichment of accessibility violations.

    Delegates to AIExplanationService for per-violation explanation generation,
    to FixGeneratorService for per-rule remediation suggestion generation,
    and to SimulatorService for per-rule disability simulation generation.
    This wrapper exists to maintain backward compatibility with existing imports
    and to provide a single entry point for all AI-related operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def explain_violations(self, audit_id: uuid.UUID) -> int:
        """
        Enriches all violations for the given audit with AI-generated explanations.

        Returns the count of violations successfully enriched.
        Delegates to AIExplanationService.
        """
        logger.info("AI explanation started", audit_id=str(audit_id))
        service = AIExplanationService(self.db)
        return await service.enrich_audit_violations(audit_id)

    async def generate_fixes(self, audit_id: uuid.UUID) -> int:
        """
        Generates AI-powered remediation suggestions for all violations
        in the given audit. Fixes are generated once per unique rule_id
        and batch-applied to all matching violations.

        Returns the count of violations updated with fixes.
        Delegates to FixGeneratorService.
        """
        logger.info("AI fix generation started", audit_id=str(audit_id))
        service = FixGeneratorService(self.db)
        return await service.generate_fixes_for_audit(audit_id)

    async def generate_simulations(self, audit_id: uuid.UUID) -> int:
        """
        Generates AI-powered disability simulations for all violations
        in the given audit. Simulations are generated once per unique
        rule_id and batch-applied to all matching violations.

        Returns the count of violations updated with simulations.
        Delegates to SimulatorService.
        """
        logger.info("AI simulation generation started", audit_id=str(audit_id))
        service = SimulatorService(self.db)
        return await service.generate_simulations_for_audit(audit_id)
