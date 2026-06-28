from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.enums import ViolationSeverity
from app.services.reporter_service import (
    _MAX_PENALTY,
    _SEVERITY_WEIGHTS,
    _build_summary_text,
    _calculate_score,
    _count_by_severity,
    _score_to_grade,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_violation(severity: ViolationSeverity) -> MagicMock:
    v = MagicMock()
    v.severity = severity
    return v


def make_violations(*severities: ViolationSeverity) -> list:
    return [make_violation(s) for s in severities]


# ---------------------------------------------------------------------------
# _calculate_score
# ---------------------------------------------------------------------------

def test_score_is_100_with_no_violations():
    assert _calculate_score([]) == 100.0


def test_score_decreases_with_violations():
    violations = make_violations(ViolationSeverity.CRITICAL)
    score = _calculate_score(violations)
    assert score < 100.0


def test_score_floors_at_zero():
    # 10 critical violations × 10.0 weight = 100 penalty → score = 0
    violations = make_violations(*[ViolationSeverity.CRITICAL] * 10)
    assert _calculate_score(violations) == 0.0


def test_score_never_goes_negative():
    # 20 critical violations → penalty > MAX_PENALTY
    violations = make_violations(*[ViolationSeverity.CRITICAL] * 20)
    assert _calculate_score(violations) >= 0.0


def test_critical_weighs_more_than_minor():
    critical_score = _calculate_score(make_violations(ViolationSeverity.CRITICAL))
    minor_score = _calculate_score(make_violations(ViolationSeverity.MINOR))
    assert critical_score < minor_score


def test_score_is_rounded_to_one_decimal():
    violations = make_violations(ViolationSeverity.MODERATE, ViolationSeverity.MINOR)
    score = _calculate_score(violations)
    assert score == round(score, 1)


def test_score_with_mixed_severities():
    violations = make_violations(
        ViolationSeverity.CRITICAL,   # 10.0
        ViolationSeverity.SERIOUS,    #  5.0
        ViolationSeverity.MODERATE,   #  2.0
        ViolationSeverity.MINOR,      #  0.5
    )
    # penalty = 17.5, score = 100 - (17.5/100 * 100) = 82.5
    assert _calculate_score(violations) == 82.5


def test_severity_weights_ordering():
    assert _SEVERITY_WEIGHTS[ViolationSeverity.CRITICAL] > _SEVERITY_WEIGHTS[ViolationSeverity.SERIOUS]
    assert _SEVERITY_WEIGHTS[ViolationSeverity.SERIOUS] > _SEVERITY_WEIGHTS[ViolationSeverity.MODERATE]
    assert _SEVERITY_WEIGHTS[ViolationSeverity.MODERATE] > _SEVERITY_WEIGHTS[ViolationSeverity.MINOR]


# ---------------------------------------------------------------------------
# _count_by_severity
# ---------------------------------------------------------------------------

def test_count_by_severity_all_zeros_for_empty():
    counts = _count_by_severity([])
    assert all(v == 0 for v in counts.values())


def test_count_by_severity_counts_correctly():
    violations = make_violations(
        ViolationSeverity.CRITICAL,
        ViolationSeverity.CRITICAL,
        ViolationSeverity.SERIOUS,
        ViolationSeverity.MINOR,
    )
    counts = _count_by_severity(violations)
    assert counts[ViolationSeverity.CRITICAL] == 2
    assert counts[ViolationSeverity.SERIOUS] == 1
    assert counts[ViolationSeverity.MODERATE] == 0
    assert counts[ViolationSeverity.MINOR] == 1


def test_count_by_severity_all_same():
    violations = make_violations(*[ViolationSeverity.MODERATE] * 5)
    counts = _count_by_severity(violations)
    assert counts[ViolationSeverity.MODERATE] == 5


# ---------------------------------------------------------------------------
# _score_to_grade
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("score,expected_grade", [
    (100.0, "A"),
    (90.0,  "A"),
    (89.9,  "B"),
    (75.0,  "B"),
    (74.9,  "C"),
    (60.0,  "C"),
    (59.9,  "D"),
    (40.0,  "D"),
    (39.9,  "F"),
    (0.0,   "F"),
])
def test_score_to_grade(score, expected_grade):
    assert _score_to_grade(score) == expected_grade


# ---------------------------------------------------------------------------
# _build_summary_text
# ---------------------------------------------------------------------------

def test_summary_text_perfect_score():
    counts = {s: 0 for s in ViolationSeverity}
    text = _build_summary_text(100.0, counts, pages=5)
    assert "No accessibility violations" in text
    assert "5 page" in text


def test_summary_text_with_critical_violations():
    counts = {
        ViolationSeverity.CRITICAL: 3,
        ViolationSeverity.SERIOUS: 0,
        ViolationSeverity.MODERATE: 0,
        ViolationSeverity.MINOR: 0,
    }
    text = _build_summary_text(70.0, counts, pages=2)
    assert "3 critical" in text
    assert "immediate attention" in text


def test_summary_text_with_serious_no_critical():
    counts = {
        ViolationSeverity.CRITICAL: 0,
        ViolationSeverity.SERIOUS: 4,
        ViolationSeverity.MODERATE: 1,
        ViolationSeverity.MINOR: 0,
    }
    text = _build_summary_text(75.0, counts, pages=3)
    assert "4 serious" in text
    assert "critical" not in text.lower().split("4 serious")[0]


def test_summary_text_includes_score_and_pages():
    counts = {s: 1 for s in ViolationSeverity}
    text = _build_summary_text(55.0, counts, pages=4)
    assert "55.0/100" in text
    assert "4 page" in text


def test_summary_text_includes_grade():
    counts = {s: 0 for s in ViolationSeverity}
    counts[ViolationSeverity.MODERATE] = 2
    text = _build_summary_text(96.0, counts, pages=1)
    assert "(A)" in text


# ---------------------------------------------------------------------------
# ReporterService.build_report — DB integration (mocked)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_build_report_creates_report_with_correct_counts():
    from app.services.reporter_service import ReporterService

    db = AsyncMock()
    service = ReporterService(db)

    critical_v = make_violation(ViolationSeverity.CRITICAL)
    moderate_v = make_violation(ViolationSeverity.MODERATE)

    service._get_pages = AsyncMock(return_value=[MagicMock(), MagicMock()])
    service._get_violations = AsyncMock(return_value=[critical_v, moderate_v])

    mock_report = MagicMock()
    mock_report.accessibility_score = 77.5
    mock_report.total_violations = 2
    mock_report.critical_count = 1
    mock_report.serious_count = 0
    mock_report.moderate_count = 1
    mock_report.minor_count = 0
    mock_report.pages_scanned = 2
    mock_report.summary_text = "Test summary"
    mock_report.id = __import__("uuid").uuid4()
    mock_report.audit_id = __import__("uuid").uuid4()
    mock_report.generated_at = __import__("datetime").datetime.now()

    service.report_repo = AsyncMock()
    service.report_repo.create = AsyncMock(return_value=mock_report)

    import uuid
    report = await service.build_report(uuid.uuid4())

    service.report_repo.create.assert_called_once()
    call_kwargs = service.report_repo.create.call_args.kwargs
    assert call_kwargs["critical_count"] == 1
    assert call_kwargs["moderate_count"] == 1
    assert call_kwargs["total_violations"] == 2
    assert call_kwargs["pages_scanned"] == 2


@pytest.mark.asyncio
async def test_build_report_score_is_100_when_no_violations():
    from app.services.reporter_service import ReporterService

    db = AsyncMock()
    service = ReporterService(db)
    service._get_pages = AsyncMock(return_value=[MagicMock()])
    service._get_violations = AsyncMock(return_value=[])

    mock_report = MagicMock()
    mock_report.accessibility_score = 100.0
    mock_report.total_violations = 0
    mock_report.critical_count = 0
    mock_report.serious_count = 0
    mock_report.moderate_count = 0
    mock_report.minor_count = 0
    mock_report.pages_scanned = 1
    mock_report.summary_text = "Perfect!"
    mock_report.id = __import__("uuid").uuid4()
    mock_report.audit_id = __import__("uuid").uuid4()
    mock_report.generated_at = __import__("datetime").datetime.now()

    service.report_repo = AsyncMock()
    service.report_repo.create = AsyncMock(return_value=mock_report)

    import uuid
    await service.build_report(uuid.uuid4())

    call_kwargs = service.report_repo.create.call_args.kwargs
    assert call_kwargs["accessibility_score"] == 100.0
    assert call_kwargs["total_violations"] == 0
