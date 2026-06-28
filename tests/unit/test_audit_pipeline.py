import uuid
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from app.core.enums import AuditStatus
from app.services.audit_pipeline import (
    _mark_failed,
    _step_1_mark_running,
    _step_2_crawl,
    _step_4_scan,
    _step_6_build_report,
    _step_7_mark_completed,
    run_audit_pipeline,
)


AUDIT_ID = uuid.uuid4()
TARGET_URL = "https://example.com"


# ---------------------------------------------------------------------------
# Step 1 — mark RUNNING
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_step_1_marks_audit_running():
    db = AsyncMock()
    mock_audit = MagicMock()

    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = mock_audit

    with patch("app.services.audit_pipeline.AuditRepository", return_value=mock_repo):
        await _step_1_mark_running(db, AUDIT_ID)

    mock_repo.update_status.assert_called_once_with(mock_audit, AuditStatus.RUNNING)


@pytest.mark.asyncio
async def test_step_1_raises_if_audit_not_found():
    db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    with patch("app.services.audit_pipeline.AuditRepository", return_value=mock_repo):
        with pytest.raises(RuntimeError, match="not found"):
            await _step_1_mark_running(db, AUDIT_ID)


# ---------------------------------------------------------------------------
# Step 2 — crawl
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_step_2_calls_crawler_with_correct_args():
    mock_pages = [MagicMock(), MagicMock()]
    mock_crawler = AsyncMock()
    mock_crawler.crawl.return_value = mock_pages

    with patch("app.services.audit_pipeline.CrawlerService", return_value=mock_crawler):
        result = await _step_2_crawl(TARGET_URL, max_pages=10)

    mock_crawler.crawl.assert_called_once_with(TARGET_URL, max_pages=10)
    assert result == mock_pages


@pytest.mark.asyncio
async def test_step_2_returns_crawled_pages():
    mock_pages = [MagicMock() for _ in range(5)]
    mock_crawler = AsyncMock()
    mock_crawler.crawl.return_value = mock_pages

    with patch("app.services.audit_pipeline.CrawlerService", return_value=mock_crawler):
        result = await _step_2_crawl(TARGET_URL, max_pages=5)

    assert len(result) == 5


# ---------------------------------------------------------------------------
# Step 4 — scan
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_step_4_calls_scanner_with_pages():
    pages = [MagicMock()]
    mock_results = [MagicMock()]
    mock_scanner = AsyncMock()
    mock_scanner.scan.return_value = mock_results

    with patch("app.services.audit_pipeline.ScannerService", return_value=mock_scanner):
        result = await _step_4_scan(pages)

    mock_scanner.scan.assert_called_once_with(pages)
    assert result == mock_results


# ---------------------------------------------------------------------------
# Step 6 — build report
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_step_6_calls_build_report():
    db = AsyncMock()
    mock_report = MagicMock()
    mock_report.accessibility_score = 85.0
    mock_reporter = AsyncMock()
    mock_reporter.build_report.return_value = mock_report

    with patch("app.services.audit_pipeline.ReporterService", return_value=mock_reporter):
        await _step_6_build_report(db, AUDIT_ID)

    mock_reporter.build_report.assert_called_once_with(AUDIT_ID)


# ---------------------------------------------------------------------------
# Step 7 — mark COMPLETED
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_step_7_marks_audit_completed():
    db = AsyncMock()
    mock_audit = MagicMock()
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = mock_audit

    with patch("app.services.audit_pipeline.AuditRepository", return_value=mock_repo):
        await _step_7_mark_completed(db, AUDIT_ID)

    mock_repo.update_status.assert_called_once_with(mock_audit, AuditStatus.COMPLETED)


# ---------------------------------------------------------------------------
# _mark_failed
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mark_failed_updates_status_to_failed():
    mock_audit = MagicMock()
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = mock_audit

    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    with patch("app.services.audit_pipeline.AsyncSessionLocal", return_value=mock_session):
        with patch("app.services.audit_pipeline.AuditRepository", return_value=mock_repo):
            await _mark_failed(AUDIT_ID, error="Something went wrong")

    mock_repo.update_status.assert_called_once_with(mock_audit, AuditStatus.FAILED, error="Something went wrong")


