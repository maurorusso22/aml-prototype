"""Suspicious flows: funds passed through an account, and a dormant account brought back."""

from datetime import timedelta
from decimal import Decimal

from ...models import Channel, Direction, PaymentPurpose
from ..background import individual_activity
from ..builder import CaseBuilder, ScenarioRun
from ..context import CENT, SynthContext
from ..parties import FOREIGN_COUNTRIES, company, person
from ..personas import make_individual

COLLECTION_PURPOSES = (  # Vague reasons given by the senders of pass-through funds
    PaymentPurpose.FAMILY_SUPPORT,
    PaymentPurpose.LOAN,
    PaymentPurpose.OTHER,
    PaymentPurpose.UNKNOWN,
)
FORWARDED_SHARE = Decimal("0.92")  # Share of collected funds wired abroad


def pass_through(ctx: SynthContext, case_index: int) -> ScenarioRun:
    """A student collects transfers from many unrelated people and wires them abroad.

    Args:
        ctx: Generation context.
        case_index: Case number, used to build identifiers.

    Returns:
        The scenario, alerted on the first outgoing wire.
    """
    rng = ctx.rng
    persona = make_individual(
        ctx, case_index, birth_years=(1999, 2005), occupation="Student", income=(4_000, 9_000)
    )
    builder = CaseBuilder(ctx, persona)
    individual_activity(builder)
    start = ctx.period_end - timedelta(days=rng.randint(30, 40))
    collected = Decimal(0)
    for _ in range(rng.randint(12, 20)):
        amount, purpose = ctx.money(300, 1800), rng.choice(COLLECTION_PURPOSES)
        builder.wire(ctx.days_after(start, 0, 14), amount, Direction.INBOUND, person(ctx), purpose)
        collected += amount
    beneficiaries = (
        company(ctx, country=rng.choice(FOREIGN_COUNTRIES)),
        person(ctx, country=rng.choice(FOREIGN_COUNTRIES)),
    )
    parts = rng.randint(2, 3)
    share = (collected * FORWARDED_SHARE / parts).quantize(CENT)
    wires = [
        builder.wire(
            ctx.days_after(start, 15, 20),
            share,
            Direction.OUTBOUND,
            beneficiaries[part % 2],
            rng.choice((PaymentPurpose.INVOICE, PaymentPurpose.OTHER)),
        )
        for part in range(parts)
    ]
    first = min(wires, key=lambda wire: wire.booked_at)
    return ScenarioRun(
        builder,
        first,
        "rapid_movement_of_funds",
        "Many small inflows from unrelated people, forwarded abroad within days.",
    )


def dormant_reactivation(ctx: SynthContext, case_index: int) -> ScenarioRun:
    """An account unused for months suddenly receives large foreign inflows, then empties.

    Args:
        ctx: Generation context.
        case_index: Case number, used to build identifiers.

    Returns:
        The scenario, alerted on the first inflow after the dormant period.
    """
    rng = ctx.rng
    persona = make_individual(ctx, case_index, birth_years=(1950, 1975))
    builder = CaseBuilder(ctx, persona)
    individual_activity(builder, end=ctx.period_start + timedelta(days=rng.randint(60, 90)))
    restart = ctx.period_end - timedelta(days=rng.randint(35, 45))
    sender = company(ctx, country=rng.choice(FOREIGN_COUNTRIES))
    first = builder.wire(
        restart, ctx.money(30_000, 60_000), Direction.INBOUND, sender, PaymentPurpose.INVOICE
    )
    for _ in range(rng.randint(2, 3)):
        day, amount = ctx.days_after(restart, 3, 25), ctx.money(15_000, 40_000)
        builder.wire(day, amount, Direction.INBOUND, sender, PaymentPurpose.INVOICE)
    for _ in range(rng.randint(3, 5)):
        amount = ctx.round_money(2_000, 5_000, 100)
        builder.cash(ctx.days_after(restart, 1, 30), amount, Direction.OUTBOUND, Channel.BRANCH)
    for _ in range(2):
        day, amount = ctx.days_after(restart, 5, 30), ctx.money(5_000, 15_000)
        builder.wire(day, amount, Direction.OUTBOUND, person(ctx), PaymentPurpose.OTHER)
    return ScenarioRun(
        builder,
        first,
        "dormant_account_reactivation",
        "Large inflows on an account with no customer activity for several months.",
    )
