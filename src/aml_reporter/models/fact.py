"""Facts: the unit of traceability between analytics and report."""

from collections import Counter
from typing import Self

from pydantic import Field, model_validator

from .base import DomainModel
from .enums import FactCategory, FactStatus
from .formats import CaseId, FactId, NonEmptyStr, TransactionId


class Fact(DomainModel):
    """A computed result, together with the transactions that support it.

    Every figure in the report is a fact, and every fact points back to its evidence. When a
    measure cannot be computed, `value` is null and `status` says why, so that a missing
    measure is never mistaken for a zero by the rules or by the analyst.
    """

    id: FactId = Field(description="Stable fact identifier, cited by the report.")
    category: FactCategory = Field(description="Report area the fact belongs to.")
    label: NonEmptyStr = Field(description="Short human-readable name of the measure.")
    value: bool | int | float | str | None = Field(
        description="Computed value; null when the status is not `measured`."
    )
    status: FactStatus = Field(
        default=FactStatus.MEASURED, description="Whether the value was measured, or why not."
    )
    unit: NonEmptyStr | None = Field(
        default=None, description="Unit of measure, e.g. count, EUR, ratio, days."
    )
    evidence: tuple[TransactionId, ...] = Field(
        default=(), description="Transactions that support the value."
    )

    @model_validator(mode="after")
    def check_status(self) -> Self:
        """Require a value exactly when the fact is measured.

        Returns:
            The validated fact.
        """
        if (self.value is None) == (self.status is FactStatus.MEASURED):
            raise ValueError("value must be null exactly when status is not measured")
        return self


class FactSheet(DomainModel):
    """Every fact computed for one case: the input of the red-flag rules and of the report."""

    case_id: CaseId = Field(description="Case the facts describe.")
    facts: tuple[Fact, ...] = Field(description="Facts in the order the analysers produced them.")

    @model_validator(mode="after")
    def check_unique_ids(self) -> Self:
        """Reject fact sheets where two facts share an identifier.

        Returns:
            The validated fact sheet.
        """
        duplicates = sorted(i for i, n in Counter(fact.id for fact in self.facts).items() if n > 1)
        if duplicates:
            raise ValueError(f"duplicate fact ids: {', '.join(duplicates)}")
        return self

    def get(self, fact_id: str) -> Fact:
        """Look up a fact by identifier.

        Args:
            fact_id: Identifier such as `F-CASH-002`.

        Returns:
            The fact.

        Raises:
            KeyError: When no fact has that identifier.
        """
        for fact in self.facts:
            if fact.id == fact_id:
                return fact
        raise KeyError(fact_id)
