"""Facts: the unit of traceability between analytics and report."""

from collections import Counter
from typing import Self

from pydantic import Field, model_validator

from .base import DomainModel
from .enums import FactCategory
from .formats import CaseId, FactId, NonEmptyStr, TransactionId


class Fact(DomainModel):
    """A computed result, together with the transactions that support it.

    Every figure in the report is a fact, and every fact points back to its evidence.
    """

    id: FactId = Field(description="Stable fact identifier, cited by the report.")
    category: FactCategory = Field(description="Report area the fact belongs to.")
    label: NonEmptyStr = Field(description="Short human-readable name of the measure.")
    value: bool | int | float | str = Field(description="Computed value.")
    unit: NonEmptyStr | None = Field(
        default=None, description="Unit of measure, e.g. count, EUR, ratio, days."
    )
    evidence: tuple[TransactionId, ...] = Field(
        default=(), description="Transactions that support the value."
    )


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
