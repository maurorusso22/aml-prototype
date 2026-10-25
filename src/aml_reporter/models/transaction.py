"""Transactions booked on the customer's accounts and cards."""

from typing import Self

from pydantic import AwareDatetime, Field, model_validator

from .base import DomainModel
from .enums import Channel, Direction, TransactionType
from .formats import AccountId, CardId, CurrencyCode, PositiveMoney, TransactionId

ALLOWED_CHANNELS = {  # Channels through which each transaction type can happen
    TransactionType.WIRE_TRANSFER: {Channel.BRANCH, Channel.ONLINE, Channel.INTERBANK},
    TransactionType.CASH_DEPOSIT: {Channel.BRANCH, Channel.ATM},
    TransactionType.CASH_WITHDRAWAL: {Channel.BRANCH, Channel.ATM},
    TransactionType.CARD_PAYMENT: {Channel.POS, Channel.ONLINE},
    TransactionType.DIRECT_DEBIT: {Channel.INTERBANK},
}
FIXED_DIRECTIONS = {  # Types whose direction follows from the type itself
    TransactionType.CASH_DEPOSIT: Direction.INBOUND,
    TransactionType.CASH_WITHDRAWAL: Direction.OUTBOUND,
    TransactionType.CARD_PAYMENT: Direction.OUTBOUND,
    TransactionType.DIRECT_DEBIT: Direction.OUTBOUND,
}
CARD_FREE_TYPES = {TransactionType.WIRE_TRANSFER, TransactionType.DIRECT_DEBIT}  # Never card-based


class Transaction(DomainModel):
    """A single booked transaction.

    Amounts are always positive; `direction` says whether money came in or went out.
    """

    transaction_id: TransactionId = Field(description="Transaction identifier.")
    account_id: AccountId = Field(description="Account the transaction is booked on.")
    card_id: CardId | None = Field(default=None, description="Card used, if any.")
    booked_at: AwareDatetime = Field(description="Booking timestamp, with UTC offset.")
    amount: PositiveMoney = Field(description="Transaction amount.")
    currency: CurrencyCode = Field(default="EUR", description="ISO 4217 currency code.")
    direction: Direction = Field(description="Money in or out of the account.")
    channel: Channel = Field(description="How the transaction reached the account.")
    transaction_type: TransactionType = Field(description="Kind of banking operation.")
    description: str = Field(
        default="",
        max_length=500,
        description="Free-text description as recorded by the payment system; LLM input.",
    )

    @model_validator(mode="after")
    def check_consistency(self) -> Self:
        """Check that type, channel, direction, and card fit together.

        Returns:
            The validated transaction.
        """
        problems: list[str] = []
        kind = self.transaction_type
        if self.channel not in ALLOWED_CHANNELS[kind]:
            allowed = ", ".join(sorted(ALLOWED_CHANNELS[kind]))
            problems.append(f"{kind} must use one of [{allowed}], got {self.channel}")
        expected = FIXED_DIRECTIONS.get(kind)
        if expected is not None and self.direction is not expected:
            problems.append(f"{kind} must be {expected}, got {self.direction}")
        if kind is TransactionType.CARD_PAYMENT and self.card_id is None:
            problems.append("card_payment requires card_id")
        if kind in CARD_FREE_TYPES and self.card_id is not None:
            problems.append(f"{kind} must not have card_id")
        if problems:
            raise ValueError("; ".join(problems))
        return self
