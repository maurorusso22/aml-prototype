"""Facts: the unit of traceability between analytics and report."""

from pydantic import Field

from .base import DomainModel
from .enums import FactCategory
from .formats import FactId, NonEmptyStr, TransactionId


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
