"""Ordinary activity of an individual customer, whatever the scenario."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ..models import Direction, IndividualCustomer, PaymentPurpose
from .builder import CaseBuilder
from .context import CENT, month_starts
from .parties import Party, company, person

LOAN_SHARE = 0.4  # Share of individuals repaying a consumer loan by direct debit
FAMILY_TRANSFER_SHARE = 0.3  # Monthly chance of a transfer to a relative


@dataclass(frozen=True)
class Household:
    """Counterparties of an individual's everyday life."""

    employer: Party
    landlord: Party
    utility: Party
    lender: Party
    relatives: tuple[Party, ...]


def individual_activity(builder: CaseBuilder, end: date | None = None) -> Household:
    """Add salary, rent, bills, card spending, cash, and family transfers, month by month.

    Args:
        builder: Case under construction.
        end: Last day of activity; defaults to the end of the look-back window.

    Returns:
        The counterparties used, so scenarios can reuse them.
    """
    ctx, customer = builder.ctx, builder.persona.customer
    family_name = customer.last_name if isinstance(customer, IndividualCustomer) else None
    household = Household(
        employer=company(ctx),
        landlord=person(ctx),
        utility=company(ctx, sector="ENERGIA"),
        lender=company(ctx, sector="FINANZIARIA"),
        relatives=tuple(person(ctx, last_name=family_name) for _ in range(2)),
    )
    window = (ctx.period_start, end or ctx.period_end)
    rent, has_loan = ctx.money(450, 1100), ctx.rng.random() < LOAN_SHARE
    for month in month_starts(*window):
        _monthly_flows(builder, household, month, window, rent, has_loan)
        _everyday_spending(builder, household, month, window)
    return household


def _monthly_flows(
    builder: CaseBuilder,
    household: Household,
    month: date,
    window: tuple[date, date],
    rent: Decimal,
    has_loan: bool,
) -> None:
    """Add the recurring flows of one month: salary, rent, bills, and loan instalment.

    Args:
        builder: Case under construction.
        household: Counterparties of the customer.
        month: First day of the month.
        window: First and last day of activity.
        rent: Monthly rent in euros.
        has_loan: Whether a loan instalment is collected.
    """
    ctx = builder.ctx
    for day in ctx.days_in_month(month, window, 26, 28):
        variation = Decimal(f"{ctx.rng.uniform(0.98, 1.02):.4f}")
        salary = (builder.persona.monthly_income * variation).quantize(CENT)
        builder.wire(day, salary, Direction.INBOUND, household.employer, PaymentPurpose.SALARY)
    for day in ctx.days_in_month(month, window, 1, 5):
        builder.wire(day, rent, Direction.OUTBOUND, household.landlord, PaymentPurpose.RENT)
    for day in ctx.days_in_month(month, window, 10, 20):
        builder.direct_debit(day, ctx.money(40, 140), household.utility, PaymentPurpose.INVOICE)
    for day in ctx.days_in_month(month, window, 15, 15, count=int(has_loan)):
        builder.direct_debit(day, ctx.money(150, 160), household.lender, PaymentPurpose.LOAN)


def _everyday_spending(
    builder: CaseBuilder, household: Household, month: date, window: tuple[date, date]
) -> None:
    """Add the irregular flows of one month: card payments, ATM cash, help to relatives.

    Args:
        builder: Case under construction.
        household: Counterparties of the customer.
        month: First day of the month.
        window: First and last day of activity.
    """
    ctx = builder.ctx
    rng = ctx.rng
    for day in ctx.days_in_month(month, window, count=rng.randint(5, 10)):
        builder.card_payment(day, ctx.money(4, 120))
    for day in ctx.days_in_month(month, window, count=rng.randint(0, 2)):
        builder.atm_withdrawal(day, ctx.round_money(50, 260, 10))
    if rng.random() < FAMILY_TRANSFER_SHARE:
        for day in ctx.days_in_month(month, window):
            relative, amount = rng.choice(household.relatives), ctx.money(100, 500)
            builder.wire(day, amount, Direction.OUTBOUND, relative, PaymentPurpose.FAMILY_SUPPORT)
