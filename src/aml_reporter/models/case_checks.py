"""Cross-reference checks for case bundles.

Each check returns human-readable problems instead of raising, so a single validation error can
report every inconsistency in a bundle at once.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .case import CaseBundle


def find_reference_problems(case: CaseBundle) -> list[str]:
    """Run every cross-reference check on a case bundle.

    Args:
        case: Bundle whose fields have already passed field-level validation.

    Returns:
        Problems found, empty when the bundle is consistent.
    """
    return [
        *_duplicates("account_id", (account.account_id for account in case.accounts)),
        *_duplicates("card_id", (card.card_id for card in case.cards)),
        *_duplicates("transaction_id", (tx.transaction_id for tx in case.transactions)),
        *_period_problems(case),
        *_card_problems(case),
        *_transaction_problems(case),
        *_alert_problems(case),
    ]


def _duplicates(label: str, ids: Iterable[str]) -> list[str]:
    """Find identifiers that appear more than once.

    Args:
        label: Field name used in the messages.
        ids: Identifiers to inspect.

    Returns:
        One problem per duplicated identifier.
    """
    return [f"duplicate {label} {value}" for value, count in Counter(ids).items() if count > 1]


def _period_problems(case: CaseBundle) -> list[str]:
    """Check that the look-back window is not reversed.

    Args:
        case: Bundle to inspect.

    Returns:
        Problems found.
    """
    if case.period_end < case.period_start:
        return ["period_end must not precede period_start"]
    return []


def _card_problems(case: CaseBundle) -> list[str]:
    """Check that every card is linked to an account in the bundle.

    Args:
        case: Bundle to inspect.

    Returns:
        Problems found.
    """
    account_ids = {account.account_id for account in case.accounts}
    return [
        f"card {card.card_id} references unknown account {card.account_id}"
        for card in case.cards
        if card.account_id not in account_ids
    ]


def _transaction_problems(case: CaseBundle) -> list[str]:
    """Check accounts, cards, and booking dates of every transaction.

    Args:
        case: Bundle to inspect.

    Returns:
        Problems found.
    """
    account_ids = {account.account_id for account in case.accounts}
    card_accounts = {card.card_id: card.account_id for card in case.cards}
    problems: list[str] = []
    for tx in case.transactions:
        if tx.account_id not in account_ids:
            problems.append(f"transaction {tx.transaction_id} references unknown account")
        if tx.card_id is not None and card_accounts.get(tx.card_id) != tx.account_id:
            problems.append(
                f"transaction {tx.transaction_id} uses card {tx.card_id}, "
                f"which is not linked to account {tx.account_id}"
            )
        booked_on = tx.booked_at.date()
        if not case.period_start <= booked_on <= case.period_end:
            problems.append(
                f"transaction {tx.transaction_id} booked on {booked_on}, outside the case period"
            )
    return problems


def _alert_problems(case: CaseBundle) -> list[str]:
    """Check that the alert points to this customer and to a known transaction.

    Args:
        case: Bundle to inspect.

    Returns:
        Problems found.
    """
    alert = case.alert
    problems: list[str] = []
    if alert.customer_id != case.customer.customer_id:
        problems.append(f"alert refers to customer {alert.customer_id}, not to the bundle's one")
    alerted = next(
        (tx for tx in case.transactions if tx.transaction_id == alert.transaction_id), None
    )
    if alerted is None:
        problems.append(f"alert references unknown transaction {alert.transaction_id}")
    elif alert.raised_at < alerted.booked_at:
        problems.append("alert raised before the alerted transaction was booked")
    return problems
