"""What the money is for, according to the payment purposes found by enrichment."""

from ..models import Direction, Fact, FactCategory, PaymentPurpose
from .base import AnalysisContext
from .facts import Facts, euros, ratio, total
from .registry import analyser

SIDES = (  # (numbering offset, direction, word): inflow facts from 1, outflow facts from 101
    (0, Direction.INBOUND, "Inflows"),
    (100, Direction.OUTBOUND, "Outflows"),
)


@analyser
def purpose_mix(context: AnalysisContext) -> list[Fact]:
    """Sum enriched inflows and outflows by payment purpose.

    Every purpose always gets a fact, so identifiers stay the same from case to case.

    Args:
        context: Case under analysis.

    Returns:
        Facts F-PURP-001 to 007 (inflows), 101 to 107 (outflows), and 201 (unknown share).
    """
    facts = Facts("PURP", FactCategory.TRANSACTION_BEHAVIOUR)
    enriched = [
        tx for tx in context.bundle.transactions if tx.transaction_id in context.enrichments
    ]
    for offset, direction, word in SIDES:
        flows = [tx for tx in enriched if tx.direction is direction]
        for number, purpose in enumerate(PaymentPurpose, start=1):
            labelled = [
                tx
                for tx in flows
                if context.enrichments[tx.transaction_id].payment_purpose is purpose
            ]
            label = f"{word} for {purpose.replace('_', ' ')}"
            facts.add(offset + number, label, euros(total(labelled)), "EUR", labelled)
    unknown = [
        tx
        for tx in enriched
        if context.enrichments[tx.transaction_id].payment_purpose is PaymentPurpose.UNKNOWN
    ]
    share = ratio(len(unknown), len(enriched))
    facts.add(201, "Share of transfers and debits with no stated purpose", share, "ratio", unknown)
    return facts.items
