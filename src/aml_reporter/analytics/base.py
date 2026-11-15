"""The analysis context: a case bundle with its enrichments and the views analysers share."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from functools import cached_property

from ..models import CaseBundle, Direction, Enrichment, Transaction

RECENT_DAYS = 90  # Length of the recent window, counted back from the end of the look-back period
MIN_BASELINE_DAYS = 30  # Shortest earlier history that can stand for the customer's usual level


@dataclass(frozen=True)
class AnalysisContext:
    """A case bundle with its enrichments, plus the views most analysers need."""

    bundle: CaseBundle
    enrichments: Mapping[str, Enrichment]

    @cached_property
    def alerted(self) -> Transaction:
        """The transaction that triggered the alert."""
        alert_id = self.bundle.alert.transaction_id
        return next(tx for tx in self.bundle.transactions if tx.transaction_id == alert_id)

    @cached_property
    def recent_start(self) -> date:
        """First day of the recent window."""
        return self.bundle.period_end - timedelta(days=RECENT_DAYS - 1)

    @cached_property
    def observed_from(self) -> date:
        """First day of observable history: the period start, or the first account opening if later.

        Before this day the customer had no account, so their inactivity there is not a signal.
        """
        opened = min(account.opened_on for account in self.bundle.accounts)
        return max(self.bundle.period_start, opened)

    @cached_property
    def observed_days(self) -> int:
        """Days of observable history, used to scale flows to a month or a year."""
        return (self.bundle.period_end - self.observed_from).days + 1

    @cached_property
    def baseline_days(self) -> int:
        """Days of observable history before the recent window: the base of the usual level."""
        return max((self.recent_start - self.observed_from).days, 0)

    def flows(self, direction: Direction, recent: bool = False) -> list[Transaction]:
        """Select inbound or outbound transactions.

        Args:
            direction: Inbound or outbound.
            recent: Keep only the recent window.

        Returns:
            Matching transactions in booking order.
        """
        return [
            tx
            for tx in self.bundle.transactions
            if tx.direction is direction and (not recent or self.is_recent(tx))
        ]

    def is_recent(self, transaction: Transaction) -> bool:
        """Tell whether a transaction falls in the recent window.

        Args:
            transaction: Any transaction of the bundle.

        Returns:
            True when booked in the last `RECENT_DAYS` days of the period.
        """
        return transaction.booked_at.date() >= self.recent_start

    def counterparty(self, transaction: Transaction) -> str | None:
        """Identify a transaction's counterparty: its IBAN when known, else its name.

        Args:
            transaction: Any transaction.

        Returns:
            A grouping key, or None when the enrichment found no counterparty.
        """
        enrichment = self.enrichments.get(transaction.transaction_id)
        if enrichment is None:
            return None
        return enrichment.counterparty_iban or enrichment.counterparty_name


def month_starts(start: date, end: date) -> list[date]:
    """List the first day of every month that overlaps a window.

    Args:
        start: First day of the window.
        end: Last day of the window.

    Returns:
        First days of the months, in order.
    """
    months, current = [], start.replace(day=1)
    while current <= end:
        months.append(current)
        current = date(current.year + current.month // 12, current.month % 12 + 1, 1)
    return months
