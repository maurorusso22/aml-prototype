"""What every enricher does, and which transactions it reads."""

from collections.abc import Sequence
from typing import Protocol

from ..models import Enrichment, Transaction, TransactionType

ENRICHABLE_TYPES = frozenset(  # Transactions whose description names a counterparty
    {TransactionType.WIRE_TRANSFER, TransactionType.DIRECT_DEBIT}
)


class Enricher(Protocol):
    """Turns free-text descriptions into structured fields."""

    def enrich(self, transactions: Sequence[Transaction]) -> list[Enrichment]:
        """Enrich every enrichable transaction.

        Args:
            transactions: Any transactions; card and cash operations are skipped.

        Returns:
            One enrichment per wire transfer or direct debit, in input order.
        """
        ...


def enrichable(transactions: Sequence[Transaction]) -> list[Transaction]:
    """Keep the transactions whose description is worth reading.

    Args:
        transactions: Any transactions.

    Returns:
        Wire transfers and direct debits, in input order.
    """
    return [tx for tx in transactions if tx.transaction_type in ENRICHABLE_TYPES]


def normalise(text: str) -> str:
    """Collapse whitespace, so equal descriptions share cache entries.

    Case is kept: extracted names must match the original text verbatim.

    Args:
        text: Raw description.

    Returns:
        Description with single spaces and no padding.
    """
    return " ".join(text.split())
