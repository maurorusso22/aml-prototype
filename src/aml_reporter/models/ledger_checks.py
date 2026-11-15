"""Ledger checks for case bundles: amounts the analytics can add up, on live accounts.

These problems would silently corrupt every figure, so they reject the bundle. Softer issues,
which only limit what the analysis can say, are data-quality warnings in `controls/`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .case import CaseBundle

SUPPORTED_CURRENCY = "EUR"  # Analytics add amounts as euros and never convert currencies


def find_ledger_problems(case: CaseBundle) -> list[str]:
    """Run every ledger check on a case bundle.

    Args:
        case: Bundle whose fields have already passed field-level validation.

    Returns:
        Problems found, empty when the ledger is consistent.
    """
    return [*_currency_problems(case), *_lifecycle_problems(case)]


def _currency_problems(case: CaseBundle) -> list[str]:
    """Reject accounts and transactions in a currency the analytics cannot add up.

    Args:
        case: Bundle to inspect.

    Returns:
        Problems found.
    """
    problems = [
        f"account {account.account_id} is in {account.currency}, not {SUPPORTED_CURRENCY}"
        for account in case.accounts
        if account.currency != SUPPORTED_CURRENCY
    ]
    problems += [
        f"transaction {tx.transaction_id} is in {tx.currency}, not {SUPPORTED_CURRENCY}"
        for tx in case.transactions
        if tx.currency != SUPPORTED_CURRENCY
    ]
    return problems


def _lifecycle_problems(case: CaseBundle) -> list[str]:
    """Reject transactions booked before their account opened or after it closed.

    Args:
        case: Bundle to inspect.

    Returns:
        Problems found.
    """
    accounts = {account.account_id: account for account in case.accounts}
    problems: list[str] = []
    for tx in case.transactions:
        account, booked_on = accounts.get(tx.account_id), tx.booked_at.date()
        if account is None:
            continue
        if booked_on < account.opened_on:
            problems.append(
                f"transaction {tx.transaction_id} booked on {booked_on}, "
                f"before account {account.account_id} opened"
            )
        if account.closed_on is not None and booked_on > account.closed_on:
            problems.append(
                f"transaction {tx.transaction_id} booked on {booked_on}, "
                f"after account {account.account_id} closed"
            )
    return problems
