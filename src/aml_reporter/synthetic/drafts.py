"""Draft transactions: everything about a transaction except its identifier."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from ..models import Channel, CounterpartyType, Direction, PaymentPurpose, TransactionType


@dataclass(frozen=True)
class LabelDraft:
    """Ground truth for a description: what an ideal enricher would extract."""

    counterparty_name: str | None
    counterparty_iban: str | None
    counterparty_type: CounterpartyType | None
    payment_purpose: PaymentPurpose
    hard: bool


@dataclass(frozen=True, eq=False)
class Draft:
    """A transaction before identifiers are assigned.

    Equality is by identity, so drafts can key dictionaries even when two look the same.
    """

    booked_at: datetime
    amount: Decimal
    direction: Direction
    channel: Channel
    transaction_type: TransactionType
    description: str
    uses_card: bool = False
    label: LabelDraft | None = None
