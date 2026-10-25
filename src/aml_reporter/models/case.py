"""The case bundle: the input of the whole pipeline."""

from datetime import date
from typing import Self

from pydantic import Field, model_validator

from .accounts import Account, Card
from .alert import Alert
from .base import DomainModel
from .case_checks import find_reference_problems
from .customer import Customer
from .formats import CaseId
from .transaction import Transaction


class CaseBundle(DomainModel):
    """Everything known about an alert: the alert itself, the customer, and their activity.

    Besides field-level validation, the bundle checks that every cross-reference resolves, so
    downstream stages can trust IDs without defensive lookups.
    """

    case_id: CaseId = Field(description="Case identifier.")
    period_start: date = Field(description="First day of the look-back window.")
    period_end: date = Field(description="Last day of the look-back window.")
    alert: Alert = Field(description="The alert under investigation.")
    customer: Customer = Field(description="Customer master data.")
    accounts: tuple[Account, ...] = Field(min_length=1, description="Customer's accounts.")
    cards: tuple[Card, ...] = Field(default=(), description="Cards linked to those accounts.")
    transactions: tuple[Transaction, ...] = Field(
        min_length=1, description="Every transaction in the look-back window."
    )

    @model_validator(mode="after")
    def check_references(self) -> Self:
        """Report every broken cross-reference in a single error.

        Returns:
            The validated case bundle.
        """
        problems = find_reference_problems(self)
        if problems:
            raise ValueError("; ".join(problems))
        return self
