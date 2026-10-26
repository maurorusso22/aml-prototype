"""Structuring: cash split into deposits that each stay just below a threshold."""

from datetime import timedelta

from ...models import Channel, Direction
from ..background import individual_activity
from ..builder import CaseBuilder, ScenarioRun
from ..context import SynthContext
from ..personas import make_individual

ILLUSTRATIVE_THRESHOLD = 10_000.0  # Illustrative cash threshold, not taken from any regulation


def structuring_cash(ctx: SynthContext, case_index: int) -> ScenarioRun:
    """Several cash deposits within a few weeks, each between 85% and 99% of the threshold.

    Args:
        ctx: Generation context.
        case_index: Case number, used to build identifiers.

    Returns:
        The scenario, alerted on the last deposit.
    """
    persona = make_individual(ctx, case_index)
    builder = CaseBuilder(ctx, persona)
    individual_activity(builder)
    days, day = [], ctx.period_end - timedelta(days=50)
    for _ in range(ctx.rng.randint(6, 9)):
        day = ctx.days_after(day, 2, 5)
        days.append(day)
    low, high = ILLUSTRATIVE_THRESHOLD * 0.85, ILLUSTRATIVE_THRESHOLD * 0.99
    deposits = [
        builder.cash(day, ctx.money(low, high), Direction.INBOUND, Channel.BRANCH) for day in days
    ]
    return ScenarioRun(
        builder,
        deposits[-1],
        "repeated_cash_deposits",
        "Several cash deposits just below the reporting threshold within a few weeks.",
    )
