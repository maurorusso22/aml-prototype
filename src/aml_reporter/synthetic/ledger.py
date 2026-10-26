"""Collect the drafted transactions of one case: card and cash operations."""

from datetime import date
from decimal import Decimal

from ..models import Channel, Direction, TransactionType
from .context import SynthContext
from .drafts import Draft
from .products import Persona
from .retail import atm_withdrawal_text, card_payment_text, cash_text

ONLINE_CARD_SHARE = 0.3  # Share of card payments made on the web instead of at a terminal


class Ledger:
    """Accumulates drafts for one persona; these operations carry no label."""

    def __init__(self, ctx: SynthContext, persona: Persona) -> None:
        """Start an empty ledger.

        Args:
            ctx: Generation context.
            persona: Customer the transactions belong to.
        """
        self.ctx = ctx
        self.persona = persona
        self.drafts: list[Draft] = []

    def cash(self, day: date, amount: Decimal, direction: Direction, channel: Channel) -> Draft:
        """Add a cash deposit or withdrawal.

        Args:
            day: Booking date.
            amount: Amount in euros.
            direction: Inbound for deposits, outbound for withdrawals.
            channel: Branch or ATM.

        Returns:
            The new draft.
        """
        deposit = direction is Direction.INBOUND
        kind = TransactionType.CASH_DEPOSIT if deposit else TransactionType.CASH_WITHDRAWAL
        text = cash_text(self.ctx.rng, deposit)
        return self.add(Draft(self.ctx.at(day), amount, direction, channel, kind, text))

    def atm_withdrawal(self, day: date, amount: Decimal) -> Draft:
        """Add a card withdrawal at an ATM in the customer's city.

        Args:
            day: Booking date.
            amount: Amount in euros.

        Returns:
            The new draft.
        """
        text = atm_withdrawal_text(self.persona.city)
        kind = TransactionType.CASH_WITHDRAWAL
        draft = Draft(self.ctx.at(day), amount, Direction.OUTBOUND, Channel.ATM, kind, text, True)
        return self.add(draft)

    def card_payment(self, day: date, amount: Decimal) -> Draft:
        """Add a card payment, in a shop or online.

        Args:
            day: Booking date.
            amount: Amount in euros.

        Returns:
            The new draft.
        """
        online = self.ctx.rng.random() < ONLINE_CARD_SHARE
        text = card_payment_text(self.ctx.rng, self.persona.city, online)
        channel = Channel.ONLINE if online else Channel.POS
        kind = TransactionType.CARD_PAYMENT
        draft = Draft(self.ctx.at(day), amount, Direction.OUTBOUND, channel, kind, text, True)
        return self.add(draft)

    def add(self, draft: Draft) -> Draft:
        """Store a draft.

        Args:
            draft: Draft to store.

        Returns:
            The same draft, so callers can keep a handle on it.
        """
        self.drafts.append(draft)
        return draft
