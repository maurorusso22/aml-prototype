"""Structured fields extracted from a transaction's free-text description."""

from typing import Self

from pydantic import Field, model_validator

from .base import DomainModel
from .enums import CounterpartyType, EnrichmentSource, PaymentPurpose
from .formats import Iban, NonEmptyStr, TransactionId


class Enrichment(DomainModel):
    """Output of the enrichment stage for one transaction.

    Missing information is explicit: `None` for values that could not be extracted or
    classified, `unknown` for a payment purpose that cannot be determined.
    """

    transaction_id: TransactionId = Field(description="Transaction the fields refer to.")
    counterparty_name: NonEmptyStr | None = Field(
        default=None, description="Counterparty name, verbatim from the description."
    )
    counterparty_iban: Iban | None = Field(
        default=None, description="Counterparty IBAN, verbatim from the description."
    )
    counterparty_type: CounterpartyType | None = Field(
        default=None, description="Natural or legal person; set only with counterparty_name."
    )
    payment_purpose: PaymentPurpose = Field(
        default=PaymentPurpose.UNKNOWN, description="Purpose stated in the description."
    )
    source: EnrichmentSource = Field(description="Component that produced these fields.")

    @model_validator(mode="after")
    def check_consistency(self) -> Self:
        """Reject a counterparty type without the counterparty it classifies.

        Returns:
            The validated enrichment.
        """
        if self.counterparty_type is not None and self.counterparty_name is None:
            raise ValueError("counterparty_type requires counterparty_name")
        return self
