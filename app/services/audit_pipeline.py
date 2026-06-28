from __future__ import annotations

import uuid
import traceback

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AuditStatus
from app.db.session import AsyncSessionLocal
from app.repositories.audit_repo import AuditRepository
from app.repositories.project_repo import ProjectRepository
from app.services.ai_engine_service import AIEngineService
from app.services.crawler_service import CrawlerService
from app.services.reporter_service import ReporterService
from app.services.scan_persistence_service import ScanPersistenceService
from app.services.scanner_service import ScannerService

logger = structlog.get_logger(__name__)


async def run_audit_pipeline(audit_id: uuid.UUID, target_url: str, max_pages: int) -> None:
    """
    Full 7-step accessibility audit pipeline.
    Runs as a FastAPI BackgroundTask with its own DB session.

    Steps:
        1. Mark audit RUNNING
        2. Crawl website
        3. Save pages to DB
        4. Run axe-core accessibility scan
        5. Save violations to DB
        6. Enrich violations with AI explanations
        7. Calculate accessibility score + build report
        8. Mark audit COMPLETED (or FAILED on error)
    """
    logger.info("Pipeline started", audit_id=str(audit_id), url=target_url)

    try:
        async with AsyncSessionLocal() as db:
            try:
                await _step_1_mark_running(db, audit_id)

                crawled_pages = await _step_2_crawl(target_url, max_pages)

                scan_results = await _step_4_scan(crawled_pages)

                await _step_3_and_5_persist(db, audit_id, scan_results)

                await _step_6_explain(db, audit_id)

                await _step_7_build_report(db, audit_id)

                await _step_8_mark_completed(db, audit_id)
                await db.commit()

                logger.info("Pipeline completed", audit_id=str(audit_id))

            except Exception as exc:
                traceback.print_exc()
                logger.error("Pipeline failed", audit_id=str(audit_id), error=str(exc), exc_info=True)
                await db.rollback()
                await _mark_failed(audit_id, error=str(exc))
    except Exception as exc:
        traceback.print_exc()
        logger.error("Pipeline failed at session creation", audit_id=str(audit_id), error=str(exc), exc_info=True)
        await _mark_failed(audit_id, error=f"Session creation failed: {exc}")


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------

async def _step_1_mark_running(db: AsyncSession, audit_id: uuid.UUID) -> None:
    repo = AuditRepository(db)
    audit = await repo.get_by_id(audit_id)
    if not audit:
        raise RuntimeError(f"Audit {audit_id} not found at pipeline start")
    await repo.update_status(audit, AuditStatus.RUNNING)
    await db.flush()
    logger.info("Step 1: audit marked RUNNING", audit_id=str(audit_id))


async def _step_2_crawl(target_url: str, max_pages: int):
    logger.info("Step 2: crawling", url=target_url, max_pages=max_pages)
    crawler = CrawlerService()
    pages = await crawler.crawl(target_url, max_pages=max_pages)
    logger.info("Step 2: crawl complete", pages=len(pages))
    return pages


async def _step_4_scan(crawled_pages):
    logger.info("Step 4: scanning", pages=len(crawled_pages))
    scanner = ScannerService()
    results = await scanner.scan(crawled_pages)
    logger.info("Step 4: scan complete", results=len(results))
    return results


async def _step_3_and_5_persist(db: AsyncSession, audit_id: uuid.UUID, scan_results) -> None:
    """Steps 3 and 5 combined — pages and violations are persisted together per page."""
    logger.info("Steps 3+5: persisting pages and violations", audit_id=str(audit_id))
    persistence = ScanPersistenceService(db)
    summary = await persistence.persist(audit_id, scan_results)
    logger.info("Steps 3+5: persistence complete", **summary)


async def _step_6_explain(db: AsyncSession, audit_id: uuid.UUID) -> None:
    """Step 6: enrich violations with AI-generated plain English explanations and fixes."""
    logger.info("Step 6: AI explanation enrichment", audit_id=str(audit_id))
    ai_service = AIEngineService(db)
    count = await ai_service.explain_violations(audit_id)
    logger.info("Step 6: AI enrichment complete", audit_id=str(audit_id), violations_enriched=count)

    # Step 6b: Generate AI fixes for all violations (one fix per unique rule_id)
    logger.info("Step 6b: AI fix generation", audit_id=str(audit_id))
    fix_count = await ai_service.generate_fixes(audit_id)
    logger.info("Step 6b: AI fix generation complete", audit_id=str(audit_id), violations_fixed=fix_count)

    # Step 6c: Generate disability simulations for all violations (one simulation per unique rule_id)
    logger.info("Step 6c: AI simulation generation", audit_id=str(audit_id))
    sim_count = await ai_service.generate_simulations(audit_id)
    logger.info("Step 6c: AI simulation generation complete", audit_id=str(audit_id), violations_simulated=sim_count)

    await db.flush()


async def _step_7_build_report(db: AsyncSession, audit_id: uuid.UUID) -> None:
    logger.info("Step 7: building report", audit_id=str(audit_id))
    reporter = ReporterService(db)
    report = await reporter.build_report(audit_id)
    logger.info("Step 7: report built", score=report.accessibility_score, audit_id=str(audit_id))


async def _step_8_mark_completed(db: AsyncSession, audit_id: uuid.UUID) -> None:
    repo = AuditRepository(db)
    audit = await repo.get_by_id(audit_id)
    await repo.update_status(audit, AuditStatus.COMPLETED)
    logger.info("Step 8: audit marked COMPLETED", audit_id=str(audit_id))


async def _mark_failed(audit_id: uuid.UUID, error: str) -> None:
    """Opens a fresh session to mark the audit as FAILED after a pipeline error."""
    async with AsyncSessionLocal() as db:
        try:
            repo = AuditRepository(db)
            audit = await repo.get_by_id(audit_id)
            if audit:
                await repo.update_status(audit, AuditStatus.FAILED, error=error[:1000])
                await db.commit()
        except Exception as exc:
            logger.error("Failed to mark audit as FAILED", audit_id=str(audit_id), error=str(exc))