@pytest.mark.asyncio
async def test_mark_failed_truncates_long_error_messages():
    mock_audit = MagicMock()
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = mock_audit

    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    long_error = "x" * 2000

    with patch("app.services.audit_pipeline.AsyncSessionLocal", return_value=mock_session):
        with patch("app.services.audit_pipeline.AuditRepository", return_value=mock_repo):
            await _mark_failed(AUDIT_ID, error=long_error)

    call_kwargs = mock_repo.update_status.call_args.kwargs
    assert len(call_kwargs["error"]) <= 1000


# ---------------------------------------------------------------------------
# run_audit_pipeline — full happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_audit_pipeline_executes_all_steps_in_order():
    mock_audit = MagicMock()
    mock_audit.id = AUDIT_ID

    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = mock_audit

    mock_pages = [MagicMock()]
    mock_crawler = AsyncMock()
    mock_crawler.crawl.return_value = mock_pages

    mock_scan_results = [MagicMock()]
    mock_scanner = AsyncMock()
    mock_scanner.scan.return_value = mock_scan_results

    mock_persistence = AsyncMock()
    mock_persistence.persist.return_value = {"pages_saved": 1, "total_violations": 2}

    mock_report = MagicMock()
    mock_report.accessibility_score = 80.0
    mock_reporter = AsyncMock()
    mock_reporter.build_report.return_value = mock_report

    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    with patch("app.services.audit_pipeline.AsyncSessionLocal", return_value=mock_session), \
         patch("app.services.audit_pipeline.AuditRepository", return_value=mock_repo), \
         patch("app.services.audit_pipeline.CrawlerService", return_value=mock_crawler), \
         patch("app.services.audit_pipeline.ScannerService", return_value=mock_scanner), \
         patch("app.services.audit_pipeline.ScanPersistenceService", return_value=mock_persistence), \
         patch("app.services.audit_pipeline.ReporterService", return_value=mock_reporter):

        await run_audit_pipeline(AUDIT_ID, TARGET_URL, max_pages=10)

    # Verify each step was called
    mock_crawler.crawl.assert_called_once_with(TARGET_URL, max_pages=10)
    mock_scanner.scan.assert_called_once_with(mock_pages)
    mock_persistence.persist.assert_called_once_with(AUDIT_ID, mock_scan_results)
    mock_reporter.build_report.assert_called_once_with(AUDIT_ID)

    # Step 1 (RUNNING) and step 7 (COMPLETED) status updates
    status_calls = [c.args[1] for c in mock_repo.update_status.call_args_list]
    assert AuditStatus.RUNNING in status_calls
    assert AuditStatus.COMPLETED in status_calls


@pytest.mark.asyncio
async def test_run_audit_pipeline_marks_failed_on_crawler_error():
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = MagicMock()

    mock_crawler = AsyncMock()
    mock_crawler.crawl.side_effect = Exception("DNS resolution failed")

    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    failed_session = AsyncMock()
    failed_session.__aenter__.return_value = failed_session
    failed_session.__aexit__.return_value = None

    failed_repo = AsyncMock()
    failed_repo.get_by_id.return_value = MagicMock()

    call_count = 0

    def session_factory():
        nonlocal call_count
        call_count += 1
        return mock_session if call_count == 1 else failed_session

    with patch("app.services.audit_pipeline.AsyncSessionLocal", side_effect=session_factory), \
         patch("app.services.audit_pipeline.AuditRepository", side_effect=[mock_repo, failed_repo]), \
         patch("app.services.audit_pipeline.CrawlerService", return_value=mock_crawler):

        await run_audit_pipeline(AUDIT_ID, TARGET_URL, max_pages=10)

    failed_repo.update_status.assert_called_once()
    call_args = failed_repo.update_status.call_args
    assert call_args.args[1] == AuditStatus.FAILED


@pytest.mark.asyncio
async def test_run_audit_pipeline_does_not_raise_on_failure():
    """Pipeline must never propagate exceptions — caller is BackgroundTasks."""
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    mock_repo = AsyncMock()
    mock_repo.get_by_id.side_effect = Exception("DB connection lost")

    with patch("app.services.audit_pipeline.AsyncSessionLocal", return_value=mock_session), \
         patch("app.services.audit_pipeline.AuditRepository", return_value=mock_repo):

        # Should not raise
        await run_audit_pipeline(AUDIT_ID, TARGET_URL, max_pages=5)
