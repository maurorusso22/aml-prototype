"""Alerts raised by transaction monitoring."""

from pydantic import AwareDatetime, Field

from .base import DomainModel
from .formats import AlertId, CustomerId, NonEmptyStr, ScenarioName, TransactionId


class Alert(DomainModel):
    """An alert raised on a single transaction.

    Scenario names are invented for this project and do not mirror any real monitoring system.
    """

    alert_id: AlertId = Field(description="Alert identifier.")
    customer_id: CustomerId = Field(description="Customer the alert refers to.")
    transaction_id: TransactionId = Field(description="Transaction that triggered the alert.")
    raised_at: AwareDatetime = Field(description="When the alert was raised, with UTC offset.")
    scenario: ScenarioName = Field(description="Monitoring scenario that fired, in snake_case.")
    reason: NonEmptyStr = Field(description="Human-readable explanation of why it fired.")
