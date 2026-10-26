"""False positives: unusual-looking inflows that have a legitimate explanation."""

from datetime import timedelta
from decimal import Decimal

from ...models import Direction, PaymentPurpose
from ..background import individual_activity
from ..builder import CaseBuilder, ScenarioRun
from ..context import CENT, SynthContext
from ..parties import person
from ..personas import make_individual

BONUS_TEXTS = (  # Purpose texts of a one-off bonus
    "PREMIO DI RISULTATO {year}",
    "BONUS ANNUALE {year}",
    "UNA TANTUM {year}",
)
SALE_TEXTS = ("SALDO PREZZO COMPRAVENDITA IMMOBILE", "SALDO ROGITO APPARTAMENTO")  # House sale
LARGE_INFLOW = "large_incoming_transfer"  # Invented monitoring scenario for both cases
LARGE_INFLOW_REASON = "Incoming transfer well above the customer's usual inflows."  # Alert text


def salary_bonus(ctx: SynthContext, case_index: int) -> ScenarioRun:
    """An employee receives a one-off annual bonus from their usual employer.

    Args:
        ctx: Generation context.
        case_index: Case number, used to build identifiers.

    Returns:
        The scenario, alerted on the bonus.
    """
    persona = make_individual(ctx, case_index)
    builder = CaseBuilder(ctx, persona)
    household = individual_activity(builder)
    day = ctx.period_end - timedelta(days=ctx.rng.randint(5, 20))
    amount = (persona.monthly_income * Decimal(ctx.rng.randint(3, 5))).quantize(CENT)
    text = ctx.rng.choice(BONUS_TEXTS).format(year=day.year)
    bonus = builder.wire(
        day, amount, Direction.INBOUND, household.employer, PaymentPurpose.SALARY, text
    )
    return ScenarioRun(builder, bonus, LARGE_INFLOW, LARGE_INFLOW_REASON)


def property_sale(ctx: SynthContext, case_index: int) -> ScenarioRun:
    """A home owner receives the price of a flat they sold.

    Args:
        ctx: Generation context.
        case_index: Case number, used to build identifiers.

    Returns:
        The scenario, alerted on the sale proceeds.
    """
    persona = make_individual(ctx, case_index, birth_years=(1950, 1970))
    builder = CaseBuilder(ctx, persona)
    individual_activity(builder)
    day = ctx.period_end - timedelta(days=ctx.rng.randint(5, 20))
    amount = ctx.round_money(140_000, 320_000, 1000)
    text = ctx.rng.choice(SALE_TEXTS)
    sale = builder.wire(day, amount, Direction.INBOUND, person(ctx), PaymentPurpose.OTHER, text)
    return ScenarioRun(builder, sale, LARGE_INFLOW, LARGE_INFLOW_REASON)
