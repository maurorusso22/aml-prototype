"""Ordinary activity of a sole trader, whatever the scenario."""

from dataclasses import dataclass

from ..models import Direction, PaymentPurpose
from .builder import CaseBuilder
from .context import month_starts
from .parties import Party, company, person

CLIENT_COUNT = 5  # Companies that buy from the sole trader
SUPPLIER_COUNT = 3  # Companies the sole trader buys from


@dataclass(frozen=True)
class Trade:
    """Counterparties of a sole trader's business."""

    clients: tuple[Party, ...]
    suppliers: tuple[Party, ...]
    landlord: Party
    utility: Party


def business_activity(
    builder: CaseBuilder,
    invoices_per_month: tuple[int, int] = (2, 4),
    invoice_amount: tuple[float, float] = (400.0, 3000.0),
) -> Trade:
    """Add client invoices, supplier payments, rent, bills, and card spending, month by month.

    Args:
        builder: Case under construction.
        invoices_per_month: Range of client invoices collected each month.
        invoice_amount: Range of a client invoice in euros.

    Returns:
        The counterparties used, so scenarios can reuse them.
    """
    ctx = builder.ctx
    rng = ctx.rng
    trade = Trade(
        clients=tuple(company(ctx) for _ in range(CLIENT_COUNT)),
        suppliers=tuple(company(ctx) for _ in range(SUPPLIER_COUNT)),
        landlord=person(ctx),
        utility=company(ctx, sector="ENERGIA"),
    )
    window = (ctx.period_start, ctx.period_end)
    rent = ctx.money(600, 1500)
    for month in month_starts(*window):
        for day in ctx.days_in_month(month, window, count=rng.randint(*invoices_per_month)):
            client, amount = rng.choice(trade.clients), ctx.money(*invoice_amount)
            builder.wire(day, amount, Direction.INBOUND, client, PaymentPurpose.INVOICE)
        for day in ctx.days_in_month(month, window, count=rng.randint(1, 3)):
            supplier, amount = rng.choice(trade.suppliers), ctx.money(200, 1500)
            builder.wire(day, amount, Direction.OUTBOUND, supplier, PaymentPurpose.INVOICE)
        for day in ctx.days_in_month(month, window, 1, 5):
            builder.wire(day, rent, Direction.OUTBOUND, trade.landlord, PaymentPurpose.RENT)
        for day in ctx.days_in_month(month, window, 10, 20):
            builder.direct_debit(day, ctx.money(80, 300), trade.utility, PaymentPurpose.INVOICE)
        for day in ctx.days_in_month(month, window, count=rng.randint(3, 6)):
            builder.card_payment(day, ctx.money(20, 150))
    return trade
