"""Record-level data-quality checks: bookings that repeat, and cards used outside their validity.

Both point to a faulty data feed more often than to the customer, so they warn rather than
reject: the analyst decides whether the records distort the figures.
"""

from collections import Counter
from collections.abc import Sequence

from ..models import CaseBundle, Transaction
from .models import IssueCode, QualityIssue


def duplicate_bookings(transactions: Sequence[Transaction]) -> QualityIssue | None:
    """Warn about bookings that repeat an earlier one field for field, except the identifier.

    Args:
        transactions: Every transaction of the case.

    Returns:
        The issue, listing the repeats but not their first occurrence, or None.
    """
    seen: Counter[tuple[object, ...]] = Counter()
    repeats = []
    for tx in transactions:
        key = (tx.account_id, tx.card_id, tx.booked_at, tx.amount, tx.direction, tx.description)
        if seen[key]:
            repeats.append(tx.transaction_id)
        seen[key] += 1
    if not repeats:
        return None
    details = {"count": len(repeats)}
    return QualityIssue(code=IssueCode.DUPLICATES, details=details, transactions=tuple(repeats))


def card_validity(bundle: CaseBundle) -> QualityIssue | None:
    """Warn about card transactions booked outside the issue and expiry dates of their card.

    Args:
        bundle: Validated case bundle.

    Returns:
        The issue, or None.
    """
    cards = {card.card_id: card for card in bundle.cards}
    outside = tuple(
        tx.transaction_id
        for tx in bundle.transactions
        if tx.card_id is not None
        and not cards[tx.card_id].issued_on <= tx.booked_at.date() <= cards[tx.card_id].expires_on
    )
    if not outside:
        return None
    details = {"count": len(outside)}
    return QualityIssue(code=IssueCode.CARD_VALIDITY, details=details, transactions=outside)
