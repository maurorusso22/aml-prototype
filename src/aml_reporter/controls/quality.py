"""Data-quality checks: what limits the analysis of a valid case, reported instead of hidden.

A bundle that fails validation is rejected outright. These checks cover the softer problems:
the case can be analysed, but some figures rest on less than they seem to, and the analyst
must know which ones before relying on them.
"""

from collections.abc import Sequence

from ..analytics.base import MIN_BASELINE_DAYS, AnalysisContext
from ..enrichment import enrichable
from ..models import CaseBundle, Enrichment, EnrichmentSource, Transaction
from .config import QualityThresholds
from .models import IssueCode, QualityIssue
from .records import card_validity, duplicate_bookings

NO_FALLBACK = "baseline"  # Enricher whose records are rule-based by design, never a fallback


def check_quality(
    bundle: CaseBundle,
    enrichments: Sequence[Enrichment],
    enricher: str,
    thresholds: QualityThresholds,
) -> tuple[QualityIssue, ...]:
    """Run every data-quality check on a validated case and its enrichments.

    Args:
        bundle: Validated case bundle.
        enrichments: Fields extracted from its descriptions.
        enricher: Name of the enricher that produced them.
        thresholds: Tolerances of the checks.

    Returns:
        Issues found, in a fixed order; empty when the case is clean.
    """
    context = AnalysisContext(bundle, {item.transaction_id: item for item in enrichments})
    targets = enrichable(bundle.transactions)
    found = (
        _short_history(context),
        _undescribed(targets, thresholds.max_undescribed_share),
        _unenriched(targets, enrichments),
        _fallback(enrichments, enricher, thresholds.max_fallback_share),
        duplicate_bookings(bundle.transactions),
        card_validity(bundle),
    )
    return tuple(issue for issue in found if issue is not None)


def _short_history(context: AnalysisContext) -> QualityIssue | None:
    """Warn when the history before the recent window is too short for a usual level.

    Args:
        context: Case under analysis.

    Returns:
        The issue, or None.
    """
    if context.baseline_days >= MIN_BASELINE_DAYS:
        return None
    details = {"days": context.baseline_days, "minimum": MIN_BASELINE_DAYS}
    return QualityIssue(code=IssueCode.SHORT_HISTORY, details=details)


def _undescribed(targets: list[Transaction], tolerance: float) -> QualityIssue | None:
    """Warn when transfers and debits have no description for enrichment to read.

    Args:
        targets: Transfers and direct debits of the case.
        tolerance: Share of them allowed an empty description.

    Returns:
        The issue, or None.
    """
    empty = [tx for tx in targets if not tx.description.strip()]
    if not empty or len(empty) <= tolerance * len(targets):
        return None
    details = {"count": len(empty), "total": len(targets)}
    ids = tuple(tx.transaction_id for tx in empty)
    return QualityIssue(code=IssueCode.UNDESCRIBED, details=details, transactions=ids)


def _unenriched(
    targets: list[Transaction], enrichments: Sequence[Enrichment]
) -> QualityIssue | None:
    """Warn when the enricher returned nothing for some transfers or debits.

    Args:
        targets: Transfers and direct debits of the case.
        enrichments: Enrichments received.

    Returns:
        The issue, or None.
    """
    received = {item.transaction_id for item in enrichments}
    missing = tuple(tx.transaction_id for tx in targets if tx.transaction_id not in received)
    if not missing:
        return None
    details = {"count": len(missing), "total": len(targets)}
    return QualityIssue(code=IssueCode.UNENRICHED, details=details, transactions=missing)


def _fallback(
    enrichments: Sequence[Enrichment], enricher: str, tolerance: float
) -> QualityIssue | None:
    """Warn when an LLM enricher fell back to the rules for too many records.

    Args:
        enrichments: Enrichments received.
        enricher: Name of the enricher that produced them.
        tolerance: Share of records allowed to come from the fallback.

    Returns:
        The issue, or None.
    """
    if enricher == NO_FALLBACK or not enrichments:
        return None
    fallen = sum(item.source is EnrichmentSource.BASELINE for item in enrichments)
    share = fallen / len(enrichments)
    if share <= tolerance:
        return None
    details = {"share": round(share * 100), "limit": round(tolerance * 100)}
    return QualityIssue(code=IssueCode.FALLBACK, details=details)
