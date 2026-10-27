"""The alerted transaction compared with the customer's own history."""

from statistics import median

from ..models import Fact, FactCategory
from .base import AnalysisContext
from .facts import Facts, euros, ratio
from .registry import analyser


@analyser
def alert_in_context(context: AnalysisContext) -> list[Fact]:
    """Compare the alerted transaction with earlier ones of the same type and direction.

    Args:
        context: Case under analysis.

    Returns:
        Facts F-ALERT-001 to F-ALERT-009.
    """
    facts = Facts("ALERT", FactCategory.ALERT)
    alerted = context.alerted
    peers = [
        tx
        for tx in context.bundle.transactions
        if tx.transaction_type is alerted.transaction_type
        and tx.direction is alerted.direction
        and tx.booked_at < alerted.booked_at
    ]
    typical = median(tx.amount for tx in peers) if peers else alerted.amount * 0
    largest = max(peers, key=lambda tx: tx.amount, default=None)
    kind = f"{alerted.direction} {alerted.transaction_type}".replace("_", " ")
    facts.add(1, "Amount of the alerted transaction", euros(alerted.amount), "EUR", [alerted])
    facts.add(2, "Kind of the alerted transaction", kind, None, [alerted])
    facts.add(3, "Earlier transactions of the same kind", len(peers), "count", peers)
    facts.add(4, "Median amount of those transactions", euros(typical), "EUR", peers)
    multiple = ratio(alerted.amount, typical)
    facts.add(5, "Alerted amount as a multiple of that median", multiple, "times", [alerted])
    largest_amount, largest_evidence = (euros(largest.amount), [largest]) if largest else (0.0, [])
    facts.add(6, "Largest of those transactions", largest_amount, "EUR", largest_evidence)
    _add_counterparty(context, facts)
    return facts.items


def _add_counterparty(context: AnalysisContext, facts: Facts) -> None:
    """Describe the counterparty of the alerted transaction, when enrichment found one.

    Args:
        context: Case under analysis.
        facts: Collection receiving F-ALERT-007 to F-ALERT-009.
    """
    alerted = context.alerted
    enrichment = context.enrichments.get(alerted.transaction_id)
    key = context.counterparty(alerted)
    if enrichment is None or key is None:
        return
    earlier = [
        tx
        for tx in context.bundle.transactions
        if tx.booked_at < alerted.booked_at and context.counterparty(tx) == key
    ]
    name = enrichment.counterparty_name or key
    facts.add(7, "Counterparty of the alerted transaction", name, None, [alerted])
    facts.add(8, "Earlier transactions with the same counterparty", len(earlier), "count", earlier)
    if enrichment.counterparty_type is not None:
        kind = enrichment.counterparty_type.replace("_", " ")
        facts.add(9, "Type of that counterparty", kind, None, [alerted])
