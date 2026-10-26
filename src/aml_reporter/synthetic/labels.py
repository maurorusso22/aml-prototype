"""Ground-truth labels, stored apart from case bundles so the pipeline never sees them."""

from pydantic import Field

from ..models import CounterpartyType, Outcome, PaymentPurpose
from ..models.base import DomainModel
from ..models.formats import CaseId, Iban, NonEmptyStr, ScenarioName, TransactionId


class TransactionLabel(DomainModel):
    """What an ideal enricher should extract from one transaction description."""

    transaction_id: TransactionId = Field(description="Labelled transaction.")
    counterparty_name: NonEmptyStr | None = Field(description="Name as written in the text.")
    counterparty_iban: Iban | None = Field(description="IBAN, when the text shows it.")
    counterparty_type: CounterpartyType | None = Field(description="Natural or legal person.")
    payment_purpose: PaymentPurpose = Field(description="Purpose behind the text.")
    hard: bool = Field(description="True for the noisiest descriptions.")


class CaseLabels(DomainModel):
    """Ground truth for one synthetic case."""

    case_id: CaseId = Field(description="Case the labels refer to.")
    scenario: ScenarioName = Field(description="Synthetic scenario that produced the case.")
    expected_outcome: Outcome = Field(description="Decision an analyst should reach.")
    transactions: tuple[TransactionLabel, ...] = Field(description="One label per description.")
