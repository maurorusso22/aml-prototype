"""Rule-based enricher: offline, deterministic, and the fallback for every LLM failure."""

from collections.abc import Sequence

from ..models import Enrichment, EnrichmentSource, Transaction
from .base import enrichable, normalise
from .rules import classify_counterparty, classify_purpose, extract_counterparty, extract_iban


class BaselineEnricher:
    """Extracts fields with regular expressions and keyword rules, no LLM involved."""

    def enrich(self, transactions: Sequence[Transaction]) -> list[Enrichment]:
        """Enrich every wire transfer and direct debit.

        Args:
            transactions: Any transactions; card and cash operations are skipped.

        Returns:
            One enrichment per enrichable transaction, in input order.
        """
        return [self.enrich_one(tx) for tx in enrichable(transactions)]

    def enrich_one(self, transaction: Transaction) -> Enrichment:
        """Apply every rule to one description.

        Args:
            transaction: A wire transfer or direct debit.

        Returns:
            The enrichment, with source `baseline`.
        """
        text = normalise(transaction.description)
        name = extract_counterparty(text)
        return Enrichment(
            transaction_id=transaction.transaction_id,
            counterparty_name=name,
            counterparty_iban=extract_iban(text),
            counterparty_type=classify_counterparty(name) if name else None,
            payment_purpose=classify_purpose(text),
            source=EnrichmentSource.BASELINE,
        )
