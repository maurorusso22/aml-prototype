"""Helpers to build facts: a numbered collection, and exact arithmetic on amounts.

Amounts are summed as exact decimals and only turned into floats when stored in a fact. A
measure that cannot be computed is passed on as a `FactStatus` instead of a value.
"""

from collections.abc import Iterable
from decimal import Decimal

from ..models import Fact, FactCategory, FactStatus, Transaction

CENT = Decimal("0.01")  # Smallest amount unit

type FactValue = bool | int | float | str  # What a measured fact can hold


class Facts:
    """Collects the facts of one analyser, numbered under a common identifier prefix."""

    def __init__(self, prefix: str, category: FactCategory) -> None:
        """Start an empty collection.

        Args:
            prefix: Area code in fact identifiers, e.g. `CASH` for `F-CASH-002`.
            category: Report area of every fact collected.
        """
        self.prefix, self.category = prefix, category
        self.items: list[Fact] = []

    def add(
        self,
        number: int,
        label: str,
        value: FactValue | FactStatus,
        unit: str | None = None,
        evidence: Iterable[Transaction] = (),
    ) -> None:
        """Add a fact whose evidence is a list of transactions.

        Args:
            number: Position within the area; stable across cases, so reports can cite it.
            label: Human-readable name of the measure.
            value: Computed value, or the status that explains why there is none.
            unit: Unit of measure, if any.
            evidence: Transactions supporting the value.
        """
        if isinstance(value, FactStatus):
            measured, status = None, value
        else:
            measured, status = value, FactStatus.MEASURED
        self.items.append(
            Fact(
                id=f"F-{self.prefix}-{number:03d}",
                category=self.category,
                label=label,
                value=measured,
                status=status,
                unit=unit,
                evidence=tuple(tx.transaction_id for tx in evidence),
            )
        )


def total(transactions: Iterable[Transaction]) -> Decimal:
    """Sum transaction amounts exactly.

    Args:
        transactions: Transactions to sum.

    Returns:
        The total.
    """
    return sum((tx.amount for tx in transactions), Decimal(0))


def euros(amount: Decimal) -> float:
    """Turn an exact amount into a fact value.

    Args:
        amount: Amount in euros.

    Returns:
        The amount rounded to the cent.
    """
    return float(amount.quantize(CENT))


def ratio(
    numerator: Decimal | int | float, denominator: Decimal | int | float
) -> float | FactStatus:
    """Divide for shares and multiples, saying why there is no ratio when the reference is zero.

    A zero reference with a positive observation is an increase from nothing, which exceeds
    any multiple: returning 0 would hide exactly the spikes the rules look for.

    Args:
        numerator: Part or observed value.
        denominator: Whole or reference value.

    Returns:
        The ratio rounded to four decimals; `no_baseline` or `no_activity` on a zero reference.
    """
    if not denominator:
        return FactStatus.NO_BASELINE if numerator else FactStatus.NO_ACTIVITY
    return round(float(Decimal(str(numerator)) / Decimal(str(denominator))), 4)
