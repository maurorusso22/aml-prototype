"""Money in and out of the customer's accounts, overall and in the recent window."""

from decimal import Decimal

from ..models import Direction, Fact, FactCategory, Transaction
from .base import RECENT_DAYS, AnalysisContext
from .facts import Facts, euros, ratio, total
from .registry import analyser


@analyser
def flow_summary(context: AnalysisContext) -> list[Fact]:
    """Total, monthly, and recent flows, and how recent flows compare with the earlier period.

    Args:
        context: Case under analysis.

    Returns:
        Facts F-FLOW-001 to F-FLOW-008.
    """
    facts = Facts("FLOW", FactCategory.TRANSACTION_BEHAVIOUR)
    bundle = context.bundle
    period_days = (bundle.period_end - bundle.period_start).days + 1
    inflows, outflows = context.flows(Direction.INBOUND), context.flows(Direction.OUTBOUND)
    total_in, total_out = total(inflows), total(outflows)
    facts.add(1, "Total inflows", euros(total_in), "EUR", inflows)
    facts.add(2, "Total outflows", euros(total_out), "EUR", outflows)
    facts.add(3, "Net flow", euros(total_in - total_out), "EUR")
    facts.add(4, "Average monthly inflows", euros(total_in * 30 / period_days), "EUR")
    recent_in, recent_in_total, in_multiple = _recent(context, Direction.INBOUND, period_days)
    recent_out, recent_out_total, out_multiple = _recent(context, Direction.OUTBOUND, period_days)
    days = f"the last {RECENT_DAYS} days"
    facts.add(5, f"Inflows in {days}", euros(recent_in_total), "EUR", recent_in)
    facts.add(6, "Recent inflows as a multiple of the usual level", in_multiple, "times")
    facts.add(7, f"Outflows in {days}", euros(recent_out_total), "EUR", recent_out)
    facts.add(8, "Recent outflows as a multiple of the usual level", out_multiple, "times")
    return facts.items


def _recent(
    context: AnalysisContext, direction: Direction, period_days: int
) -> tuple[list[Transaction], Decimal, float]:
    """Measure recent flows against the earlier part of the period.

    The earlier total is scaled to the length of the recent window, so 1 means business as
    usual and 3 means three times the usual flow.

    Args:
        context: Case under analysis.
        direction: Inbound or outbound.
        period_days: Length of the look-back period in days.

    Returns:
        Recent transactions, their total, and the multiple of the usual level.
    """
    recent = context.flows(direction, recent=True)
    earlier = total(tx for tx in context.flows(direction) if not context.is_recent(tx))
    earlier_days = period_days - RECENT_DAYS
    usual = earlier * RECENT_DAYS / earlier_days if earlier_days > 0 else Decimal(0)
    recent_total = total(recent)
    return recent, recent_total, ratio(recent_total, usual)
