"""Accounts and cards held by the customer."""

from datetime import date
from typing import Self

from pydantic import Field, model_validator

from .base import DomainModel
from .enums import AccountStatus, CardType
from .formats import AccountId, CardId, CurrencyCode, Iban, MaskedPan, Money


class Account(DomainModel):
    """A current account held by the customer."""

    account_id: AccountId = Field(description="Account identifier.")
    iban: Iban = Field(description="Account IBAN (synthetic, invalid by design).")
    currency: CurrencyCode = Field(default="EUR", description="ISO 4217 currency code.")
    status: AccountStatus = Field(description="Lifecycle state at the end of the case period.")
    opened_on: date = Field(description="Opening date.")
    closed_on: date | None = Field(default=None, description="Closing date, set only if closed.")
    balance: Money = Field(
        description="Balance at the end of the case period; negative when overdrawn."
    )

    @model_validator(mode="after")
    def check_lifecycle(self) -> Self:
        """Keep status and closing date consistent with each other.

        Returns:
            The validated account.
        """
        if self.closed_on is not None and self.closed_on < self.opened_on:
            raise ValueError("closed_on must not precede opened_on")
        if (self.status is AccountStatus.CLOSED) != (self.closed_on is not None):
            raise ValueError("closed_on must be set if and only if status is closed")
        return self


class Card(DomainModel):
    """A payment card linked to one of the customer's accounts."""

    card_id: CardId = Field(description="Card identifier.")
    account_id: AccountId = Field(description="Account the card is charged to.")
    card_type: CardType = Field(description="Kind of card.")
    masked_pan: MaskedPan = Field(description="Card number with only the last four digits.")
    issued_on: date = Field(description="Issue date.")
    expires_on: date = Field(description="Expiry date.")

    @model_validator(mode="after")
    def check_validity(self) -> Self:
        """Reject cards that expire before being issued.

        Returns:
            The validated card.
        """
        if self.expires_on <= self.issued_on:
            raise ValueError("expires_on must follow issued_on")
        return self
