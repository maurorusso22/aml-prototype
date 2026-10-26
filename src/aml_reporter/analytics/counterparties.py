"""Who the customer transacts with: how many counterparties, how concentrated, how new."""

from collections import defaultdict

from ..models import CounterpartyType, Direction, Fact, FactCategory, Transaction
from .base import RECENT_DAYS, AnalysisContext
from .facts import Facts, ratio, total
from .registry import analyser


@analyser
def counterparty_analysis(context: AnalysisContext) -> list[Fact]:
    """Count, rank, and date the counterparties found by enrichment.

    Counterparties are grouped by IBAN when known, otherwise by name.

    Args:
        context: Case under analysis.

    Returns:
        Facts F-CPTY-001 to F-CPTY-007.
    """
    facts = Facts("CPTY", FactCategory.COUNTERPARTY)
    inflows = context.flows(Direction.INBOUND)
    senders = _group(context, inflows)
    receivers = _group(context, context.flows(Direction.OUTBOUND))
    sent = [tx for group in senders.values() for tx in group]
    received = [tx for group in receivers.values() for tx in group]
    facts.add(1, "Distinct counterparties sending money", len(senders), "count", sent)
    facts.add(2, "Distinct counterparties receiving money", len(receivers), "count", received)
    largest = max(senders.values(), key=total, default=[])
    facts.add(
        3,
        "Share of inflows from the largest sender",
        ratio(total(largest), total(inflows)),
        "ratio",
        largest,
    )
    facts.add(4, "Largest sender", _name(context, largest[0]) if largest else "none", None, largest)
    people = [
        group
        for group in senders.values()
        if _is_person(context, group[0]) and any(context.is_recent(tx) for tx in group)
    ]
    people_label = f"Distinct people sending money in the last {RECENT_DAYS} days"
    facts.add(5, people_label, len(people), "count", [tx for group in people for tx in group])
    first_seen = [
        min(group, key=lambda tx: tx.booked_at)
        for group in _group(context, sent + received).values()
    ]
    new = [tx for tx in first_seen if context.is_recent(tx)]
    facts.add(
        6, f"Counterparties first seen in the last {RECENT_DAYS} days", len(new), "count", new
    )
    from_people = [tx for tx in sent if _is_person(context, tx)]
    share = ratio(total(from_people), total(inflows))
    facts.add(7, "Share of inflows from natural persons", share, "ratio", from_people)
    return facts.items


def _group(
    context: AnalysisContext, transactions: list[Transaction]
) -> dict[str, list[Transaction]]:
    """Group transactions by counterparty, skipping those without one.

    Args:
        context: Case under analysis.
        transactions: Transactions to group.

    Returns:
        Transactions per counterparty key, in first-seen order.
    """
    groups: dict[str, list[Transaction]] = defaultdict(list)
    for tx in transactions:
        key = context.counterparty(tx)
        if key is not None:
            groups[key].append(tx)
    return dict(groups)


def _is_person(context: AnalysisContext, transaction: Transaction) -> bool:
    """Tell whether a transaction's counterparty is a natural person.

    Args:
        context: Case under analysis.
        transaction: An enriched transaction.

    Returns:
        True for natural persons.
    """
    enrichment = context.enrichments.get(transaction.transaction_id)
    return (
        enrichment is not None and enrichment.counterparty_type is CounterpartyType.NATURAL_PERSON
    )


def _name(context: AnalysisContext, transaction: Transaction) -> str:
    """Name a counterparty for a fact label.

    Args:
        context: Case under analysis.
        transaction: An enriched transaction.

    Returns:
        The counterparty name, or its IBAN when no name was found.
    """
    enrichment = context.enrichments[transaction.transaction_id]
    return enrichment.counterparty_name or str(enrichment.counterparty_iban)
