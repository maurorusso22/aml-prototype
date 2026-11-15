"""Timing: periods of inactivity and bursts of activity."""

from datetime import timedelta

from ..models import Channel, Fact, FactCategory, FactStatus, Transaction
from .base import AnalysisContext
from .facts import Facts, ratio
from .registry import analyser

CUSTOMER_CHANNELS = frozenset(  # Channels where the customer acts, unlike incoming transfers
    {Channel.BRANCH, Channel.ATM, Channel.ONLINE, Channel.POS}
)
BURST_DAYS = 7  # Width of the window used to find bursts of activity


@analyser
def temporal_patterns(context: AnalysisContext) -> list[Fact]:
    """Find the longest inactivity, the silence before the alert, and the busiest week.

    When the customer initiated nothing before the alert, the silence runs back to the start of
    the observed history: a lower bound of the true silence, flagged by F-TIME-006, rather than
    a zero that would hide the reactivation of a dormant account.

    Args:
        context: Case under analysis.

    Returns:
        Facts F-TIME-001 to F-TIME-006.
    """
    facts = Facts("TIME", FactCategory.TRANSACTION_BEHAVIOUR)
    alerted = context.alerted
    transactions = sorted(context.bundle.transactions, key=lambda tx: tx.booked_at)
    own = [tx for tx in transactions if tx.channel in CUSTOMER_CHANNELS]
    gaps = [
        ((later.booked_at - earlier.booked_at).days, [earlier, later])
        for earlier, later in zip(own, own[1:], strict=False)
    ]
    longest_label = "Longest period without customer-initiated activity"
    if gaps:
        longest, bounds = max(gaps, key=lambda gap: gap[0])
        facts.add(1, longest_label, longest, "days", bounds)
    else:
        facts.add(1, longest_label, FactStatus.NO_ACTIVITY, "days", own)
    before = [tx for tx in own if tx.booked_at < alerted.booked_at]
    if before:
        silence = (alerted.booked_at - before[-1].booked_at).days
    else:
        silence = max((alerted.booked_at.date() - context.observed_from).days, 0)
    facts.add(
        2, "Days without customer-initiated activity before the alert", silence, "days", before[-1:]
    )
    busiest = _busiest_window(transactions)
    usual = len(transactions) * BURST_DAYS / context.observed_days
    facts.add(3, f"Most transactions in any {BURST_DAYS} days", len(busiest), "count", busiest)
    facts.add(4, f"Average transactions per {BURST_DAYS} days", round(usual, 2), "count")
    facts.add(
        5,
        "Busiest week as a multiple of the average",
        ratio(len(busiest), round(usual, 4)),
        "times",
        busiest,
    )
    no_history = "No customer-initiated activity before the alert in the observed history"
    facts.add(6, no_history, not before, None)
    return facts.items


def _busiest_window(transactions: list[Transaction]) -> list[Transaction]:
    """Find the window of `BURST_DAYS` days holding the most transactions.

    Args:
        transactions: Transactions in booking order.

    Returns:
        The transactions of the busiest window, earliest window on ties.
    """
    best: list[Transaction] = []
    for start, first in enumerate(transactions):
        end = first.booked_at + timedelta(days=BURST_DAYS)
        window = [tx for tx in transactions[start:] if tx.booked_at < end]
        if len(window) > len(best):
            best = window
    return best
