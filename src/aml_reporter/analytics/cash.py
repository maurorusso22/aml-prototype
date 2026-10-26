"""Cash deposits and withdrawals, including deposits that stay just below a threshold."""

from ..models import Direction, Fact, FactCategory, TransactionType
from .base import RECENT_DAYS, AnalysisContext
from .facts import Facts, euros, ratio, total
from .registry import analyser

ILLUSTRATIVE_CASH_THRESHOLD = 10_000  # Illustrative threshold, not taken from any regulation
NEAR_THRESHOLD_SHARE = 0.85  # Deposits from 85% of the threshold upwards count as "just below"


@analyser
def cash_activity(context: AnalysisContext) -> list[Fact]:
    """Count and sum cash movements, overall and in the recent window.

    Args:
        context: Case under analysis.

    Returns:
        Facts F-CASH-001 to F-CASH-007.
    """
    facts = Facts("CASH", FactCategory.TRANSACTION_BEHAVIOUR)
    transactions = context.bundle.transactions
    deposits = [tx for tx in transactions if tx.transaction_type is TransactionType.CASH_DEPOSIT]
    withdrawals = [
        tx for tx in transactions if tx.transaction_type is TransactionType.CASH_WITHDRAWAL
    ]
    recent_deposits = [tx for tx in deposits if context.is_recent(tx)]
    low = ILLUSTRATIVE_CASH_THRESHOLD * NEAR_THRESHOLD_SHARE
    near = [tx for tx in recent_deposits if low <= tx.amount < ILLUSTRATIVE_CASH_THRESHOLD]
    recent_withdrawals = [tx for tx in withdrawals if context.is_recent(tx)]
    inflows = total(context.flows(Direction.INBOUND))
    days = f"the last {RECENT_DAYS} days"
    facts.add(1, "Cash deposits", len(deposits), "count", deposits)
    facts.add(2, f"Cash deposits in {days}", len(recent_deposits), "count", recent_deposits)
    facts.add(3, f"Cash deposited in {days}", euros(total(recent_deposits)), "EUR", recent_deposits)
    near_label = f"Recent cash deposits just below EUR {ILLUSTRATIVE_CASH_THRESHOLD:,}"
    facts.add(4, near_label, len(near), "count", near)
    facts.add(5, "Cash withdrawn", euros(total(withdrawals)), "EUR", withdrawals)
    recent_withdrawn = euros(total(recent_withdrawals))
    facts.add(6, f"Cash withdrawn in {days}", recent_withdrawn, "EUR", recent_withdrawals)
    facts.add(7, "Share of inflows paid in cash", ratio(total(deposits), inflows), "ratio")
    return facts.items
