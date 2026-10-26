"""Profile mismatch: a sole trader whose turnover far exceeds the declared one."""

from datetime import timedelta

from ...models import Direction, PaymentPurpose
from ..builder import CaseBuilder, ScenarioRun
from ..context import SynthContext
from ..personas import make_business
from ..trade import business_activity


def profile_mismatch(ctx: SynthContext, case_index: int) -> ScenarioRun:
    """Client invoices add up to several times the turnover declared at onboarding.

    Args:
        ctx: Generation context.
        case_index: Case number, used to build identifiers.

    Returns:
        The scenario, alerted on a large client payment near the end of the window.
    """
    persona = make_business(ctx, case_index, turnover=(30_000, 50_000))
    builder = CaseBuilder(ctx, persona)
    trade = business_activity(builder, invoices_per_month=(4, 7), invoice_amount=(1_500, 6_000))
    day = ctx.period_end - timedelta(days=ctx.rng.randint(3, 15))
    client, amount = ctx.rng.choice(trade.clients), ctx.money(18_000, 30_000)
    alerted = builder.wire(day, amount, Direction.INBOUND, client, PaymentPurpose.INVOICE)
    return ScenarioRun(
        builder,
        alerted,
        "turnover_above_profile",
        "Incoming payments far exceed the turnover declared at onboarding.",
    )
